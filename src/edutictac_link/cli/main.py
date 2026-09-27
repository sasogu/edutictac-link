"""Interfície de línia d'ordes d'EduTicTac Link."""

from __future__ import annotations

import asyncio
import logging
import socket
import sys

import click

from edutictac_link import __version__
from edutictac_link.config import Config
from edutictac_link.devices import all_profiles
from edutictac_link.doctor import exit_code, run_checks


def _configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _run_server(config: Config) -> None:
    # Importació tardana perquè 'doctor' i 'devices' funcionen sense bleak.
    from edutictac_link.server import LinkServer

    _configure_logging(config.debug)
    logging.getLogger("edutictac_link").info("EduTicTac Link %s", __version__)
    try:
        asyncio.run(LinkServer(config).serve())
    except KeyboardInterrupt:
        click.echo("\nAturat.")
    except OSError as exc:
        raise click.ClickException(
            f"No s'ha pogut escoltar en {config.host}:{config.port} ({exc}). "
            "Potser ja hi ha una altra instància en marxa."
        ) from exc


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--host", default=None, help="Adreça d'escolta (per defecte 127.0.0.1).")
@click.option("--port", type=int, default=None, help="Port d'escolta (per defecte 20111).")
@click.option("--debug/--no-debug", default=None, help="Activa els missatges de depuració.")
@click.version_option(__version__, prog_name="edutictac-link")
@click.pass_context
def main(ctx: click.Context, host: str | None, port: int | None, debug: bool | None):
    """Alternativa lliure a Scratch Link per a Linux.

    Sense suborde, arranca el daemon compatible amb Scratch 3 i TurboWarp.
    """
    config = Config.from_env()
    if host is not None:
        config.host = host
    if port is not None:
        config.port = port
    if debug is not None:
        config.debug = debug
    ctx.obj = config

    if ctx.invoked_subcommand is None:
        _run_server(config)


@main.command()
@click.pass_obj
def run(config: Config) -> None:
    """Arranca el daemon (equivalent a invocar sense suborde)."""
    _run_server(config)


@main.command()
@click.pass_obj
def status(config: Config) -> None:
    """Mostra si el daemon està escoltant."""
    listening = _port_open(config.host, config.port)
    state = "escoltant" if listening else "aturat"
    click.echo(f"EduTicTac Link: {state}")
    click.echo(f"  URL:   ws://{config.host}:{config.port}/scratch/ble")
    click.echo(f"  Origen: {'validat' if config.enforce_origin else 'obert'}")
    sys.exit(0 if listening else 1)


@main.command()
def devices() -> None:
    """Llista els dispositius coneguts i els seus filtres."""
    for profile in all_profiles():
        click.echo(f"{profile.id:<10} {profile.label} [{profile.transport}]")
        if profile.extension:
            click.echo(f"           extensió: {profile.extension}")
        if profile.firmware:
            click.echo(f"           {profile.firmware}")
        if profile.notes:
            click.echo(f"           {profile.notes}")


@main.command()
@click.pass_obj
def doctor(config: Config) -> None:
    """Comprova l'entorn (Python, BlueZ, adaptador, ports, navegadors)."""
    checks = run_checks(config)
    symbols = {"ok": "[ ok ]", "warn": "[avís]", "fail": "[fail]"}
    for check in checks:
        click.echo(f"{symbols.get(check.status, '[ ?? ]')} {check.name}: {check.detail}")
    sys.exit(exit_code(checks))


if __name__ == "__main__":  # pragma: no cover
    main()
