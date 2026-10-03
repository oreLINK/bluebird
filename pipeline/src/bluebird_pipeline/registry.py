"""A tiny plugin registry shared by the four layers.

Each layer owns one :class:`Registry` (``EXTRACTORS``, ``TRANSFORMERS``,
``AGGREGATORS``, ``DISPLAYERS``). Classes register themselves with a decorator::

    @register_extractor("open_meteo_ensemble")
    class ExtractorOpenMeteoEnsemble(Extractor): ...

:func:`load_plugins` imports every module of the four layer packages so that
dropping a new file in a layer folder is enough to make it available.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

LAYER_PACKAGES = (
    "bluebird_pipeline.bronze",
    "bluebird_pipeline.silver",
    "bluebird_pipeline.gold",
    "bluebird_pipeline.diamond",
)


class RegistryError(KeyError):
    """Raised on duplicate registration or unknown plugin id."""

    def __str__(self) -> str:  # KeyError quotes its message by default
        return str(self.args[0])


class Registry[T]:
    """Map plugin ids to classes of one kind."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._classes: dict[str, type[T]] = {}

    def register(self, plugin_id: str) -> Callable[[type[T]], type[T]]:
        """Class decorator registering ``cls`` under ``plugin_id``."""

        def decorator(cls: type[T]) -> type[T]:
            existing = self._classes.get(plugin_id)
            if existing is not None and existing is not cls:
                raise RegistryError(
                    f"{self.kind} '{plugin_id}' is already registered by {existing.__qualname__}"
                )
            cls.id = plugin_id  # type: ignore[attr-defined]
            self._classes[plugin_id] = cls
            return cls

        return decorator

    def get(self, plugin_id: str) -> type[T]:
        try:
            return self._classes[plugin_id]
        except KeyError:
            available = ", ".join(sorted(self._classes)) or "none"
            raise RegistryError(
                f"unknown {self.kind} '{plugin_id}' (available: {available})"
            ) from None

    def ids(self) -> list[str]:
        return sorted(self._classes)

    def items(self) -> list[tuple[str, type[T]]]:
        return sorted(self._classes.items())

    def __contains__(self, plugin_id: object) -> bool:
        return plugin_id in self._classes


def autodiscover(package_name: str) -> None:
    """Import every public module of ``package_name`` (modules starting with '_' are skipped)."""
    package = importlib.import_module(package_name)
    for module in pkgutil.iter_modules(package.__path__):
        if not module.name.startswith("_") and module.name != "base":
            importlib.import_module(f"{package_name}.{module.name}")


def load_plugins() -> None:
    """Register every Extractor, Transformer, Aggregator and Displayer."""
    for package_name in LAYER_PACKAGES:
        autodiscover(package_name)
