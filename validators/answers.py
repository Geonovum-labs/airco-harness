"""Tolerant extraction from a model answer: the content of a code block, or the whole text."""

from __future__ import annotations

import re

CODE_BLOCK = re.compile(r"```[ \t]*([\w+-]*)[^\n]*\n(.*?)```", re.DOTALL)


def code_blocks(text: str) -> list[tuple[str, str]]:
    return [(lang.lower(), body.strip()) for lang, body in CODE_BLOCK.findall(text)]


def block(text: str, languages: tuple[str, ...]) -> str:
    """First code block in one of `languages`, else the first code block, else the whole text."""
    blocks = code_blocks(text)
    for lang, body in blocks:
        if lang in languages:
            return body
    if blocks:
        return blocks[0][1]
    return text.strip()


def json_text(text: str) -> str:
    candidate = block(text, ("json", "jsonc"))
    if candidate.startswith(("{", "[")):
        return candidate
    start = min((i for i in (candidate.find("{"), candidate.find("[")) if i >= 0), default=-1)
    end = max(candidate.rfind("}"), candidate.rfind("]"))
    return candidate[start : end + 1] if 0 <= start < end else candidate
