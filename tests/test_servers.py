"""airco-servers starts the host servers a measurement's variants need, and no others."""

from airco_harness import servers


def names(variants):
    return [s.name for s in servers.needed(variants)]


def test_only_the_host_servers_of_the_variants_named_are_needed():
    assert names(["0", "skill-metadata", "mcp-dsfl-context"]) == []
    assert names(["mcp-bag-ldproxy"]) == ["bag"]
    assert names(["mcp-groundwater-monitoring", "mcp-bgt-wijkenbuurten-subsurface+skill-metadata"]) == [
        "groundwater-monitoring",
        "bgt",
        "wijkenbuurten",
        "subsurface-models",
    ]


def test_a_server_two_variants_share_is_needed_once():
    assert names(["mcp-bgt-wijkenbuurten-subsurface", "mcp-bgt-wijkenbuurten-subsurface+skill-metadata"]) == ["bgt", "wijkenbuurten", "subsurface-models"]


def test_an_lfs_pointer_gives_its_sha256_and_size_and_a_file_that_is_not_one_gives_none():
    pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:f6daed07698d982cf9d25a369c265dbf8d5f577c86b49c7a1b1feb7406636a13\nsize 84\n"
    assert servers._pointer(pointer) == ("f6daed07698d982cf9d25a369c265dbf8d5f577c86b49c7a1b1feb7406636a13", 84)
    assert servers._pointer(b"PGDMP\xe5 binary") is None


def test_up_starts_nothing_for_variants_without_host_servers(monkeypatch, capsys):
    monkeypatch.setattr(servers.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError(f"started {a}")))
    servers.up(["0", "skill-metadata"], timeout=1)
    assert "need no server on the host" in capsys.readouterr().out
