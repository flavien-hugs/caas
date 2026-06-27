"""
Page domain — the page builder's data model.

A ``Page`` is a sequence of typed ``Block`` records. The backend treats
``Block.props`` as an opaque ``dict``; per-type validation lives entirely
client-side (Zod schemas in the SvelteKit app), so the backend stays one
step removed from UI-level concerns and adding a new block type doesn't
require a backend release.

Slug is the public identifier (``GET /pages/{slug}``). Normalisation
happens at construction time so the storage layer never sees a malformed
slug.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class PageStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


# Lowercase letters/digits + hyphens. No leading/trailing hyphen, no
# consecutive hyphens. 2-100 chars (matches typical URL slug limits).
_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?$")


def normalize_slug(raw: str) -> str:
    """Lower-case, trim, collapse whitespace/underscores to hyphens.

    Raises ``ValueError`` if the result doesn't match :data:`_SLUG_RE`.
    """
    s = raw.strip().lower()
    # whitespace and underscores → single hyphen
    s = re.sub(r"[\s_]+", "-", s)
    # strip non-allowed chars
    s = re.sub(r"[^a-z0-9-]", "", s)
    # collapse multiple hyphens
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if not _SLUG_RE.fullmatch(s):
        raise ValueError(f"invalid slug: {raw!r}")
    return s


@dataclass(frozen=True, slots=True)
class Block:
    id: str
    type: str
    props: dict[str, Any]

    @staticmethod
    def new(type: str, props: dict[str, Any] | None = None) -> "Block":
        return Block(id=str(uuid4()), type=type, props=dict(props or {}))


@dataclass(frozen=True, slots=True)
class Page:
    id: str
    slug: str
    title: str
    blocks: tuple[Block, ...] = field(default_factory=tuple)
    status: PageStatus = PageStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: datetime | None = None

    @staticmethod
    def new(slug: str, title: str) -> "Page":
        now = datetime.now(timezone.utc)
        return Page(
            id=str(uuid4()),
            slug=normalize_slug(slug),
            title=title.strip(),
            blocks=(),
            status=PageStatus.DRAFT,
            created_at=now,
            updated_at=now,
            published_at=None,
        )

    def with_blocks(self, blocks: list[Block] | tuple[Block, ...]) -> "Page":
        return replace(self, blocks=tuple(blocks), updated_at=datetime.now(timezone.utc))

    def with_title(self, title: str) -> "Page":
        return replace(self, title=title.strip(), updated_at=datetime.now(timezone.utc))

    def publish(self) -> "Page":
        now = datetime.now(timezone.utc)
        return replace(self, status=PageStatus.PUBLISHED, published_at=now, updated_at=now)

    def unpublish(self) -> "Page":
        return replace(self, status=PageStatus.DRAFT, updated_at=datetime.now(timezone.utc))

    @property
    def is_published(self) -> bool:
        return self.status is PageStatus.PUBLISHED
