import json
import re

import pytest
from jsonschema import validators

from airco_harness import dataset
from validators import rules, sources
from validators.geo import Reference

TESTSETS = rules.TESTSETS_DIR
SAMPLE_SCHEMA = json.loads((TESTSETS / "sample.schema.json").read_text(encoding="utf-8"))
NAMES = dataset.testsets()
FOLDERS = sorted(p for name in NAMES for p in (TESTSETS / name / "samples").iterdir())
IDS = [f"{p.parent.parent.name}/{p.name}" for p in FOLDERS]
RULES = set(rules.RULES)


def test_test_sets_are_the_folders_with_a_manifest():
    assert NAMES == ["dsfl", "imgeo", "technisch-register"]


@pytest.mark.parametrize("name", NAMES)
def test_every_test_set_states_purpose_version_and_date(name):
    manifest = dataset.manifest(name)
    assert sorted(manifest) == ["date", "purpose", "version"] and all(manifest.values())


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_sample_folder_is_named_by_its_id_and_holds_a_valid_sample(folder):
    sample = json.loads((folder / "sample.json").read_text(encoding="utf-8"))
    assert re.fullmatch(r"[a-z0-9.-]+-G\d{2}-\d{2}" if "defect" in sample else r"[a-z0-9.-]+-\d{2}", folder.name)
    assert list(validators.validator_for(SAMPLE_SCHEMA)(SAMPLE_SCHEMA).iter_errors(sample)) == []


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_expected_outcome_names_a_known_rule_and_valid_answer_schema(folder):
    expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    assert expected["rule"] in RULES
    if "answer_schema" in expected:
        schema = json.loads((folder / expected["answer_schema"]).read_text(encoding="utf-8"))
        validators.validator_for(schema).check_schema(schema)


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_a_map_sample_requires_only_panden_of_its_reference(folder):
    expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    if expected["rule"] != "map":
        pytest.skip("not a map sample")
    reference = Reference.load(expected["reference"])
    assert expected["must"] and set(expected["must"]) <= set(reference.panden)


def technisch_register(name: str) -> str:
    return sources.path(f"technisch-register-2019/{name}").read_text(encoding="utf-8")


def test_the_components_of_sbom_01_are_in_the_vendored_repository():
    """Each required version, and the yepnope version, is in the file it comes from at the pinned commit."""
    assert "jQuery JavaScript Library v1.9.1" in technisch_register("src/resources/js/jquery-1.9.1.js")
    assert "jQuery UI - v1.10.1" in technisch_register("src/resources/js/jquery-ui-1.10.1.min.js")
    assert "jQuery UI - v1.10.1" in technisch_register("src/resources/css/jquery-ui-1.10.1.min.css")
    modernizr = technisch_register("src/resources/js/modernizr.js")
    assert modernizr.startswith("/* Modernizr 2.6.2 ") and "yepnope1.5.4" in modernizr
    assert "//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" in technisch_register("src/index.php")


def test_no_page_of_the_vendored_repository_loads_a_script_so_sbom_02_is_not_affected():
    pages = ["src/index.php", "src/listDescriptions.php", *(f"src/resources/html/{n}" for n in ("footer.html", "header.html", "help.php", "over.php"))]
    assert [p for p in pages if re.search(r"<script|resources/js|\.js\b", technisch_register(p), re.I)] == []


def test_the_vendored_repository_is_mit_licensed_by_geonovum():
    license_text = technisch_register("LICENSE")
    assert license_text.startswith("MIT License") and "Copyright (c) 2019 Geonovum" in license_text
