"""Scan logs for secrets and personal data before they are published.

    uv run airco-logcheck reports/<name>/logs
    uv run airco-logcheck --mask reports/<name>/logs   # first replace email addresses and home paths, then scan

Reads every .eval log through Inspect and every .json, .html, .md and .csv
file, and searches the text of every string in them, decoded, for: the values
of key-like variables from the environment and .env, API key patterns, email
addresses and home directory paths. A log that cannot be read is reported too.
Exits 1 on any finding, and 2 when a given path does not exist.

An agent that reads the web brings contact addresses from the pages into its
log, and a traceback names the home folder of the machine that ran it. --mask
replaces every email address that is not in ALLOWED and every home path, as
MASKS says, in the JSON of each .eval log and in every .json file, before the
scan, and prints where it replaced home paths. The rest of the log stays as it
was, so the scores do not change.
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


# What --mask replaces, and with what. A home path is the user name of the machine that ran the matrix; on a GitHub
# runner it shows up in tracebacks through uv's Python and through the checkout, both under /home/runner.
MASKS = {"email": (PATTERNS["email"], "[email removed]"), "home path": (PATTERNS["home path"], "~")}


def _masked(value: object, where: str, found: list[tuple[str, str]]) -> object:
    """`value` with every email address outside ALLOWED and every home path masked; appends (label, JSON key path) to found."""
    if isinstance(value, str):
        for label, (pattern, mask) in MASKS.items():

            def replace(m: re.Match, label: str = label, mask: str = mask) -> str:
                if m.group(0) in ALLOWED:
                    return m.group(0)
                found.append((label, where))
                return mask

            value = pattern.sub(replace, value)
        return value
    if isinstance(value, dict):
        masked = {}
        for k, v in value.items():
            key = _masked(k, where, found)  # the location names the masked key, so it never prints what it masks
            masked[key] = _masked(v, f"{where}.{key}", found)
        return masked
    if isinstance(value, list):
        return [_masked(v, f"{where}[]", found) for v in value]
    return value


def mask(path: Path) -> list[tuple[str, str]]:
    """Mask email addresses and home paths in a .eval log (each JSON member of the zip) or a .json file, in place.

    Returns one (label, location) per replacement; the location is the zip member and the JSON key path, which tells a
    traceback from a tool result without printing the text itself."""
    found: list[tuple[str, str]] = []
    if path.suffix == ".json":
        data = _masked(json.loads(path.read_text(encoding="utf-8")), "", found)
        if found:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return found
    with zipfile.ZipFile(path) as source:
        members = [(info, source.read(info)) for info in source.infolist()]
    rewritten = []
    for info, body in members:
        if info.filename.endswith(".json"):
            before = len(found)
            data = _masked(json.loads(body), f"{info.filename}:", found)
            if len(found) > before:
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        rewritten.append((info, body))
    if found:
        temporary = path.with_suffix(".eval.tmp")
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as target:
            for info, body in rewritten:
                target.writestr(info, body)
        temporary.replace(path)
    return found


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
    parser.add_argument(
        "--mask", action="store_true", help="replace email addresses and home paths in .eval and .json files before the scan; changes the files"
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    missing = [r for r in args.roots if not Path(r).exists()]
    if missing:
        print(f"not found: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    if args.mask:
        for root in args.roots:
            base = Path(root)
            for path in [base] if base.is_file() else sorted(base.rglob("*")):
                if path.is_file() and path.suffix in (".eval", ".json"):
                    found = mask(path)
                    emails = sum(label == "email" for label, _ in found)
                    homes = sorted({where for label, where in found if label == "home path"})
                    if emails:
                        print(f"{path}: {emails} email addresses masked")
                    if homes:
                        print(f"{path}: {len(found) - emails} home paths masked, at {', '.join(homes[:10])}")
    hits = [h for root in args.roots for h in scan(root)]
    for h in hits[:200]:
        print(h)
    print(f"{len(hits)} findings")
    sys.exit(1 if hits else 0)
