"""The `source` metric: did the agent use the authoritative source and version of the standard?"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path

ALLOWLIST = Path(__file__).resolve().parent.parent / "testsets" / "sources-allowlist.json"


@cache
def _patterns(standard: str) -> tuple[list[re.Pattern], list[re.Pattern]]:
    entry = json.loads(ALLOWLIST.read_text(encoding="utf-8"))[standard]
    return [re.compile(p) for p in entry["authoritative"]], [re.compile(p) for p in entry["non_authoritative"]]


def classify(url: str, standard: str) -> str:
    authoritative, other_versions = _patterns(standard)
    if any(p.search(url) for p in other_versions):
        return "non_authoritative"
    if any(p.search(url) for p in authoritative):
        return "authoritative"
    return "other"


def assess(retrievals: list[dict], standard: str) -> tuple[int, dict]:
    """1 when at least one successful retrieval is authoritative and none is a non-authoritative version.

    A retrieval is a dict with at least "url" and "status" (200 when the tool answered without an error, else 0).
    After a redirect the page the agent read is at "final_url", so that is the URL that is classified.
    """
    ok = [r for r in retrievals if 200 <= int(r.get("status") or 0) < 300]
    classes = {r.get("final_url") or r["url"]: classify(r.get("final_url") or r["url"], standard) for r in ok}
    value = int("authoritative" in classes.values() and "non_authoritative" not in classes.values())
    return value, {"retrieved": classes, "failed": [r["url"] for r in retrievals if r not in ok]}
