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
