"""Diamond layer contract: ``Displayer`` classes shape gold data for the frontend.

Diamond files are small, minified JSON documents that the static site fetches
directly. Their shape is defined by pydantic models in :mod:`.models`, exported
as JSON Schemas so the frontend types stay in sync.

Every registered Displayer runs on each diamond run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel

from ..context import RunContext
from ..registry import Registry


@dataclass(frozen=True)
class DiamondArtifact:
    """One file to write: a storage key and its payload."""

    key: str
    payload: BaseModel


class Displayer(ABC):
    """Build frontend payloads from gold data.

    Subclasses implement :meth:`display` and register with
    ``@register_displayer("id")``.
    """

    id: ClassVar[str]

    @abstractmethod
    def display(self, ctx: RunContext) -> list[DiamondArtifact]:
        """Return the files to publish for this run."""


DISPLAYERS: Registry[Displayer] = Registry("displayer")
register_displayer = DISPLAYERS.register
