from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDRouteLabelGeometryMixin import HBDRouteLabelGeometryMixin
from lk_metro.PGD.PGDTypes import Bounds

RouteLabelOption = tuple[Bounds, Point, float, float, float, int]


class HBDRouteLabelOptionMixin(HBDRouteLabelGeometryMixin):
    def _route_label_option(
        self,
        center: Point,
        half_width: float,
        half_height: float,
        clearance: float,
        other_parts: list[tuple[Point, Point]],
        start_distance: float,
    ) -> RouteLabelOption:
        bounds = (
            center[0] - half_width,
            center[1] - half_height,
            center[0] + half_width,
            center[1] + half_height,
        )
        other_distance = min(
            (
                self._point_segment_distance(center, *part)
                for part in other_parts
            ),
            default=float("inf"),
        )
        line_hits = sum(
            self._segment_intersects_bounds(*part, bounds)
            for part in other_parts
        )
        return (
            bounds,
            center,
            start_distance,
            clearance,
            other_distance,
            line_hits,
        )
