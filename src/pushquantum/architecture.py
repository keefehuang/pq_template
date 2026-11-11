"""Zones (from a JSON spec, see `architectures/default.json`) and the initial loading of qubits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pushquantum.move import Site

ArchitectureSpec = str | Path | dict[str, Any]


@dataclass(frozen=True)
class Zone:
    name: str
    x: tuple[int, int]
    y: tuple[int, int]
    operations: frozenset[str]
    spacing: float = 1.0
    pair_axis: str | None = None
    pair_distance: float | None = None


def load_spec(spec: ArchitectureSpec | None = None) -> dict[str, Any]:
    """A spec from a path, a dict, or (if `None`) the bundled default."""
    if spec is None:
        return json.loads(resources.files("pushquantum").joinpath("architectures/default.json").read_text("utf-8"))
    if isinstance(spec, dict):
        return spec
    return json.loads(Path(spec).read_text(encoding="utf-8"))


def _parse_zone(name: str, z: dict[str, Any]) -> Zone:
    pairs = z.get("pairs")
    return Zone(
        name=name,
        x=(int(z["x"][0]), int(z["x"][1])),
        y=(int(z["y"][0]), int(z["y"][1])),
        operations=frozenset(z.get("operations", ())),
        spacing=float(z.get("spacing", 1.0)),
        pair_axis=pairs["axis"] if pairs else None,
        pair_distance=float(pairs["distance"]) if pairs else None,
    )


class Architecture:
    """The zones of `spec` and `initial_loading` (qubit `0..n-1` -> `(x, y)` site in the loading zone)."""

    def __init__(self, initial_loading: dict[int, Site], spec: ArchitectureSpec | None = None) -> None:
        data = load_spec(spec)
        self.zones: dict[str, Zone] = {name: _parse_zone(name, z) for name, z in data["zones"].items()}
        self.loading_zone: str = data.get("loading_zone", "storage")
        self.initial_loading: dict[int, Site] = dict(initial_loading)
