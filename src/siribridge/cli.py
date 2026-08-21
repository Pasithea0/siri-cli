"""siribridge CLI.

Primary usage is a bare query:

    siri "what time is it"
    siri what time is it

The first argument(s) are joined as the query and sent to the real macOS
Siri, with the captured response printed. A few built-in subcommands are
also available: `status`, `health`.
"""

from __future__ import annotations

import sys

import click

from siribridge import __version__, config


@click.command(context_settings={"ignore_unknown_options": False})
@click.argument("query", nargs=-1, required=False)
@click.option("--timeout", default=30.0, show_default=True,
              help="Max seconds to wait for Siri's response to settle.")
@click.option("--backend", default="siriai", show_default=True,
              help="siriai (macOS27 Siri AI app) or typetosiri (macOS26 overlay).")
@click.version_option(__version__)
def main(query: tuple[str, ...], timeout: float, backend: str) -> None:
    """Ask the real macOS Siri from the command line.

    Pass a query in quotes (or as bare words) — e.g. `siri "what time is it"`.
    """
    if not query:
        _print_usage()
        sys.exit(0)

    # Built-in subcommands.
    first = query[0].lower()
    if first == "status":
        _status_cmd()
        return
    if first == "health":
        _health_cmd()
        return
    if first in ("-h", "--help"):
        click.echo(main.get_help(click.Context(main)))
        return

    # Otherwise treat everything as the query.
    query_text = " ".join(query)
    _ask_cmd(query_text, timeout=timeout, backend=backend)


def _ask_cmd(query: str, timeout: float, backend: str) -> None:
    from siribridge.driver.base import SiriError
    from siribridge.driver.siriai import SiriAiBackend
    from siribridge.driver.typetosiri import TypeToSiriBackend

    if backend == "siriai":
        backend_obj = SiriAiBackend()
    elif backend == "typetosiri":
        backend_obj = TypeToSiriBackend()
    else:
        click.echo(f"error: unknown backend: {backend}", err=True)
        sys.exit(1)
    try:
        resp = backend_obj.ask(query, timeout_s=timeout)
    except SiriError as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    click.echo(resp.text)


def _status_cmd() -> None:
    status = config.check()
    for line in status.summary():
        click.echo(line)
    if not status.all_required:
        click.echo("\nMissing permissions — how to enable:")
        for name, guide in config.how_to_enable().items():
            click.echo(f"  [{name}] {guide}")
        sys.exit(1)


def _health_cmd() -> None:
    status = config.check()
    if status.all_required:
        click.echo("ok")
    else:
        click.echo("missing: " + ", ".join(
            n for n, g in config.how_to_enable().items()
        ))
        sys.exit(1)


def _print_usage() -> None:
    click.echo(
        "siribridge — ask the real macOS Siri from the CLI\n"
        "\n"
        "Usage:\n"
        '  siri "what time is it"      Ask Siri (response printed)\n'
        "  siri what time is it        Same, without quotes\n"
        "  siri status                 Check permissions + environment\n"
        "  siri health                 Exit 0 if ready\n"
        "  siri --version              Show version\n"
        "\n"
        "Options:\n"
        "  --backend siriai|typetosiri  Backend to use (default: siriai)\n"
        "  --timeout SECONDS            Max wait for the response (default: 30)"
    )


if __name__ == "__main__":
    main()
