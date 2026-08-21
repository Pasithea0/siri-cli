"""siribridge CLI entrypoint.

Phase 0 exposes `status` / `health` so permissions can be verified before
the capture pipeline exists. Functional `ask` lands with the driver backend.
"""

from __future__ import annotations

import sys

import click

from siribridge import __version__, config
from siribridge.driver.typetosiri import TypeToSiriBackend


@click.group()
@click.version_option(__version__)
def main() -> None:
    """Bidirectional CUA-to-Siri interface."""


@main.command("status")
def status_cmd() -> None:
    """Print environment + permission status."""
    status = config.check()
    for line in status.summary():
        click.echo(line)
    if not status.all_required:
        click.echo("\nMissing permissions — how to enable:")
        for name, guide in config.how_to_enable().items():
            click.echo(f"  [{name}] {guide}")
        sys.exit(1)


@main.command("health")
def health_cmd() -> None:
    """Exit 0 if all required permissions are present, else non-zero."""
    status = config.check()
    if status.all_required:
        click.echo("ok")
    else:
        click.echo("missing: " + ", ".join(
            n for n, g in config.how_to_enable().items()
        ))
        sys.exit(1)


@main.command("ask")
@click.argument("query")
@click.option("--timeout", default=30.0, show_default=True, help="Max seconds to wait for Siri's response to settle.")
@click.option("--backend", default="typetosiri", show_default=True, help="Backend to use (typetosiri for now; spotlight later).")
def ask_cmd(query: str, timeout: float, backend: str) -> None:
    """Ask the real macOS Siri and print the captured response.

    QUERY is the natural-language question/command, e.g. "what time is it".
    """
    if backend != "typetosiri":
        click.echo(f"Unknown backend: {backend}", err=True)
        sys.exit(1)
    from siribridge.driver.base import SiriError

    backend_obj = TypeToSiriBackend()
    try:
        resp = backend_obj.ask(query, timeout_s=timeout)
    except SiriError as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    click.echo(resp.text)


if __name__ == "__main__":
    main()
