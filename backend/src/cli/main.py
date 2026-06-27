import asyncio
import logging

import typer
import uvicorn

from src.application.use_cases import ReconcilePendingInput
from src.cli.seed_pages import run_seed_pages
from src.infrastructure.http.deps import build_reconcile_pending, build_resolved_config

cli = typer.Typer(pretty_exceptions_show_locals=False, no_args_is_help=True)

log = logging.getLogger(__name__)


@cli.command("run")
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(9090, help="Bind port"),
    reload: bool = typer.Option(False, help="Auto-reload on code changes"),
) -> None:
    """Start the HTTP API."""
    uvicorn.run(
        "src.infrastructure.http.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


async def run_sync_iteration(book_ids: list[str] | None):
    """Run one ReconcilePending pass and echo a summary line.

    Exposed at module scope so :py:func:`sync_pending_loop` and the unit tests
    can drive the same code path without going through Typer.
    """
    cfg = await build_resolved_config()
    summary = await build_reconcile_pending(cfg).execute(ReconcilePendingInput(book_ids=book_ids or None))
    typer.echo(
        f"processed={summary.processed} confirmed={summary.confirmed} "
        f"failed={summary.failed} skipped={summary.skipped} errored={summary.errored}"
    )
    for pid in summary.purchase_ids_confirmed:
        typer.echo(f"  SUCCESS  {pid}")
    return summary


@cli.command("sync-pending")
def sync_pending(
    book_id: list[str] = typer.Option(
        None,
        "--book-id",
        "-b",
        help="Filter by product (repeatable: -b lutte-contre-fraude -b sbbs-kids)",
    ),
) -> None:
    """Reconcile PENDING/FAILED purchases against the payment provider — one shot."""
    asyncio.run(run_sync_iteration(book_id))


async def sync_pending_loop_body(book_ids: list[str] | None, interval_seconds: int) -> None:
    """Long-running reconciliation loop. Catches every iteration's exception
    so a single bad run never kills the worker — it just gets retried on the
    next tick."""
    log.info("sync-pending loop starting (book_ids=%s, interval=%ss)", book_ids, interval_seconds)
    while True:
        try:
            await run_sync_iteration(book_ids)
        except Exception:
            log.exception("sync-pending iteration errored — retrying on next tick")
        await asyncio.sleep(interval_seconds)


@cli.command("sync-pending-loop")
def sync_pending_loop(
    book_id: list[str] = typer.Option(
        None,
        "--book-id",
        "-b",
        help="Filter by product (repeatable). Defaults to all migrated products.",
    ),
    interval_seconds: int = typer.Option(
        900,
        "--interval-seconds",
        "-i",
        envvar="SYNC_INTERVAL_SECONDS",
        help="Seconds to sleep between iterations (env: SYNC_INTERVAL_SECONDS).",
    ),
) -> None:
    """
    Run sync-pending forever with a sleep between iterations.

    Designed for the cron-worker compose service. The interval is tunable via
    SYNC_INTERVAL_SECONDS so we can shorten it in staging and lengthen it in
    prod without rebuilding the image.
    """
    asyncio.run(sync_pending_loop_body(book_id, interval_seconds))


@cli.command("seed-pages")
def seed_pages() -> None:
    """Idempotent seed for builder pages (currently: lutte-contre-fraude).

    Safe to run on every deploy — existing pages are left untouched.
    """
    run_seed_pages()


if __name__ == "__main__":
    cli()
