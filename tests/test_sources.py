"""The vendored source files against their lock file."""

from validators import sources


def test_vendored_files_match_the_lock():
    assert sources.check() == 0
