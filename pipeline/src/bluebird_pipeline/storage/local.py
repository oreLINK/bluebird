"""Filesystem storage backend."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .base import Storage


class LocalStorage(Storage):
    """Store objects as files under ``root``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError(f"key escapes storage root: {key}")
        return path

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.chmod(tmp_name, 0o644)  # mkstemp creates 0600 files
            os.replace(tmp_name, path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def list(self, prefix: str) -> list[str]:
        base = self._path(prefix)
        if not base.is_dir():
            return []
        root = self.root.resolve()
        return sorted(
            path.relative_to(root).as_posix()
            for path in base.rglob("*")
            if path.is_file() and not path.name.startswith(".")
        )
