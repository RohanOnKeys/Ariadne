"""
estimate.py

CLI: run the UKF (orbit determination) over a sequence of direct
position/velocity measurements from a state-vector file, reporting the
filtered final state, its covariance, and a NIS consistency check.
"""

import json
from pathlib import Path
from typing import Optional

import click
import numpy as np

from ariadne.estimate.diagnostics import compute_nis, run_nis_consistency_check
from ariadne.estimate.noise_models import (
    build_measurement_noise,
    build_process_noise_discrete_white_noise,
)
from ariadne.estimate.ukf import UnscentedKalmanFilter
from ariadne.exceptions import AriadneError
from ariadne.export import state_to_dict
from ariadne.ingest.sniff import load_file
from ariadne.models.state_vector import SatelliteState


@click.command("estimate")
@click.argument("measurements_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--pos-sigma", type=float, default=0.1, show_default=True,
    help="Measurement 1-sigma position noise, km.",
)
@click.option(
    "--vel-sigma", type=float, default=1e-4, show_default=True,
    help="Measurement 1-sigma velocity noise, km/s.",
)
@click.option(
    "--sigma-accel", type=float, default=1e-6, show_default=True,
    help="Process noise 1-sigma un-modeled acceleration, km/s^2.",
)
@click.option(
    "--initial-pos-sigma", type=float, default=1.0, show_default=True,
    help="Initial covariance 1-sigma position, km.",
)
@click.option(
    "--initial-vel-sigma", type=float, default=1e-3, show_default=True,
    help="Initial covariance 1-sigma velocity, km/s.",
)
@click.option(
    "--format", "fmt", type=click.Choice(["table", "json"]), default="table", show_default=True,
)
@click.option("--out", "out_path", type=click.Path(dir_okay=False))
def estimate(
    measurements_path: str, pos_sigma: float, vel_sigma: float, sigma_accel: float,
    initial_pos_sigma: float, initial_vel_sigma: float, fmt: str, out_path: Optional[str],
) -> None:
    """Run the UKF over a sequence of position/velocity measurements."""
    try:
        records, warnings = load_file(measurements_path)
    except AriadneError as exc:
        raise click.ClickException(str(exc))
    for warning in warnings:
        click.echo(f"warning: {warning}", err=True)
    if len(records) < 2 or not isinstance(records[0], SatelliteState):
        raise click.ClickException(
            f"{measurements_path} needs at least 2 state-vector measurements "
            "(looks like a TLE file, or too short?)."
        )

    records = sorted(records, key=lambda r: r.epoch)

    x0 = records[0].as_vector()
    P0 = np.diag([initial_pos_sigma**2] * 3 + [initial_vel_sigma**2] * 3)
    R = build_measurement_noise(pos_sigma, vel_sigma)
    ukf = UnscentedKalmanFilter(x0, P0, np.zeros((6, 6)), R)

    nis_sequence = []
    epoch = records[0].epoch
    for record in records[1:]:
        dt = (record.epoch - epoch).total_seconds()
        ukf.Q = build_process_noise_discrete_white_noise(dt, sigma_accel)
        ukf.predict(dt)
        ukf.update(record.as_vector())
        nis_sequence.append(compute_nis(ukf.last_innovation, ukf.last_innovation_cov))
        epoch = record.epoch

    consistency = run_nis_consistency_check(nis_sequence, dof=6)
    final_state = SatelliteState.from_vector(
        ukf.x, epoch, records[0].frame, norad_id=records[0].norad_id, name=records[0].name,
    )

    if fmt == "json":
        payload = {
            "state": state_to_dict(final_state),
            "covariance": ukf.P.tolist(),
            "nis_consistency": consistency,
        }
        text = json.dumps(payload, indent=2)
        if out_path:
            Path(out_path).write_text(text)
            click.echo(f"wrote {out_path}")
        else:
            click.echo(text)
    else:
        click.echo(f"updates: {len(nis_sequence)}")
        click.echo(f"final epoch: {final_state.epoch.isoformat()}")
        click.echo(f"position (km): {final_state.position}")
        click.echo(f"velocity (km/s): {final_state.velocity}")
        click.echo(
            f"NIS consistency: {consistency['verdict']} "
            f"({consistency['fraction_in_bound']:.1%} in-bound, "
            f"95% CI [{consistency['lower_bound']:.2f}, {consistency['upper_bound']:.2f}])"
        )
