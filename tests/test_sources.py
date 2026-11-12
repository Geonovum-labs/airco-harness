"""The vendored source files against their lock file."""

import json

import pytest

from validators import sources


def test_vendored_files_match_the_lock():
    assert sources.check() == 0


def test_an_aggregate_pages_with_its_own_offset_and_keeps_only_the_reduced_result(monkeypatch):
    features = [{"id": str(i), "properties": {"status": "Pand in gebruik", "oorspronkelijkBouwjaar": 1990 + i % 3 * 10}} for i in range(sources.PAGE_SIZE + 7)]
    requested = []

    def get(url, body=None):
        requested.append(url)
        offset = int(url.rsplit("offset=", 1)[1])
        return json.dumps({"features": features[offset : offset + sources.PAGE_SIZE]}).encode(), {}

    monkeypatch.setattr(sources, "_get", get)
    monkeypatch.setattr(sources, "PAGE_PAUSE", 0)
    result = json.loads(sources._get_paged(sources.Aggregate("https://example.org/items?limit=5000", sources._per_decade)))
    assert [u.rsplit("offset=", 1)[1] for u in requested] == ["0", str(sources.PAGE_SIZE)]
    assert result == {"panden": len(features), "per_status": {"Pand in gebruik": {"1990": 1669, "2000": 1669, "2010": 1669}}}


def test_a_feature_that_two_pages_both_return_is_an_error(monkeypatch):
    page = json.dumps({"features": [{"id": str(i), "properties": {}} for i in range(sources.PAGE_SIZE)]}).encode()
    monkeypatch.setattr(sources, "_get", lambda url, body=None: (page, {}))
    monkeypatch.setattr(sources, "PAGE_PAUSE", 0)
    with pytest.raises(ValueError, match="twice"):
        sources._get_paged(sources.Aggregate("https://example.org/items?limit=5000", len))


def test_a_comma_in_the_properties_of_an_ldproxy_url_stays_literal():
    assert "properties=a,b&" in sources._ldproxy("collections/pand/items", properties="a,b", limit=1) + "&"
