"""The expected answers of the dsfl samples, derived again from the vendored sources."""

import json

import pytest
import shapely

from validators import geo, rules, sources


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


@pytest.mark.parametrize("sample_id", [f"dsfl-0{n}" for n in range(1, 6)])
def test_every_dsfl_sample_names_its_deck_wording_and_its_source(sample_id):
    data = expected(sample_id)
    assert data["note"].startswith("Deck wording: ") and "sources/dsfl/" in data["source"]
