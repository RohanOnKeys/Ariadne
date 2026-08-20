"""
fetch.py

CLI: retrieve TLEs from CelesTrak (unauthenticated) or Space-Track
(authenticated, credentials from the environment), disk-cached via
`ariadne.fetch.cache`.
"""

from pathlib import Path
from typing import Optional

import click

from ariadne.exceptions import AriadneError
from ariadne.fetch import celestrak, spacetrack
from ariadne.fetch.cache import get_cached


def _emit(text: str, out_path: Optional[str]) -> None:
    if out_path:
        Path(out_path).write_text(text)
        click.echo(f"wrote {out_path}")
    else:
        click.echo(text, nl=False)


def _warn_if_stale(is_stale: bool, age_hours: float) -> None:
    if is_stale:
        click.echo(
            f"warning: fresh fetch failed, serving stale cache ({age_hours:.1f}h old)",
            err=True,
        )


@click.group("fetch")
def fetch() -> None:
    """Fetch TLE data from CelesTrak or Space-Track."""


@fetch.command("group")
@click.argument("group_name")
@click.option(
    "--out", "out_path", type=click.Path(dir_okay=False),
    help="Write TLE text here instead of stdout.",
)
@click.option(
    "--ttl-hours", type=float, default=6.0, show_default=True, help="Cache freshness window.",
)
@click.option("--no-cache", is_flag=True, help="Bypass the cache and force a fresh fetch.")
def fetch_group(group_name: str, out_path: Optional[str], ttl_hours: float, no_cache: bool) -> None:
    """Fetch every object in a CelesTrak group (e.g. 'active', 'stations', 'starlink')."""
    try:
        if no_cache:
            text, is_stale, age_hours = celestrak.fetch_group_text(group_name), False, 0.0
        else:
            result = get_cached(
                "celestrak", f"GROUP={group_name}",
                lambda: celestrak.fetch_group_text(group_name), ttl_hours=ttl_hours,
            )
            text, is_stale, age_hours = result.text, result.is_stale, result.age_hours
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    _warn_if_stale(is_stale, age_hours)
    _emit(text, out_path)


@fetch.command("norad")
@click.argument("norad_id", type=int)
@click.option(
    "--provider", type=click.Choice(["celestrak", "spacetrack"]),
    default="celestrak", show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(dir_okay=False),
    help="Write TLE text here instead of stdout.",
)
@click.option(
    "--ttl-hours", type=float, default=6.0, show_default=True, help="Cache freshness window.",
)
@click.option("--no-cache", is_flag=True, help="Bypass the cache and force a fresh fetch.")
def fetch_norad(
    norad_id: int, provider: str, out_path: Optional[str], ttl_hours: float, no_cache: bool,
) -> None:
    """Fetch a single object's latest TLE by NORAD catalog number."""
    fetch_text = (
        celestrak.fetch_norad_id_text if provider == "celestrak" else spacetrack.fetch_norad_id_text
    )
    try:
        if no_cache:
            text, is_stale, age_hours = fetch_text(norad_id), False, 0.0
        else:
            result = get_cached(
                provider, f"CATNR={norad_id}", lambda: fetch_text(norad_id), ttl_hours=ttl_hours,
            )
            text, is_stale, age_hours = result.text, result.is_stale, result.age_hours
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    _warn_if_stale(is_stale, age_hours)
    _emit(text, out_path)
