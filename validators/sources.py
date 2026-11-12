"""Source files of the standards under test: fetch, record provenance, read back.

    uv run airco-sources           # fetch everything and rewrite sources/sources.lock.json
    uv run airco-sources --check   # verify local files against the lock
    uv run airco-sources --only dsfl/   # fetch one group, keep the rest of the lock

Every source is a URL stored at a fixed path under sources/. A file from
GitHub is pinned to a commit in its URL. A source whose query is too long for
a GET is a POST, with a body built from a file fetched before it; the lock
then records the method and the sha256 of the body. A source that is too big
to keep is an Aggregate: its pages are fetched one by one, reduced to a small
JSON file, and the lock records method "GET, paged". The lock records the sha256 and size
of each file, and Last-Modified and ETag when the server sends them. The MIM
XSD and the schemas it imports are stored under schemas/<host>/<path>, where
LocalSchemas finds them, so XML validation needs no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import NamedTuple

from lxml import etree

SOURCES_DIR = Path(__file__).resolve().parent.parent / "sources"
LOCK_FILE = SOURCES_DIR / "sources.lock.json"
MIM_XSD = "mim-1.1.1/MIMFORMAT_Mim_relatiesoort.xsd"
MIM_XSD_IMPORTS = ["MIMFORMAT_Mim.xsd", "MIMFORMAT_MimExt.xsd", "MIMFORMAT_MimRef.xsd", "xlink.xsd"]


def schema_path(schema_url: str) -> str:
    parts = urllib.parse.urlsplit(schema_url)
    return f"schemas/{parts.netloc}{parts.path}"


BAG_WFS = "https://service.pdok.nl/lv/bag/wfs/v2_0"
DSFL_SPORT_VBO = "dsfl/bag-amersfoort-sport-verblijfsobjecten.json"
DSFL_SPORT_PANDEN = "dsfl/bag-amersfoort-sport-panden.geojson"


def _bag_sport_amersfoort() -> str:
    """Verblijfsobjecten in gemeente Amersfoort (its woonplaatsen) whose gebruiksdoel includes sportfunctie, as GeoJSON in WGS84."""
    woonplaatsen = "".join(
        f"<PropertyIsEqualTo><ValueReference>woonplaats</ValueReference><Literal>{w}</Literal></PropertyIsEqualTo>"
        for w in ("Amersfoort", "Hoogland", "Hooglanderveen")
    )
    fes = (
        '<Filter xmlns="http://www.opengis.net/fes/2.0"><And>'
        '<PropertyIsLike wildCard="*" singleChar="." escapeChar="!"><ValueReference>gebruiksdoel</ValueReference><Literal>*sportfunctie*</Literal></PropertyIsLike>'
        f"<Or>{woonplaatsen}</Or></And></Filter>"
    )
    query = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": "bag:verblijfsobject",
             "outputFormat": "application/json", "srsName": "EPSG:4326", "count": "1000", "FILTER": fes}  # fmt: skip
    return f"{BAG_WFS}?{urllib.parse.urlencode(query)}"


def _bag_panden_of_sport_amersfoort() -> tuple[str, bytes]:
    """The panden of the verblijfsobjecten in DSFL_SPORT_VBO, as GeoJSON in WGS84. 112 ids are too long for a GET."""
    vbo = json.loads(path(DSFL_SPORT_VBO).read_text(encoding="utf-8"))
    ids = sorted({f["properties"]["pandidentificatie"] for f in vbo["features"]})
    clauses = "".join(
        f"<fes:PropertyIsEqualTo><fes:ValueReference>identificatie</fes:ValueReference><fes:Literal>{i}</fes:Literal></fes:PropertyIsEqualTo>" for i in ids
    )
    body = (
        '<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0" service="WFS" version="2.0.0" '
        'outputFormat="application/json" count="1000"><wfs:Query typeNames="bag:pand" srsName="EPSG:4326">'
        f"<fes:Filter><fes:Or>{clauses}</fes:Or></fes:Filter></wfs:Query></wfs:GetFeature>"
    )
    return BAG_WFS, body.encode("utf-8")


BAG_API = "https://bag.ldproxy.net/bag"
PAGE_SIZE = 5000
RETRIES = 4
RETRY_WAIT = 10
PAGE_PAUSE = 1
DSFL_DECADES = "dsfl/bag-amersfoort-bouwjaar-per-decade.json"
DSFL_BOUW_GESTART = "dsfl/bag-amersfoort-bouw-gestart.json"
DSFL_GESLOOPT = "dsfl/bag-amersfoort-gesloopt.geojson"
DSFL_VOOR_1800_PANDEN = "dsfl/bag-amersfoort-voor-1800-panden.geojson"
DSFL_VOOR_1800_WONINGEN = "dsfl/bag-amersfoort-voor-1800-woningen.json"
# CBS gemeentecode of Amersfoort; the BAG 2.0 Extract at bag.ldproxy.net carries it on every object.
AMERSFOORT = "0307"
# The statuses of a pand that exists; the stored query verblijfsobjecten-in-panden uses the first four by default.
PAND_EXISTS = ("Pand in gebruik", "Pand in gebruik (niet ingemeten)", "Verbouwing pand", "Sloopvergunning verleend", "Pand buiten gebruik")
DEMOLISHED_SINCE = "2015-11-12"


class Aggregate(NamedTuple):
    """A GET that is paged with offset and then reduced to one small JSON object, so a source of 100,000 features is not vendored."""

    url: str
    reduce: Callable[[list[dict]], dict]


def _ldproxy(path: str, **params: str | int) -> str:
    """A URL of bag.ldproxy.net. A stored query rejects the parameter f. The comma in `properties` has to stay literal: %2C gives HTTP 400."""
    return f"{BAG_API}/{path}?" + urllib.parse.urlencode(params, safe=",")


def _pand_items(**params: str | int) -> str:
    return _ldproxy("collections/pand/items", f="json", limit=PAGE_SIZE, gemeentecode=AMERSFOORT, **params)


def _per_decade(features: list[dict]) -> dict:
    """Panden by status and decade of oorspronkelijkBouwjaar. 9999 means unknown and is counted as its own decade, 9990."""
    counts: dict[str, dict[int, int]] = {}
    for f in features:
        p = f["properties"]
        by_decade = counts.setdefault(p["status"], {})
        decade = p["oorspronkelijkBouwjaar"] // 10 * 10
        by_decade[decade] = by_decade.get(decade, 0) + 1
    return {"panden": len(features), "per_status": {s: {str(d): n for d, n in sorted(c.items())} for s, c in sorted(counts.items())}}


# Path under sources/ to a URL, an Aggregate, or a function that gives the URL and the body of a POST. Fetched in this order.
SOURCES: dict[str, str | Aggregate | Callable[[], tuple[str, bytes]]] = {
    "imgeo-2.2/imgeo2.2-mim-logisch.xml": "https://raw.githubusercontent.com/Geonovum/IMGeo-dev/30d750029fc4b81998d30a95185f78ff2c314ced/mim/imgeo2.2-mim-logisch.xml",
    "imgeo-2.2/catalog-bgt.html": "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/",
    "imgeo-2.2/catalog-imgeo.html": "https://docs.geostandaarden.nl/imgeo/catalogus/imgeo/",
    "imgeo-2.2/concept-register-imgeo.ttl": "https://definities.geostandaarden.nl/rest/v1/imgeo/data?format=text/turtle",
    MIM_XSD: "https://register.geostandaarden.nl/xmlschema/mim/1.1.1/MIMFORMAT_Mim_relatiesoort.xsd",
    **{schema_path(url): url for url in (f"https://register.geostandaarden.nl/xmlschema/mim/1.1.1/{name}" for name in MIM_XSD_IMPORTS)},
    DSFL_SPORT_VBO: _bag_sport_amersfoort(),
    DSFL_SPORT_PANDEN: _bag_panden_of_sport_amersfoort,
    DSFL_DECADES: Aggregate(_pand_items(properties="oorspronkelijkBouwjaar,status"), _per_decade),
    DSFL_BOUW_GESTART: _pand_items(status="Bouw gestart", properties="status,wijknaam,buurtnaam,beginGeldigheid"),
    DSFL_GESLOOPT: _pand_items(
        status="Pand gesloopt", filter=f"beginGeldigheid >= DATE('{DEMOLISHED_SINCE}')", properties="geometrie,status,oorspronkelijkBouwjaar,beginGeldigheid"
    ),
    DSFL_VOOR_1800_PANDEN: _pand_items(
        filter="oorspronkelijkBouwjaar < 1800 AND status IN (" + ",".join(f"'{s}'" for s in PAND_EXISTS) + ")",
        properties="geometrie,status,oorspronkelijkBouwjaar,beginGeldigheid",
    ),
    DSFL_VOOR_1800_WONINGEN: _ldproxy("search/verblijfsobjecten-in-panden", gebied=AMERSFOORT, bouwjaarTot=1799, gebruiksdoel="woonfunctie"),
}


@cache
def lock() -> dict[str, dict[str, object]]:
    data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    return {r["path"]: r for r in data["files"]}


def path(source: str) -> Path:
    return SOURCES_DIR / source


def read(file: Path, commit: str) -> str:
    """The text of a file of this repository as it was at `commit`, or as it is now when `commit` is empty."""
    if not commit:
        return file.read_text(encoding="utf-8")
    root = SOURCES_DIR.parent
    name = file.relative_to(root).as_posix()
    shown = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{name}"], capture_output=True)
    if shown.returncode:
        error = shown.stderr.decode("utf-8", "replace").strip()
        raise FileNotFoundError(f"{name} at commit {commit}: {error}; a shallow clone lacks older commits, fetch the full history")
    return shown.stdout.decode("utf-8")


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


def _get(source_url: str, body: bytes | None = None) -> tuple[bytes, dict[str, str]]:
    """The body and validators of a response. bag.ldproxy.net answers 404 on everything for about a minute after heavy paging, so a 404 or 5xx is retried."""
    headers = {"User-Agent": "airco-harness-sources/0.1"} | ({"Content-Type": "application/xml"} if body else {})
    req = urllib.request.Request(source_url, data=body, headers=headers)
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                headers = {k.lower().replace("-", "_"): resp.headers[k] for k in ("Last-Modified", "ETag") if resp.headers.get(k)}
                return resp.read(), headers
        except urllib.error.HTTPError as error:
            if error.code != 404 and error.code < 500 or attempt == RETRIES - 1:
                raise
        except urllib.error.URLError:
            if attempt == RETRIES - 1:
                raise
        time.sleep(RETRY_WAIT * 2**attempt)
    raise AssertionError("unreachable")


def _get_paged(aggregate: Aggregate) -> bytes:
    """All features of the url, fetched with our own offset: the `next` links of bag.ldproxy.net encode a space as %2B and fail with HTTP 400."""
    features: dict[str, dict] = {}
    while True:
        data, _ = _get(f"{aggregate.url}&offset={len(features)}")
        page = json.loads(data)["features"]
        if any(f["id"] in features for f in page):
            raise ValueError(f"paging returned a feature twice: {aggregate.url}")
        features |= {f["id"]: f for f in page}
        if len(page) < PAGE_SIZE:
            break
        time.sleep(PAGE_PAUSE)
    return (json.dumps(aggregate.reduce(list(features.values())), indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def fetch(prefix: str = "") -> None:
    """Fetch the sources whose path starts with `prefix`, and keep the lock records of the others."""
    kept = [r for r in json.loads(LOCK_FILE.read_text(encoding="utf-8"))["files"] if not r["path"].startswith(prefix)] if prefix else []
    records = []
    for target, source in SOURCES.items():
        if not target.startswith(prefix):
            continue
        match source:
            case str():
                source_url, method = source, {}
                data, headers = _get(source)
            case Aggregate(source_url, _):
                method, headers = {"method": "GET, paged"}, {}
                data = _get_paged(source)
            case _:
                source_url, body = source()
                method = {"method": "POST", "body_sha256": hashlib.sha256(body).hexdigest()}
                data, headers = _get(source_url, body)
        file = SOURCES_DIR / target
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        records.append({"path": target, "url": source_url, **method, **headers, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    payload = {"fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "files": sorted(kept + records, key=lambda r: r["path"])}
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
    parser.add_argument("--only", default="", metavar="PREFIX", help="fetch only the sources whose path starts with PREFIX, such as dsfl/")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(check() if args.check else fetch(args.only))
