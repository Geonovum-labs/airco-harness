"""A GitHub repository at one commit, fetched once into a folder of this checkout and reused after.

The commit names the content exactly: git checks every object it fetches against its hash. A partial earlier
run converges, because the checkout is forced to the commit each time. LFS files stay pointers here.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(checkout: Path, *args: str) -> str:
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    return subprocess.run(["git", "-C", str(checkout), *args], check=True, capture_output=True, text=True, env=env).stdout


def location(repository: str, commit: str, folder: str) -> Path:
    """Where checkout() puts github.com/<repository> at the commit: <folder>/<repository with __ for />/<commit> of this checkout."""
    return ROOT / folder / repository.replace("/", "__") / commit


def checkout(repository: str, commit: str, folder: str) -> Path:
    """github.com/<repository> at the commit, fetched once."""
    path = location(repository, commit, folder)
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        git(path, "init", "-q")
    present = subprocess.run(["git", "-C", str(path), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True).returncode == 0
    if not present:
        git(path, "fetch", "-q", "--depth", "1", f"https://github.com/{repository}", commit)
    git(path, "checkout", "-q", "--force", commit)
    return path
