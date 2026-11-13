"""The tools the harness gives an agent: fetch, show_on_map, plot_series and a variant's MCP tools.

fetch returns a web page as markdown, in pages of 40,000 characters. Inspect
has web_search() but no plain fetch, and an agent that can search but not read
would not get far with a catalog. show_on_map stands for the map a citizen
sees in a chat app; it says nothing about the registrations behind it.

fetch records nothing itself: the arguments are in the tool call and the
result in the tool message, both in the log, which is what the scorers and a
rescore read. show_on_map with a url also records the GeoJSON it fetched in the
sample store, because the log lacks it and a rescore must not fetch again: a
live service changes.
"""

from __future__ import annotations

import json
import re
import urllib.parse

import httpx
from inspect_ai.tool import MCPServer, Tool, ToolDef, ToolError, ToolSource, tool
from inspect_ai.util import store
from markdownify import markdownify

from validators import geo, series

PAGE_CHARS = 40_000
MAP_STORE = "show_on_map"  # sample store key: {url: GeoJSON the map loaded from it}
MAP_MAX_BYTES = 50_000_000
MAP_TIMEOUT = 120
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


@tool(name="show_on_map")
def show_on_map() -> Tool:
    async def execute(geojson: dict | None = None, url: str | None = None) -> str:
        """Show places on the map that the user sees. A new call replaces the map.

        Give either geojson or url, not both.

        Args:
          geojson: A GeoJSON FeatureCollection with coordinates in WGS84 (longitude, latitude). Put a name or address in the properties of each feature.
          url: Instead of geojson: an http or https URL that returns such a FeatureCollection as JSON. The map loads this one document; it does not follow links to further pages.
        """
        if (geojson is None) == (url is None):
            raise ToolError("give exactly one of geojson and url")
        if url is not None:
            geojson = await load_geojson(url)
        try:
            places = geo.points(geojson)
        except ValueError as error:
            raise ToolError(str(error)) from error
        if url is not None:
            store().set(MAP_STORE, {**store().get(MAP_STORE, {}), url: geojson})
        return f"{len(places)} places shown on the map."

    return execute


async def load_geojson(url: str) -> dict:
    """The JSON document at a URL, fetched once."""
    target = fetchable(url)
    if target is None:
        raise ToolError("only valid http and https URLs can be loaded")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=MAP_TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(target)
    except (httpx.HTTPError, httpx.InvalidURL) as error:
        raise ToolError(f"{type(error).__name__}: {error}") from error
    if not 200 <= resp.status_code < 300:
        raise ToolError(f"HTTP {resp.status_code}")
    if len(resp.content) > MAP_MAX_BYTES:
        raise ToolError(f"response larger than {MAP_MAX_BYTES // 1_000_000} MB")
    try:
        return json.loads(resp.content)
    except ValueError as error:
        raise ToolError("the response is not JSON") from error


class ProviderNamedTools(ToolSource):
    """The tools of an MCP server under names the model APIs accept.

    Anthropic, OpenAI and Mistral take letters, digits, _ and - in a tool name; an
    MCP server may use more, such as groundwater-monitoring.tubes.search, which
    becomes groundwater-monitoring_tubes_search. The server still gets its own name.
    """

    def __init__(self, server: MCPServer) -> None:
        self.server = server

    async def tools(self) -> list[Tool]:
        return [ToolDef(t, name=re.sub(r"[^A-Za-z0-9_-]", "_", ToolDef(t).name)).as_tool() for t in await self.server.tools()]


@tool(name="plot_series")
def plot_series() -> Tool:
    async def execute(data: dict) -> str:
        """Show a time series plot. A new call replaces the plot.

        Args:
          data: Object with points (ordered daily objects with ISO date and numeric value or null for a gap), unit, reference_plane and connect_gaps (boolean).
        """
        error = series.validate(data)
        if error:
            raise ToolError(error)
        return f"{len(data['points'])} daily entries shown in the plot."

    return execute
