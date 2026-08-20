"""
propagate.py

CLI: propagate orbit state forward in time, either a TLE via SGP4 or a
state-vector file via numerical two-body + J2 integration, and export
the result as a table, JSON, CSV, or CZML.
"""

import json
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Sequence

import click

from ariadne.cli._util import parse_iso_epoch, select_tle
from ariadne.exceptions import AriadneError
from ariadne.export import state_to_dict, to_czml, write_states_csv
from ariadne.ingest.sniff import load_file as load_state_file
from ariadne.ingest.tle import load_tle_file
from ariadne.models.state_vector import SatelliteState
from ariadne.propagate import numerical
from ariadne.propagate.sgp4 import propagate as sgp4_propagate


def _epoch_series(epoch: Sequence[str], start: Optional[str], stop: Optional[str], step_s: float):
    if epoch:
        return [parse_iso_epoch(e) for e in epoch]
    if start and stop:
        if step_s <= 0:
            raise click.UsageError("--step-s must be positive.")
        t0, t1 = parse_iso_epoch(start), parse_iso_epoch(stop)
        step = timedelta(seconds=step_s)
        epochs, t = [], t0
        while t <= t1:
            epochs.append(t)
            t += step
        return epochs
    raise click.UsageError("Provide --epoch (repeatable) or --start/--stop/--step-s.")


def _emit(states: List[SatelliteState], fmt: str, out_path: Optional[str], doc_name: str) -> None:
    if fmt == "json":
        payload = [state_to_dict(s) for s in states]
        text = json.dumps(payload, indent=2)
    elif fmt == "csv":
        if not out_path:
            raise click.UsageError("--format csv requires --out.")
        write_states_csv(states, out_path)
        click.echo(f"wrote {out_path}")
        return
    elif fmt == "czml":
        text = json.dumps(to_czml(doc_name, [states]), indent=2)
    else:
        for state in states:
            r, v = state.position, state.velocity
            click.echo(
                f"{state.epoch.isoformat()}  "
                f"r=[{r[0]:.3f}, {r[1]:.3f}, {r[2]:.3f}] km  "
                f"v=[{v[0]:.5f}, {v[1]:.5f}, {v[2]:.5f}] km/s  "
                f"({state.frame.value})"
            )
        return

    if out_path:
        Path(out_path).write_text(text)
        click.echo(f"wrote {out_path}")
    else:
        click.echo(text)


_FORMAT_OPTION = click.option(
    "--format", "fmt", type=click.Choice(["table", "json", "csv", "czml"]),
    default="table", show_default=True,
)
_OUT_OPTION = click.option("--out", "out_path", type=click.Path(dir_okay=False))


@click.group("propagate")
def propagate() -> None:
    """Propagate orbit state forward in time."""


@propagate.command("sgp4")
@click.argument("tle_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--norad-id", type=int, help="Select this object from a multi-TLE file.")
@click.option("--epoch", multiple=True, help="Target epoch, ISO-8601 UTC. Repeatable.")
@click.option("--start", help="Series start epoch, ISO-8601 UTC.")
@click.option("--stop", help="Series stop epoch, ISO-8601 UTC.")
@click.option("--step-s", type=float, default=60.0, show_default=True, help="Series step, seconds.")
@_FORMAT_OPTION
@_OUT_OPTION
def propagate_sgp4(
    tle_path: str, norad_id: Optional[int], epoch: Sequence[str],
    start: Optional[str], stop: Optional[str], step_s: float,
    fmt: str, out_path: Optional[str],
) -> None:
    """Propagate a TLE using SGP4."""
    try:
        tle = select_tle(load_tle_file(tle_path), norad_id, tle_path)
        epochs = _epoch_series(epoch, start, stop, step_s)
        states = [sgp4_propagate(tle, e) for e in epochs]
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    _emit(states, fmt, out_path, doc_name=tle.name or str(tle.norad_id))


@propagate.command("numerical")
@click.argument("state_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--dt-s", "dt_list", type=float, multiple=True,
    help="Seconds from each input state's own epoch to propagate to. Repeatable.",
)
@click.option(
    "--duration-s", type=float,
    help="Propagate across [0, duration-s] at --step-s intervals, instead of --dt-s targets.",
)
@click.option("--step-s", type=float, default=60.0, show_default=True)
@click.option("--method", type=click.Choice(["rk4", "rk45"]), default="rk45", show_default=True)
@click.option("--no-j2", is_flag=True, help="Disable the J2 perturbation term.")
@_FORMAT_OPTION
@_OUT_OPTION
def propagate_numerical(
    state_path: str, dt_list: Sequence[float], duration_s: Optional[float], step_s: float,
    method: str, no_j2: bool, fmt: str, out_path: Optional[str],
) -> None:
    """Propagate a state-vector file (CSV/TXT) using two-body + J2 numerical integration."""
    try:
        records, warnings = load_state_file(state_path)
    except AriadneError as exc:
        raise click.ClickException(str(exc))
    for warning in warnings:
        click.echo(f"warning: {warning}", err=True)
    if not records or not isinstance(records[0], SatelliteState):
        raise click.ClickException(
            f"{state_path} did not parse to state vectors (looks like a TLE file?)."
        )

    if duration_s is not None:
        if step_s <= 0:
            raise click.UsageError("--step-s must be positive.")
        dts, t = [], 0.0
        while t <= duration_s:
            dts.append(t)
            t += step_s
    else:
        dts = list(dt_list) or [0.0]

    include_j2 = not no_j2
    states: List[SatelliteState] = []
    try:
        for record in records:
            vector0 = record.as_vector()
            for dt in dts:
                if method == "rk4":
                    vector = numerical.propagate_rk4(vector0, dt, include_j2=include_j2)
                else:
                    vector = numerical.propagate(vector0, dt, include_j2=include_j2)
                states.append(SatelliteState.from_vector(
                    vector, record.epoch + timedelta(seconds=dt), record.frame,
                    norad_id=record.norad_id, name=record.name,
                ))
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    _emit(states, fmt, out_path, doc_name=Path(state_path).stem)
