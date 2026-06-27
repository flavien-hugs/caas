from __future__ import annotations

from typing import Protocol

from src.domain import ConfigSection


class SettingsRepositoryPort(Protocol):
    """Outbound port for runtime configuration storage.

    Values are opaque ``dict`` blobs per section (secrets already encrypted by
    the caller). The resolver merges them over env defaults.
    """

    async def get(self, section: ConfigSection) -> dict | None: ...

    async def set(self, section: ConfigSection, values: dict) -> None:
        """Insert-or-update the section blob."""
        ...

    async def all(self) -> dict[str, dict]:
        """Every stored section keyed by its section name."""
        ...
