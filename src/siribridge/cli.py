"""siribridge CLI entrypoint.

Phase 0 exposes `status` / `health` so permissions can be verified before
the capture pipeline exists. Functional `ask` lands with the driver backend.
"""

from __future__ import annotations

import sys

import click

from siribridge import __version__, config


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


if __name__ == "__main__":
    main()
