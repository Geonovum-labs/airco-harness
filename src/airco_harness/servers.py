"""The MCP servers on the host that a measurement needs, started from their pinned images and checked by the version they report.

    uv run airco-servers up --variants mcp-bag-ldproxy,mcp-bgt-wijkenbuurten-subsurface+skill-metadata
    uv run airco-servers down

up starts the host servers of the variants named, and no others, and waits until each one reports its pinned
serverInfo.version; it takes the options of airco-matrix and reads only --variants. A server whose URL variable
(AIRCO_<NAME>_URL) is set runs elsewhere, so up checks it but does not start it. down stops every server it can start.

A server of github.com/sjaakd is one container. The ldproxy servers (bag, bgt, wijkenbuurten) are the APIs of one
ldproxy with its database, so they start together: the data directory of github.com/cportele/dsfl-ai at the commit
of tasks.py runs with its own Docker Compose setup, unchanged, with the images of tasks.py. Its dump of Amersfoort is
in Git LFS; the files come from GitHub's media URL of the commit and are checked against the sha256 of their LFS
pointer, so git-lfs is not needed. The first start restores the dump into db/data of the checkout under .ldproxy/,
which takes minutes; a later start reuses it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from . import pinned
from .tasks import DSFL_AI_COMMIT, DSFL_AI_REPOSITORY, LDPROXY_DB_IMAGE, LDPROXY_IMAGE, VARIANTS, McpServer, compose, url_variable

LDPROXY_FOLDER = ".ldproxy"
LDPROXY_PROJECT = "airco-ldproxy"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "airco-servers", "version": "0"}},
}


def needed(variants: list[str]) -> list[McpServer]:
    """The host servers of the variants, each once, in the order of the variants."""
    found = {s.name: s for v in variants for s in compose(v).mcp if s.image}
    return list(found.values())


def container(server: McpServer) -> str:
    return f"airco-{server.name}"


def _run(*args: str, cwd: Path | None = None, env: dict | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True, env=env).stdout


def _pointer(blob: bytes) -> tuple[str, int] | None:
    """The sha256 and size of a Git LFS pointer; None for a file that is not one."""
    if not blob.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None
    fields = dict(line.split(" ", 1) for line in blob.decode().splitlines() if " " in line)
    return fields["oid"].removeprefix("sha256:"), int(fields["size"])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ldproxy_checkout() -> Path:
    """dsfl-ai at the pinned commit with its LFS files in place; converges from any partial earlier run."""
    path = pinned.checkout(DSFL_AI_REPOSITORY, DSFL_AI_COMMIT, LDPROXY_FOLDER)
    for name in filter(None, pinned.git(path, "ls-files", "-z").split("\0")):
        blob = subprocess.run(["git", "-C", str(path), "cat-file", "-p", f"HEAD:{name}"], check=True, capture_output=True).stdout
        if not (pointer := _pointer(blob)):
            continue
        oid, size = pointer
        file = path / name
        if file.stat().st_size == size and _sha256(file) == oid:
            continue
        url = f"https://media.githubusercontent.com/media/{DSFL_AI_REPOSITORY}/{DSFL_AI_COMMIT}/{urllib.parse.quote(name)}"
        partial = file.with_name(file.name + ".part")
        urllib.request.urlretrieve(url, partial)
        if partial.stat().st_size != size or _sha256(partial) != oid:
            partial.unlink()
            raise RuntimeError(f"{url} does not match its LFS pointer (sha256 {oid}, {size} bytes)")
        partial.replace(file)
    return path


def _ldproxy_compose(path: Path, *args: str) -> None:
    env = {**os.environ, "LDPROXY_IMAGE": LDPROXY_IMAGE, "BAG_DB_IMAGE": LDPROXY_DB_IMAGE}
    subprocess.run(["docker", "compose", "--project-name", LDPROXY_PROJECT, *args], cwd=path, check=True, env=env)


def _start_container(server: McpServer) -> None:
    """A server of github.com/sjaakd: its image on the port of its URL, with the base URI of its concepts set as its README asks."""
    port = urllib.parse.urlsplit(server.url).port
    concepts = f"{server.name.upper().replace('-', '_')}_CONCEPTS_BASE_URI=https://example.org/"
    subprocess.run(["docker", "rm", "-f", container(server)], check=False, capture_output=True)
    _run("docker", "run", "-d", "--name", container(server), "--platform", "linux/amd64", "-p", f"{port}:8080", "-e", concepts, server.image)


def server_version(url: str) -> str | None:
    """The serverInfo.version a server reports on initialize; None while it does not answer."""
    request = urllib.request.Request(
        url, data=json.dumps(INITIALIZE).encode(), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode()
    except OSError:
        return None
    # A Streamable HTTP server may answer as an event stream, with the JSON on its data line.
    text = next((line[5:] for line in body.splitlines() if line.startswith("data:")), body)
    return json.loads(text)["result"]["serverInfo"]["version"]


def _start(servers: list[McpServer]) -> dict[str, str]:
    """Start the servers; per server that did not start, why. One failing server does not keep the others from starting."""
    failed = {}
    ldproxy = [s for s in servers if s.image == LDPROXY_IMAGE]
    if ldproxy:
        try:
            _ldproxy_compose(ldproxy_checkout(), "up", "-d")
        except (subprocess.CalledProcessError, OSError, RuntimeError) as e:
            failed |= {s.name: f"ldproxy did not start: {e}" for s in ldproxy}
    for server in (s for s in servers if s.image != LDPROXY_IMAGE):
        try:
            _start_container(server)
        except subprocess.CalledProcessError as e:
            failed[server.name] = f"did not start: {e.stderr.strip()}"
    return failed


def up(variants: list[str], timeout: int) -> None:
    servers = needed(variants)
    if not servers:
        print("the variants need no server on the host")
        return
    failed = _start([s for s in servers if not os.environ.get(url_variable(s), "").strip()])
    deadline = time.monotonic() + timeout
    for server in (s for s in servers if s.name not in failed):
        url = os.environ.get(url_variable(server), "").strip() or server.url
        while (found := server_version(url)) is None and time.monotonic() < deadline:
            time.sleep(5)
        if found == server.version:
            print(f"{server.name} {found} at {url}")
        else:
            failed[server.name] = f"reports version {found} at {url}, not {server.version}"
    if failed:
        raise SystemExit("\n".join(f"{name} {why}" for name, why in failed.items()))


def down() -> None:
    names = {container(s) for v in VARIANTS.values() for s in v.mcp if s.image and s.image != LDPROXY_IMAGE}
    subprocess.run(["docker", "rm", "-f", *sorted(names)], check=False, capture_output=True)
    if (path := pinned.location(DSFL_AI_REPOSITORY, DSFL_AI_COMMIT, LDPROXY_FOLDER)).exists():
        _ldproxy_compose(path, "down")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["up", "down"])
    parser.add_argument("--variants", default="0", help="comma-separated variants, as for airco-matrix")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds to wait for the servers; the first start of ldproxy restores its dump")
    args, _ = parser.parse_known_args()
    load_dotenv(find_dotenv(usecwd=True))
    if args.command == "up":
        up([v.strip() for v in args.variants.split(",") if v.strip()], args.timeout)
    else:
        down()


if __name__ == "__main__":
    main()
