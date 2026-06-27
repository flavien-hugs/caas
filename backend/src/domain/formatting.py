"""
Pure formatting helpers shared by Jinja email templates and any other view
layer that needs French-locale output.

Ported from :py:mod:`app.core.ui`. The implementation must stay byte-identical
to the legacy one so a row written by ``app/`` and a row written by
``backend/`` render to the same email output during the strangler phase. A
TypeScript mirror lives under ``frontend/src/lib/utils/format-*.ts`` (added
when the SvelteKit chunk lands) — both sides are pinned with reference-value
tests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

_MONTHS_FR = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]
_DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def format_price(value: Any) -> Any:
    try:
        return "{:,.0f}".format(float(value)).replace(",", " ")
    except (TypeError, ValueError):
        return value


def format_datetime(value: Any, format_type: str = "full") -> Any:
    try:
        if isinstance(value, str):
            iso = value.replace("Z", "+00:00") if value.endswith("Z") else value
            dt = datetime.fromisoformat(iso)
        else:
            dt = value
        if not isinstance(dt, datetime):
            return value

        day_name = _DAYS_FR[dt.weekday()]
        month_name = _MONTHS_FR[dt.month - 1]

        if format_type == "full":
            return f"{day_name} {dt.day:02d} {month_name} {dt.year} à {dt.hour:02d}h{dt.minute:02d}"
        return f"{dt.day:02d} {month_name} {dt.year}"
    except Exception:
        return value
