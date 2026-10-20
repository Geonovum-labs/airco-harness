from lxml import etree

from validators import refmodel, refmodel_files, sources
from validators.refmodel import ReferenceModel, normalize

MODEL = ReferenceModel.load()
FILES = refmodel_files.paths(refmodel.REFERENCE_MODELS / refmodel.IMGEO)


def test_committed_files_match_a_fresh_write(tmp_path):
    written = refmodel_files.write(refmodel.generate(), tmp_path)
    assert {kind: path.read_bytes() for kind, path in written.items()} == {kind: path.read_bytes() for kind, path in FILES.items()}


def test_files_carry_the_whole_reference_model():
    assert MODEL.data == refmodel.generate()


def test_mim_xml_is_valid_against_the_mim_1_1_1_xsd():
    sources.mim_schema().assertValid(etree.parse(FILES["model.mim.xml"]))


def test_mim_xml_maps_attribute_types_to_mim_constructs():
    ns = refmodel_files.NS
    doc = etree.parse(FILES["model.mim.xml"])
    group = doc.find(".//mim:Objecttype[mim:naam='Pand']/mim:gegevensgroepen/mim:Gegevensgroep[mim:naam='nummeraanduidingreeks']", ns)
    assert group.findtext("mim:gegevensgroeptype/mim-ref:GegevensgroeptypeRef", namespaces=ns) == "Nummeraanduidingreeks"
    status = doc.find(
        ".//mim:Objecttype[mim:naam='IMGeo-object']/mim:attribuutsoorten/mim:Attribuutsoort[mim:naam='bgt-status']/mim:type/mim-ref:DatatypeRef", ns
    )
    assert (status.text, status.get(f"{{{ns['xlink']}}}href")) == ("Status", "#codelijst-status")


def test_functieweg_has_sixteen_bgt_values_in_sorted_order():
    assert MODEL.values("FunctieWeg") == [
        "OV-baan", "baan voor vliegverkeer", "fietspad", "inrit", "overweg", "parkeervlak", "rijbaan autosnelweg",
        "rijbaan autoweg", "rijbaan lokale weg", "rijbaan regionale weg", "ruiterpad", "spoorbaan", "voetgangersgebied",
        "voetpad", "voetpad op trap", "woonerf",
    ]  # fmt: skip


def test_plus_values_keep_their_bgt_parents_and_get_their_register_concept():
    verbindingsweg = next(v for v in MODEL.data["domains"]["FunctieWegPlus"]["values"] if v["value"] == "verbindingsweg")
    assert verbindingsweg == {
        "value": "verbindingsweg",
        "definition": verbindingsweg["definition"],
        "parents": ["rijbaan autosnelweg", "rijbaan autoweg", "rijbaan regionale weg"],
        "concept": "http://definities.geostandaarden.nl/imgeo/id/begrip/Verbindingsweg",
    }


def test_flags_of_relatieve_hoogteligging():
    attr = MODEL.attribute("IMGeo-object", "relatieveHoogteligging")
    assert (attr["authentic"], attr["formal_history"], attr["material_history"]) == ("Authentiek", True, False)


def test_known_terms_are_normalized():
    assert normalize("Niet‑BGT ") == "niet-bgt"
    assert "niet-bgt" in MODEL.all_terms
    assert "fietsstraat" not in MODEL.all_terms
    assert MODEL.all_values["fietspad"] == {"FunctieWeg"}


def test_first_table_row_is_read_although_rendered_as_header():
    assert MODEL.published_domains["FunctieWeg"][0] == "OV-baan"
    assert MODEL.published_domains["Status"] == ["bestaand"]


def test_published_values_count_as_known():
    # The IMGeo catalog publishes "historie" in StatusPlus, the MIM model does not have it.
    assert "historie" not in MODEL.values("StatusPlus")
    assert MODEL.all_values["historie"] == {"StatusPlus"}
