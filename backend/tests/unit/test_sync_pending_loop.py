"""
Tests for the sync-pending CLI loop.

The loop is glue — but the glue carries one critical guarantee: a single
errored iteration must not kill the long-running worker. Without that, a
transient DB hiccup or a provider 500 silently stops the reconciliation,
and abandoned PENDING rows accumulate forever.

This test runs the loop body with a fake iteration that fails once then
succeeds, cancels the task after both ticks, and asserts both iterations
were observed despite the first one raising.
"""

from __future__ import annotations

import asyncio

import pytest

from src.cli import main as cli_main


@pytest.mark.asyncio
async def test_loop_survives_exception_in_iteration(monkeypatch):
    calls: list[list[str] | None] = []
    raised = {"once": False}

    async def flaky_iteration(book_ids):
        calls.append(book_ids)
        if not raised["once"]:
            raised["once"] = True
            raise RuntimeError("transient provider 500")
        return None

    sleeps: list[float] = []
    real_sleep = asyncio.sleep  # bind before monkeypatching, otherwise recursion

    async def fast_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        # Yield once so the loop releases control between ticks; the test
        # cancels after enough iterations are recorded.
        await real_sleep(0)
        if len(calls) >= 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(cli_main, "run_sync_iteration", flaky_iteration)
    monkeypatch.setattr(cli_main.asyncio, "sleep", fast_sleep)

    with pytest.raises(asyncio.CancelledError):
        await cli_main.sync_pending_loop_body(["lutte-contre-fraude"], interval_seconds=900)

    # Both iterations ran (the first raised but was caught), and the loop kept
    # going with the same book_ids filter on each tick.
    assert calls == [["lutte-contre-fraude"], ["lutte-contre-fraude"]]
    # And the configured interval was actually requested.
    assert sleeps[:2] == [900, 900]


@pytest.mark.asyncio
async def test_run_sync_iteration_echoes_summary_and_returns_it(capsys, monkeypatch):
    """The one-shot iteration must echo a parseable summary line — that's
    what makes log scraping straightforward for ops dashboards."""

    class FakeUseCase:
        async def execute(self, cmd):
            from src.application.use_cases.reconcile_pending import ReconcileSummary

            return ReconcileSummary(processed=3, confirmed=1, failed=1, skipped=1, errored=0, purchase_ids_confirmed=["pid_X"])

    # The CLI resolves config then builds the reconcile use case; both bindings
    # live in ``cli_main`` directly (hoisted imports), so patch them here.
    async def fake_build_cfg():
        return object()

    monkeypatch.setattr(cli_main, "build_resolved_config", fake_build_cfg)
    monkeypatch.setattr(cli_main, "build_reconcile_pending", lambda cfg: FakeUseCase())

    summary = await cli_main.run_sync_iteration(["lutte-contre-fraude"])
    assert summary.processed == 3
    out = capsys.readouterr().out
    assert "processed=3 confirmed=1 failed=1 skipped=1 errored=0" in out
    assert "SUCCESS  pid_X" in out
