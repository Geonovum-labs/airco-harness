import pytest

from validators import source_check


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://docs.geostandaarden.nl/imgeo/catalogus/bgt/", "authoritative"),
        ("https://docs.geostandaarden.nl/imgeo/def-im-BGT-20200701/", "authoritative"),
        ("https://docs.geostandaarden.nl/imgeo/def-im-BGT-20160101/", "non_authoritative"),
        ("https://definities.geostandaarden.nl/imgeo/id/begrip/Wegdeel", "authoritative"),
        ("https://geonovum.github.io/IMGeo-dev/", "non_authoritative"),
        ("https://github.com/Geonovum/IMGeo-dev/blob/master/mim/x.xml", "non_authoritative"),
        ("https://github.com/Geonovum/IMGeo/tree/master/gmlapplicatieschema/2.1.1", "authoritative"),
        ("https://www.pdok.nl/introductie/-/article/basisregistratie-grootschalige-topografie-bgt-", "other"),
    ],
)
def test_classify(url, expected):
    assert source_check.classify(url, "imgeo-2.2") == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://service.pdok.nl/lv/bag/wfs/v2_0?service=WFS&request=GetFeature&typeNames=bag:verblijfsobject", "authoritative"),
        ("https://bagviewer.kadaster.nl/lvbag/bag-viewer/?objectId=0202010000417964", "authoritative"),
        ("https://www.ep-online.nl/Energylabel/Search", "authoritative"),
        ("https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=6842CV%208", "other"),
        ("https://www.funda.nl/", "other"),
    ],
)
def test_classify_dsfl(url, expected):
    assert source_check.classify(url, "dsfl") == expected


def test_assess_needs_an_authoritative_hit_and_no_other_version():
    ok = {"url": "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/", "status": 200}
    old = {"url": "https://geonovum.github.io/IMGeo-dev/", "status": 200}
    failed = {"url": "https://docs.geostandaarden.nl/imgeo/catalogus/imgeo/", "status": 404}
    forum = {"url": "https://forum.example.org/bgt", "status": 200}
    assert source_check.assess([ok, forum], "imgeo-2.2")[0] == 1
    assert source_check.assess([ok, old], "imgeo-2.2")[0] == 0
    assert source_check.assess([failed, forum], "imgeo-2.2") == (0, {"retrieved": {"https://forum.example.org/bgt": "other"}, "failed": [failed["url"]]})
    assert source_check.assess([], "imgeo-2.2")[0] == 0


@pytest.mark.parametrize(
    ("url", "standard", "expected"),
    [
        ("https://raw.githubusercontent.com/Geonovum/technisch-register-2019/7cc32f97d4711fe41842b653a4ef1e57af95932a/src/index.php", "sbom", "authoritative"),
        ("https://github.com/Geonovum/technisch-register-2019", "sbom", "authoritative"),
        ("https://api.github.com/repos/Geonovum/technisch-register-2019/git/trees/master?recursive=1", "sbom", "authoritative"),
        ("https://api.osv.dev/v1/query", "sbom", "authoritative"),
        ("https://nvd.nist.gov/vuln/detail/CVE-2020-11023", "sbom", "authoritative"),
        # The answers, once the repository has them, and the fork they were made in.
        ("https://raw.githubusercontent.com/Geonovum/technisch-register-2019/master/sbom.cdx.json", "sbom", "non_authoritative"),
        ("https://github.com/fterpstra/technisch-register-2019/tree/claude/publiccode", "sbom", "non_authoritative"),
        ("https://snyk.io/test/npm/jquery/1.9.1", "sbom", "other"),
        ("https://github.com/Geonovum/technisch-register-2019/blob/master/LICENSE", "publiccode-0.7", "authoritative"),
        ("https://yml.publiccode.tools/schema.core.html#key-softwaretype", "publiccode-0.7", "authoritative"),
        ("https://github.com/Geonovum/technisch-register-2019/blob/master/publiccode.yml", "publiccode-0.7", "non_authoritative"),
        ("https://developer.overheid.nl/kennisbank/open-source/standaarden/publiccode-yml", "publiccode-0.7", "other"),
    ],
)
def test_classify_technisch_register(url, standard, expected):
    assert source_check.classify(url, standard) == expected
