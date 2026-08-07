from dataclasses import dataclass

from lk_metro.GD.Point import Point
from lk_metro.Render.Types import Bounds


@dataclass
class _PlacementContext:
    positions: dict[str, Point]
    memberships: dict[str, set[str]]
    route_bounds: list[Bounds]
    canvas_bounds: Bounds
    occupied: list[Bounds]
    placed_labels: list[tuple[str, Bounds]]
    fixed_bounds: list[Bounds]
