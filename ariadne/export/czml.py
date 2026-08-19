"""
czml.py

CZML export for the Cesium-based dashboard: a `document` packet with
clock/interval, one position packet per satellite (time-tagged
Cartesian path), and marker/line packets for conjunction geometry at
TCA. This *is* the visual layer's data format, Cesium consumes the
output of `to_czml` directly.

Positions are ECI (J2000); Cesium's `"INERTIAL"` reference frame is
ICRF-based, close enough at this project's stated precision (frames.py
already treats TEME->ECI as precession-only, no nutation). CZML
distances are metres and times are ISO-8601, so every position here is
converted from Ariadne's native km and `datetime`.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from ariadne.conjunction.tca import TCAResult
from ariadne.exceptions import ExportError
from ariadne.models.state_vector import Frame, SatelliteState

_KM_TO_M = 1000.0
_DEFAULT_COLOR = (255, 215, 0, 255)
_CONJUNCTION_COLOR = (255, 0, 0, 255)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def document_packet(name: str, states: List[SatelliteState]) -> dict:
    """
    The mandatory first packet of a CZML document: identifies the
    document and sets the clock's interval from the earliest to latest
    epoch across every state being exported.

    Args:
        name: document name, shown in Cesium's UI.
        states: every state that will appear in the document (across
            all satellites), used only for their epochs.

    Raises:
        ExportError: `states` is empty.
    """
    if not states:
        raise ExportError("Cannot build a CZML document packet from an empty state list.")

    epochs = [state.epoch for state in states]
    start, stop = min(epochs), max(epochs)

    return {
        "id": "document",
        "name": name,
        "version": "1.0",
        "clock": {
            "interval": f"{_iso(start)}/{_iso(stop)}",
            "currentTime": _iso(start),
            "multiplier": 60,
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER",
        },
    }


def satellite_position_packet(
    states: List[SatelliteState], *, color: Tuple[int, int, int, int] = _DEFAULT_COLOR,
) -> dict:
    """
    A single satellite's position packet: a time-tagged Cartesian path
    plus point/path styling, from a chronological list of states for
    one object.

    Args:
        states: one object's states over time, all ECI, chronological.
        color: RGBA, 0-255 each.

    Raises:
        ExportError: `states` is empty or not all in the ECI frame.
    """
    if not states:
        raise ExportError("Cannot build a CZML position packet from an empty state list.")
    if any(state.frame != Frame.ECI for state in states):
        raise ExportError(
            "CZML position packets require ECI states (Cesium's INERTIAL "
            "reference frame is J2000-referenced); convert with "
            "propagate/frames.py first."
        )

    epoch = states[0].epoch
    cartesian = []
    for state in states:
        t = (state.epoch - epoch).total_seconds()
        cartesian.extend([t, *(state.position * _KM_TO_M)])

    norad_id = states[0].norad_id
    packet_id = f"satellite/{norad_id}" if norad_id is not None else f"satellite/{id(states)}"
    display_name = states[0].name or (str(norad_id) if norad_id is not None else "Unknown")

    return {
        "id": packet_id,
        "name": display_name,
        "position": {
            "epoch": _iso(epoch),
            "referenceFrame": "INERTIAL",
            "cartesian": cartesian,
        },
        "path": {
            "material": {"solidColor": {"color": {"rgba": list(color)}}},
            "width": 1,
            "resolution": 120,
        },
        "point": {"pixelSize": 8, "color": {"rgba": list(color)}},
    }


def conjunction_packet(
    tca: TCAResult,
    *,
    primary_id: str = "primary",
    secondary_id: str = "secondary",
    color: Tuple[int, int, int, int] = _CONJUNCTION_COLOR,
) -> dict:
    """
    Conjunction geometry at TCA: a marker at the encounter's midpoint
    plus a line connecting the two objects' actual positions, both
    static (not time-tagged, since this is a single instant) and only
    shown during that instant via `availability`.

    Args:
        tca: the TCA result to visualize.
        primary_id, secondary_id: identifiers for the packet id/name,
            should match the ids used for each object's own
            `satellite_position_packet`.
        color: RGBA, 0-255 each.
    """
    epoch_iso = _iso(tca.epoch)
    primary_m = (tca.primary_state[:3] * _KM_TO_M).tolist()
    secondary_m = (tca.secondary_state[:3] * _KM_TO_M).tolist()
    midpoint = [(p + s) / 2.0 for p, s in zip(primary_m, secondary_m)]

    return {
        "id": f"conjunction/{primary_id}-{secondary_id}",
        "name": f"TCA: {primary_id} vs {secondary_id} ({tca.miss_distance:.3f} km)",
        "availability": epoch_iso,
        "position": {"referenceFrame": "INERTIAL", "cartesian": midpoint},
        "point": {
            "pixelSize": 14,
            "color": {"rgba": list(color)},
            "outlineColor": {"rgba": [255, 255, 255, 255]},
            "outlineWidth": 2,
        },
        "polyline": {
            "positions": {"referenceFrame": "INERTIAL", "cartesian": primary_m + secondary_m},
            "width": 2,
            "material": {"solidColor": {"color": {"rgba": list(color)}}},
        },
    }


def to_czml(
    name: str,
    satellites: List[List[SatelliteState]],
    conjunctions: Optional[List[Tuple[str, str, TCAResult]]] = None,
) -> List[dict]:
    """
    Assemble a full CZML document: a document packet, one position
    packet per satellite, and one packet per conjunction event.

    Args:
        name: document name.
        satellites: one chronological state list per object.
        conjunctions: (primary_id, secondary_id, TCAResult) triples,
            `primary_id`/`secondary_id` should match the ids each
            involved satellite's own packet gets (its `norad_id`, if
            set).

    Returns:
        List of CZML packets (dicts); the document itself is
        `json.dumps`-ready, e.g. `json.dumps(to_czml(...))`.
    """
    all_states = [state for states in satellites for state in states]
    packets = [document_packet(name, all_states)]
    packets.extend(satellite_position_packet(states) for states in satellites)
    for primary_id, secondary_id, tca in (conjunctions or []):
        packets.append(conjunction_packet(tca, primary_id=primary_id, secondary_id=secondary_id))

    return packets
