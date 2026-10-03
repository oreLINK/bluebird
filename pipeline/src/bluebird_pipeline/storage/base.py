"""Abstract storage interface plus format helpers shared by every backend."""

from __future__ import annotations

import gzip
import io
import json
from abc import ABC, abstractmethod
from typing import Any

import polars as pl


class Storage(ABC):
    """Key/value blob storage with JSON, gzip-JSON and Parquet helpers."""

    # -- primitives every backend implements -----------------------------------

    @abstractmethod
    def write_bytes(self, key: str, data: bytes) -> None:
        """Write ``data`` at ``key``, replacing any existing object atomically."""

    @abstractmethod
    def read_bytes(self, key: str) -> bytes:
        """Return the bytes stored at ``key``; raise ``FileNotFoundError`` if absent."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether an object exists at ``key``."""

    @abstractmethod
    def list(self, prefix: str) -> list[str]:
        """Return every key under ``prefix`` (a folder-like path), sorted."""

    # -- format helpers --------------------------------------------------------

    def write_json(self, key: str, obj: Any, *, minify: bool = True) -> None:
        """Write a JSON document (minified by default, for the frontend)."""
        if minify:
            text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        else:
            text = json.dumps(obj, ensure_ascii=False, indent=2)
        self.write_bytes(key, (text + "\n").encode("utf-8"))

    def read_json(self, key: str) -> Any:
        return json.loads(self.read_bytes(key))

    def write_json_gz(self, key: str, text: str) -> None:
        """Write already-serialised JSON text, gzip-compressed (bronze)."""
        self.write_bytes(key, gzip.compress(text.encode("utf-8"), mtime=0))

    def read_json_gz(self, key: str) -> str:
        return gzip.decompress(self.read_bytes(key)).decode("utf-8")

    def write_parquet(self, key: str, frame: pl.DataFrame) -> None:
        buffer = io.BytesIO()
        frame.write_parquet(buffer, compression="zstd")
        self.write_bytes(key, buffer.getvalue())

    def read_parquet(self, key: str) -> pl.DataFrame:
        return pl.read_parquet(io.BytesIO(self.read_bytes(key)))
