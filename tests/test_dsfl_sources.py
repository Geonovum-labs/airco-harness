"""The expected answers of the dsfl samples, derived again from the vendored sources."""

import csv
import datetime
import json
import math
import zoneinfo

import pytest
import shapely
from lxml import etree

from validators import geo, rules, sources

AMSTERDAM = zoneinfo.ZoneInfo("Europe/Amsterdam")
STADHUISPLEIN_RD = (154792.05, 463172.16)


def expected(sample_id: str) -> dict:
    return json.loads((rules.TESTSETS_DIR / f"dsfl/samples/{sample_id}/expected.json").read_text(encoding="utf-8"))


def vendored(name: str) -> dict:
    return json.loads(sources.path(f"dsfl/{name}").read_text(encoding="utf-8"))


def test_dsfl_01_decade_with_most_existing_panden():
    counts = vendored("bag-amersfoort-bouwjaar-per-decade.json")["per_status"]
    existing: dict[str, int] = {}
    for status in sources.PAND_EXISTS:
        for decade, n in counts[status].items():
            existing[decade] = existing.get(decade, 0) + n
    assert int(max(existing, key=existing.get)) == expected("dsfl-01")["expected"]["decade"]
    assert sum(sum(c.values()) for c in counts.values()) == vendored("bag-amersfoort-bouwjaar-per-decade.json")["panden"]


def test_dsfl_02_area_with_most_panden_under_construction():
    wijken: dict[str, int] = {}
    for f in vendored("bag-amersfoort-bouw-gestart.json")["features"]:
        assert f["properties"]["status"] == "Bouw gestart"
        wijken[f["properties"]["wijknaam"]] = wijken.get(f["properties"]["wijknaam"], 0) + 1
    vathorst = {n: c for n, c in wijken.items() if n.startswith("Vathorst") or n == "Bedrijventerrein Vathorst"}
    parts = {**wijken, "Vathorst": sum(vathorst.values())}
    leaders = {name for name, n in parts.items() if n == max(parts.values())}
    assert leaders <= set(expected("dsfl-02")["expected"]["part"]["one_of"])
    assert max(wijken, key=wijken.get) in expected("dsfl-02")["expected"]["part"]["one_of"]


def test_dsfl_03_must_is_the_panden_demolished_in_the_last_ten_years_that_a_place_can_tell_apart():
    features = vendored("bag-amersfoort-gesloopt.geojson")["features"]
    reference = geo.Reference.load(expected("dsfl-03")["reference"])
    window = [f for f in features if f["properties"]["beginGeldigheid"] >= "2016-11-12"]
    alone = [f for f in window if reference.nearest(shapely.geometry.shape(f["geometry"]).representative_point(), 15) == f["id"]]
    assert {f["properties"]["status"] for f in features} == {"Pand gesloopt"}
    assert sorted(f["id"] for f in alone) == sorted(expected("dsfl-03")["must"])
    assert len(window) - len(alone) < 50


def test_dsfl_04_must_is_the_panden_with_a_sports_verblijfsobject_in_use():
    vbo = vendored("bag-amersfoort-sport-verblijfsobjecten.json")["features"]
    panden = {
        f["properties"]["pandidentificatie"]
        for f in vbo
        if f["properties"]["status"] == "Verblijfsobject in gebruik" and f["properties"]["gebruiksdoel"] == "sportfunctie"
    }
    assert sorted(panden) == expected("dsfl-04")["must"]


def test_dsfl_05_must_is_the_old_panden_with_a_home_in_use():
    result = vendored("bag-amersfoort-voor-1800-woningen.json")["features"]
    homes = [f for f in result if f["properties"]["objecttype"] == "verblijfsobject"]
    assert {h["properties"]["status"] for h in homes} <= {
        "Verblijfsobject in gebruik",
        "Verblijfsobject in gebruik (niet ingemeten)",
        "Verbouwing verblijfsobject",
    }
    assert all("woonfunctie" in h["properties"]["gebruiksdoel"] for h in homes)
    with_home = {p["title"] for h in homes for p in h["properties"]["maaktDeelUitVan"]}
    reference = vendored("bag-amersfoort-voor-1800-panden.geojson")["features"]
    assert sorted(with_home) == expected("dsfl-05")["must"]
    assert with_home <= {f["id"] for f in reference}
    assert all(f["properties"]["oorspronkelijkBouwjaar"] < 1800 and f["properties"]["status"] in sources.PAND_EXISTS for f in reference)


def test_dsfl_06_level_of_the_well_on_the_day_in_cm_nap():
    rows = list(csv.DictReader(sources.path("dsfl/bro-gld000000025798.csv").read_text(encoding="utf-8").splitlines()))
    day = datetime.date(2026, 9, 21)
    levels = {"utc": set(), "local": set()}
    for r in rows:
        value = r["Voorlopige Waarde [m]"]
        moment = datetime.datetime.fromtimestamp(int(r["Tijdstip"]) / 1000, datetime.timezone.utc)
        if value and moment.date() == day:
            levels["utc"].add(round(float(value) * 100))
        if value and moment.astimezone(AMSTERDAM).date() == day:
            levels["local"].add(round(float(value) * 100))
    assert levels["utc"] == levels["local"] == {expected("dsfl-06")["expected"]["level_cm_nap"]}
    relations = json.loads(sources.path("dsfl/bro-gmw000000009441-relations.json").read_text(encoding="utf-8"))
    assert [t["gldReferences"][0]["broId"] for t in relations["monitoringTubeReferences"]] == ["GLD000000025798"]
    well = etree.parse(str(sources.path("dsfl/bro-gmw000000009441.xml"))).getroot()
    assert float(well.findtext(".//{*}groundLevelPosition")) == 5.61


def gmw_wells() -> dict[str, tuple[tuple[float, float], str]]:
    """The delivered RD location and the removed flag of every well of the vendored search, by broId."""
    wells = {}
    for c in etree.parse(str(sources.path("dsfl/bro-gmw-amersfoort-1km.xml"))).getroot().iter("{*}GMW_C"):
        x, y = (float(v) for v in c.findtext("{*}deliveredLocation/{*}pos").split())
        wells[c.findtext("{*}broId")] = ((x, y), c.findtext("{*}removed"))
    return wells


def test_dsfl_07_must_is_the_wells_within_500_m_that_are_not_removed():
    wells = gmw_wells()
    within = {i: math.dist(STADHUISPLEIN_RD, xy) for i, (xy, _) in wells.items() if math.dist(STADHUISPLEIN_RD, xy) <= 500}
    assert (len(wells), len(within), max(within.values())) == (57, 13, pytest.approx(466.06, abs=0.01))
    assert min(math.dist(STADHUISPLEIN_RD, xy) for i, (xy, _) in wells.items() if i not in within) == pytest.approx(505.93, abs=0.01)
    assert sorted(i for i in within if wells[i][1] == "nee") == expected("dsfl-07")["must"]
    assert {i for i in within if wells[i][1] == "ja"} == {"GMW000000133351"}


def test_dsfl_07_reference_is_the_wells_of_the_search_as_points():
    features = vendored("bro-gmw-amersfoort-1km.geojson")["features"]
    assert sorted(f["id"] for f in features) == sorted(gmw_wells())
    assert {f["geometry"]["type"] for f in features} == {"Point"}
    assert all(f["id"] == f["properties"]["identificatie"] for f in features)
    assert set(expected("dsfl-07")["must"]) <= {f["id"] for f in features}


def test_dsfl_07_tolerance_keeps_required_wells_apart_from_the_rest():
    wells = gmw_wells()
    tolerance = expected("dsfl-07")["tolerance_m"]
    must = set(expected("dsfl-07")["must"])
    close = min(math.dist(wells[a][0], wells[b][0]) for a in must for b in must if a < b)
    gap = min(math.dist(wells[a][0], wells[b][0]) for a in must for b in wells if b not in must)
    assert (close, gap) == (pytest.approx(0.8, abs=0.01), pytest.approx(138.4, abs=0.1))
    assert 1 < tolerance < gap / 2  # above five-decimal rounding, far below the distance to a well that is not required


@pytest.mark.parametrize("sample_id", [f"dsfl-0{n}" for n in range(1, 8)])
def test_every_dsfl_sample_names_its_origin_and_its_source(sample_id):
    data = expected(sample_id)
    assert data["note"].startswith("Deck wording: " if sample_id < "dsfl-06" else "Origin: ") and "sources/dsfl/" in data["source"]
