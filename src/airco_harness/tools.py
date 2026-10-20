"""The fetch tool of the agent inspect: a web page as markdown, in pages of 40,000 characters.

Inspect has web_search() but no plain fetch, and an agent that can search
but not read would not get far with a catalog. The tool records nothing
itself: the URL is in the tool call and the page in the tool result, both in
the log, which is what the source scorer and a rescore read.
"""

from __future__ import annotations

import re
import urllib.parse

import httpx
from inspect_ai.tool import Tool, ToolError, tool
from markdownify import markdownify

PAGE_CHARS = 40_000
USER_AGENT = "Mozilla/5.0 (compatible; airco-harness/0.1; +https://github.com/Geonovum-labs/airco-harness)"


def to_markdown(html: str | bytes) -> str:
    """Markdown for an HTML document. Names and values stay as written: nothing is escaped."""
    text = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
    markdown = re.sub(
        r"\n{3,}", "\n\n", markdownify(text, heading_style="ATX", bullets="-", escape_asterisks=False, escape_underscores=False, escape_misc=False)
    )
    return markdown.strip()


def as_text(body: bytes, content_type: str) -> str:
    if "html" in content_type:
        return to_markdown(body)
    if content_type.startswith("text/") or any(t in content_type for t in ("json", "xml", "turtle", "yaml")):
        return body.decode("utf-8", errors="replace")
    return f"[binary content: {content_type or 'unknown type'}, {len(body)} bytes]"


def page(text: str, start: int, page_chars: int = PAGE_CHARS) -> str:
    start = max(0, start)
    end = min(len(text), start + page_chars)
    chunk = text[start:end]
    if end < len(text):
        chunk += f"\n\n[characters {start}-{end} of {len(text)}; continue with start={end}]"
    return chunk


def fetchable(url: str) -> str | None:
    """The URL without fragment when it can be fetched over http(s), else None."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.netloc or any(ord(c) < 32 or c == "\x7f" for c in url):
        return None
    return urllib.parse.urldefrag(url).url


@tool(name="fetch")
def fetch() -> Tool:
    async def execute(url: str, start: int = 0) -> str:
        """Fetch a web page over HTTP(S) and return its text as markdown. No JavaScript is run.

        Args:
          url: The http or https URL to fetch.
          start: Character offset to continue reading a long page.
        """
        target = fetchable(url)
        if target is None:
            raise ToolError("only valid http and https URLs can be fetched")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
                resp = await client.get(target)
        except (httpx.HTTPError, httpx.InvalidURL) as error:
            raise ToolError(f"{type(error).__name__}: {error}") from error
        if not 200 <= resp.status_code < 300:
            raise ToolError(f"HTTP {resp.status_code}")
        return page(as_text(resp.content, resp.headers.get("content-type", "")), start)

    return execute
