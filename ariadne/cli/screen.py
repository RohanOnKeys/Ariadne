"""
screen.py

CLI: screen a catalog of TLE objects against one primary for close
approaches within a miss-distance threshold, all propagated to a
common reference epoch via SGP4 before screening.
"""

import json
from pathlib import Path
from typing import Optional

import click

from ariadne.cli._util import parse_iso_epoch, select_tle
from ariadne.conjunction.screening import screen_catalog
from ariadne.exceptions import AriadneError
from ariadne.export.csv import write_screening_results_csv
from ariadne.export.json import screening_result_to_dict
from ariadne.ingest.tle import load_tle_file
from ariadne.propagate.sgp4 import propagate as sgp4_propagate


@click.command("screen")
@click.argument("primary_tle", type=click.Path(exists=True, dir_okay=False))
@click.argument("catalog_tle", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--epoch", required=True,
    help="Reference epoch every object is propagated to before screening, ISO-8601 UTC.",
)
@click.option(
    "--threshold-km", type=float, required=True,
    help="Only report secondaries with TCA miss distance at or below this.",
)
@click.option("--primary-norad-id", type=int)
@click.option(
    "--window-s", type=(float, float), default=(-1800.0, 1800.0), show_default=True,
    help="TCA search window per secondary, seconds from --epoch.",
)
@click.option("--no-j2", is_flag=True, help="Disable the J2 perturbation term in the TCA search.")
@click.option(
    "--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table",
    show_default=True,
)
@click.option("--out", "out_path", type=click.Path(dir_okay=False))
def screen(
    primary_tle: str, catalog_tle: str, epoch: str, threshold_km: float,
    primary_norad_id: Optional[int], window_s, no_j2: bool, fmt: str, out_path: Optional[str],
) -> None:
    """Screen a catalog against one primary object for close approaches."""
    try:
        epoch0 = parse_iso_epoch(epoch)

        primary = select_tle(load_tle_file(primary_tle), primary_norad_id, primary_tle)
        primary_state = sgp4_propagate(primary, epoch0).as_vector()

        secondaries = []
        for tle in load_tle_file(catalog_tle):
            if tle.norad_id == primary.norad_id:
                continue
            state = sgp4_propagate(tle, epoch0).as_vector()
            secondaries.append((tle.norad_id, tle.name, state))

        results = screen_catalog(
            epoch0, primary_state, secondaries, threshold_km, window_s, include_j2=not no_j2,
        )
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        text = json.dumps([screening_result_to_dict(r) for r in results], indent=2)
        if out_path:
            Path(out_path).write_text(text)
            click.echo(f"wrote {out_path}")
        else:
            click.echo(text)
    elif fmt == "csv":
        if not out_path:
            raise click.UsageError("--format csv requires --out.")
        write_screening_results_csv(results, out_path)
        click.echo(f"wrote {out_path}")
    else:
        click.echo(f"{len(results)} conjunction(s) within {threshold_km} km:")
        for result in results:
            label = result.secondary_name or result.secondary_norad_id
            click.echo(
                f"  {label}: {result.tca.miss_distance:.3f} km at {result.tca.epoch.isoformat()}"
            )
