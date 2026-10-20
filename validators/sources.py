"""Source files of the standards under test: fetch, record provenance, read back.

    uv run airco-sources           # fetch everything and rewrite sources/sources.lock.json
    uv run airco-sources --check   # verify local files against the lock

Every source is a URL stored at a fixed path under sources/. A file from
GitHub is pinned to a commit in its URL. The lock records the sha256 and size
of each file, and Last-Modified and ETag when the server sends them. The MIM
XSD and the schemas it imports are stored under schemas/<host>/<path>, where
LocalSchemas finds them, so XML validation needs no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

from lxml import etree

SOURCES_DIR = Path(__file__).resolve().parent.parent / "sources"
LOCK_FILE = SOURCES_DIR / "sources.lock.json"
MIM_XSD = "mim-1.1.1/MIMFORMAT_Mim_relatiesoort.xsd"
MIM_XSD_IMPORTS = ["MIMFORMAT_Mim.xsd", "MIMFORMAT_MimExt.xsd", "MIMFORMAT_MimRef.xsd", "xlink.xsd"]


def schema_path(schema_url: str) -> str:
    parts = urllib.parse.urlsplit(schema_url)
    return f"schemas/{parts.netloc}{parts.path}"


# Path under sources/ to URL.
SOURCES: dict[str, str] = {
    "imgeo-2.2/imgeo2.2-mim-logisch.xml": "https://raw.githubusercontent.com/Geonovum/IMGeo-dev/30d750029fc4b81998d30a95185f78ff2c314ced/mim/imgeo2.2-mim-logisch.xml",
    "imgeo-2.2/catalog-bgt.html": "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/",
    "imgeo-2.2/catalog-imgeo.html": "https://docs.geostandaarden.nl/imgeo/catalogus/imgeo/",
    "imgeo-2.2/concept-register-imgeo.ttl": "https://definities.geostandaarden.nl/rest/v1/imgeo/data?format=text/turtle",
    MIM_XSD: "https://register.geostandaarden.nl/xmlschema/mim/1.1.1/MIMFORMAT_Mim_relatiesoort.xsd",
    **{schema_path(url): url for url in (f"https://register.geostandaarden.nl/xmlschema/mim/1.1.1/{name}" for name in MIM_XSD_IMPORTS)},
}


@cache
def lock() -> dict[str, dict[str, object]]:
    data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    return {r["path"]: r for r in data["files"]}


def path(source: str) -> Path:
    return SOURCES_DIR / source


def url(source: str) -> str:
    return str(lock()[source]["url"])


def sha256(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


class LocalSchemas(etree.Resolver):
    """Resolves http(s) references in schemas to sources/schemas/<host>/<path>.

    A schema that is not present locally is an error: validation must never
    silently depend on the network.
    """

    def resolve(self, system_url, public_id, context):
        if urllib.parse.urlsplit(system_url).scheme not in ("http", "https"):
            return None
        local = SOURCES_DIR / schema_path(system_url)
        if not local.exists():
            raise FileNotFoundError(f"schema not available locally: {system_url}; run airco-sources")
        return self.resolve_filename(str(local), context)


def mim_schema() -> etree.XMLSchema:
    """The MIM 1.1.1 XSD in the mode "relatiesoort leidend" that IMGeo uses, with its imports from the local copies."""
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    parser.resolvers.add(LocalSchemas())
    return etree.XMLSchema(etree.parse(str(path(MIM_XSD)), parser, base_url=url(MIM_XSD)))


def _get(source_url: str) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(source_url, headers={"User-Agent": "airco-harness-sources/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        headers = {k.lower().replace("-", "_"): resp.headers[k] for k in ("Last-Modified", "ETag") if resp.headers.get(k)}
        return resp.read(), headers


def fetch() -> None:
    records = []
    for target, source_url in SOURCES.items():
        data, headers = _get(source_url)
        file = SOURCES_DIR / target
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        records.append({"path": target, "url": source_url, **headers, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    payload = {"fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "files": sorted(records, key=lambda r: r["path"])}
    LOCK_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(records)} files recorded in {LOCK_FILE.relative_to(SOURCES_DIR.parent)}")


def check() -> int:
    files = json.loads(LOCK_FILE.read_text(encoding="utf-8"))["files"]
    bad = 0
    for r in files:
        file = SOURCES_DIR / r["path"]
        if not file.exists():
            print(f"missing: {r['path']}")
            bad += 1
        elif sha256(file) != r["sha256"]:
            print(f"checksum mismatch: {r['path']}")
            bad += 1
    print(f"{len(files) - bad} of {len(files)} files ok")
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-sources", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only verify the files on disk against sources.lock.json; fetch nothing")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(check() if args.check else fetch())
