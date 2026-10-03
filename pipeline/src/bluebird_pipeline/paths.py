"""Locate the repository, the configuration folder and the local data folder.

Environment variables take precedence, so CI and tests can redirect them:

- ``BLUEBIRD_CONFIG_DIR``: folder containing ``massifs.yaml`` and friends.
- ``BLUEBIRD_DATA_DIR``: root of the local storage (bronze/silver/gold/diamond).
"""

from __future__ import annotations

import os
from pathlib import Path

_MARKER = Path("config") / "massifs.yaml"


class RepositoryNotFoundError(RuntimeError):
    """Raised when the Bluebird repository root cannot be located."""


def repo_root() -> Path:
    """Return the repository root, searching upwards from cwd, then from this file."""
    for start in (Path.cwd(), Path(__file__).resolve()):
        for candidate in (start, *start.parents):
            if (candidate / _MARKER).is_file():
                return candidate
    raise RepositoryNotFoundError(
        f"Could not find '{_MARKER}' above {Path.cwd()}. "
        "Run the pipeline from inside the repository or set BLUEBIRD_CONFIG_DIR."
    )


def default_config_dir() -> Path:
    """Return the configuration folder."""
    env = os.environ.get("BLUEBIRD_CONFIG_DIR")
    return Path(env) if env else repo_root() / "config"


def default_data_dir() -> Path:
    """Return the root folder of the local storage backend."""
    env = os.environ.get("BLUEBIRD_DATA_DIR")
    return Path(env) if env else repo_root() / "data"
