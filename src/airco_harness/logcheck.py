"""Scan logs for secrets and personal data before they are published.

    uv run airco-logcheck reports/<name>/logs
    uv run airco-logcheck --mask-emails reports/<name>/logs   # first replace email addresses, then scan

Reads every .eval log through Inspect and every .json, .html, .md and .csv
file, and searches the text of every string in them, decoded, for: the values
of key-like variables from the environment and .env, API key patterns, email
addresses and home directory paths. A log that cannot be read is reported too.
Exits 1 on any finding, and 2 when a given path does not exist.

An agent that reads the web brings contact addresses from the pages into its
log. --mask-emails replaces every email address that is not in ALLOWED with
MASK, in the JSON of each .eval log and in every .json file, before the scan.
The rest of the log stays as it was, so the scores do not change.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

from dotenv import dotenv_values, find_dotenv
from inspect_ai.log import read_eval_log

SECRET_NAMES = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD)$")
PATTERNS = {
    "api key": re.compile(r"(?<![A-Za-z0-9_-])(sk-ant-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,})"),
    # Not an image name with a pixel density, such as icon_1@2x.webp.
    "email": re.compile(r"[A-Za-z0-9._%+-]+@(?!\d+x\.(?:webp|png|jpe?g|gif|svg|avif)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "home path": re.compile(r"(?:/(?:Users|home)/|[A-Za-z]:\\+Users\\+)[A-Za-z0-9._-]+(?=[/\\\"'\s]|$)"),
}
# Addresses that are part of the published standard or of tools, not personal data.
# Public addresses in the sources and in Claude Code's own configuration, the git remote, and the fixed dummy token that
# Inspect SWE gives Claude Code for the bridge to Inspect (inspect_swe/_claude_code/env.py); none of them is a secret.
# huren@geldersepoort.nl is the public leasing address of the office park of the dsfl test set, allowed for now.
ALLOWED = {
    "imgeo@geonovum.nl",
    "bgt@minbzk.nl",
    "info@geonovum.nl",
    "git@github.com",
    "noreply@anthropic.com",
    "sk-ant-api03-DOq5tyLPrk9M4hPE",
    "huren@geldersepoort.nl",
}
# Inspect writes the traceback of a retried provider error into the log, with the host path of its own
# installation in the virtualenv. That names the home folder, but nothing else; a home path anywhere else is a finding.
TRACEBACK_PATH = re.compile(r"^[^\s\"']*/\.venv/")
# A web page that embeds a Google map carries the site's browser key in the map URL, and a provider's web search
# returns that URL with the result; the key is the site's and public by design. A Google key anywhere else is a finding.
MAPS_URL_KEY = re.compile(r"maps\.google(?:apis)?\.com/maps/api/[^\s\"']*[?&;]key=$")


def _allowed(match: re.Match, text: str) -> bool:
    value = match.group(0)
    return (
        value in ALLOWED
        or bool(TRACEBACK_PATH.match(text[match.end() : match.end() + 200]))
        or bool(MAPS_URL_KEY.search(text[max(0, match.start() - 300) : match.start()]))
    )


MASK = "[email removed]"


def _masked(value: object, count: list[int]) -> object:
    """`value` with every email address outside ALLOWED replaced by MASK; count[0] counts the replacements."""
    if isinstance(value, str):

        def replace(m: re.Match) -> str:
            if m.group(0) in ALLOWED:
                return m.group(0)
            count[0] += 1
            return MASK

        return PATTERNS["email"].sub(replace, value)
    if isinstance(value, dict):
        return {_masked(k, count): _masked(v, count) for k, v in value.items()}
    if isinstance(value, list):
        return [_masked(v, count) for v in value]
    return value


def mask_emails(path: Path) -> int:
    """Mask the email addresses in a .eval log (each JSON member of the zip) or a .json file, in place; the number masked."""
    count = [0]
    if path.suffix == ".json":
        data = _masked(json.loads(path.read_text(encoding="utf-8")), count)
        if count[0]:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return count[0]
    with zipfile.ZipFile(path) as source:
        members = [(info, source.read(info)) for info in source.infolist()]
    rewritten = []
    for info, body in members:
        if info.filename.endswith(".json"):
            before = count[0]
            data = _masked(json.loads(body), count)
            if count[0] > before:
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        rewritten.append((info, body))
    if count[0]:
        temporary = path.with_suffix(".eval.tmp")
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as target:
            for info, body in rewritten:
                target.writestr(info, body)
        temporary.replace(path)
    return count[0]


TRIVIAL = {"", "ollama", "dummy", "none"}
SUFFIXES = (".eval", ".json", ".html", ".md", ".csv")


def secret_values() -> dict[str, str]:
    values = dict(os.environ)
    env_file = find_dotenv(usecwd=True)
    if env_file:
        values |= {k: v or "" for k, v in dotenv_values(env_file).items()}
    return {k: v for k, v in values.items() if SECRET_NAMES.search(k) and v.strip().lower() not in TRIVIAL and len(v) >= 8}


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings(v)


def _texts(path: Path) -> list[str]:
    if path.suffix == ".eval":
        return list(_strings(read_eval_log(str(path)).model_dump(mode="json")))
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            return list(_strings(json.loads(raw)))
        except ValueError:
            pass
    return [raw]


def scan_file(path: Path, secrets: dict[str, str]) -> list[str]:
    try:
        texts = _texts(path)
    except Exception as error:  # a truncated or foreign file must not stop the scan of the others
        return [f"{path}: unreadable, not checked ({type(error).__name__}: {error})"]
    hits: set[str] = set()
    for text in texts:
        hits |= {f"value of {name}" for name, value in secrets.items() if value in text}
        for label, pattern in PATTERNS.items():
            hits |= {f"{label} {m.group(0)[:60]}" for m in pattern.finditer(text) if not _allowed(m, text)}
    return [f"{path}: {h}" for h in sorted(hits)]


def scan(root: str) -> list[str]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(root)
    files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in SUFFIXES)
    secrets = secret_values()
    return [hit for path in files for hit in scan_file(path, secrets)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-logcheck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", nargs="+", help="files or folders to scan")
    parser.add_argument("--mask-emails", action="store_true", help="replace email addresses in .eval and .json files before the scan; changes the files")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    missing = [r for r in args.roots if not Path(r).exists()]
    if missing:
        print(f"not found: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    if args.mask_emails:
        for root in args.roots:
            base = Path(root)
            for path in [base] if base.is_file() else sorted(base.rglob("*")):
                if path.is_file() and path.suffix in (".eval", ".json"):
                    masked = mask_emails(path)
                    if masked:
                        print(f"{path}: {masked} email addresses masked")
    hits = [h for root in args.roots for h in scan(root)]
    for h in hits[:200]:
        print(h)
    print(f"{len(hits)} findings")
    sys.exit(1 if hits else 0)
