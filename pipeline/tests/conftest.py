"""Shared fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from _factories import RUN_DATE, TWO_STATIONS, tiny_config_dir

from bluebird_pipeline.config import Config, load_config
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.registry import load_plugins
from bluebird_pipeline.storage import LocalStorage

load_plugins()


@pytest.fixture
def repo_config() -> Config:
    return load_config()


@pytest.fixture
def two_station_config(tmp_path: Path) -> Config:
    return load_config(tiny_config_dir(tmp_path, TWO_STATIONS))


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(tmp_path / "data")


@pytest.fixture
def ctx(two_station_config: Config, storage: LocalStorage) -> RunContext:
    return RunContext.create(
        two_station_config,
        storage,
        run_date=RUN_DATE,
        now=datetime(2026, 12, 14, 4, 30, tzinfo=UTC),
    )
