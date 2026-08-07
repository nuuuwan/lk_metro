import math

from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDRouteLabelGeometryMixin import HBDRouteLabelGeometryMixin
from lk_metro.PGD.PGDTypes import Bounds

RouteLabelOption = tuple[Bounds, Point, float, float, int]


class HBDRouteLabelCandidatesMixin(HBDRouteLabelGeometryMixin):
    def _route_label_options(
        self,
        route_id: str,
        segments: dict[str, list[list[Point]]],
    ) -> list[RouteLabelOption]:
        half_width = len(route_id) * self.ROUTE_NAME_FONT_SIZE * 0.3
        half_height = self.ROUTE_NAME_FONT_SIZE * 0.6
        other_parts = self._route_parts(segments, route_id)
        options = []
        for path in segments[route_id]:
            for first, second in zip(path, path[1:]):
                if first == second:
                    continue
                options.extend(
                    self._route_part_label_options(
                        first,
                        second,
                        half_width,
                        half_height,
                        other_parts,
                    )
                )
        return options

    def _route_part_label_options(
        self,
        first: Point,
        second: Point,
        half_width: float,
        half_height: float,
        other_parts: list[tuple[Point, Point]],
    ) -> list[RouteLabelOption]:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        length = math.hypot(x_delta, y_delta)
        normal = (-y_delta / length, x_delta / length)
        clearance = (
            abs(normal[0]) * half_width
            + abs(normal[1]) * half_height
            + self.ROUTE_STROKE_WIDTH / 2
            + 0.2
        )
        options = []
        for fraction in (0.15, 0.3, 0.5, 0.7, 0.85):
            point = (
                first[0] + fraction * x_delta,
                first[1] + fraction * y_delta,
            )
            for side in (-1.0, 1.0):
                center = (
                    point[0] + normal[0] * clearance * side,
                    point[1] + normal[1] * clearance * side,
                )
                options.append(
                    self._route_label_option(
                        center,
                        half_width,
                        half_height,
                        clearance,
                        other_parts,
                    )
                )
        return options

    def _route_label_option(
        self,
        center: Point,
        half_width: float,
        half_height: float,
        clearance: float,
        other_parts: list[tuple[Point, Point]],
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
        return bounds, center, clearance, other_distance, line_hits
