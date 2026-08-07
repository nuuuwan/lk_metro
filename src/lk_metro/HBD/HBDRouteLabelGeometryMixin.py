import math

from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Bounds


class HBDRouteLabelGeometryMixin:
    @staticmethod
    def _point_segment_distance(
        point: Point,
        first: Point,
        second: Point,
    ) -> float:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        length_squared = x_delta**2 + y_delta**2
        if math.isclose(length_squared, 0.0):
            return math.dist(point, first)
        fraction = (
            (point[0] - first[0]) * x_delta + (point[1] - first[1]) * y_delta
        ) / length_squared
        fraction = min(1.0, max(0.0, fraction))
        projection = (
            first[0] + fraction * x_delta,
            first[1] + fraction * y_delta,
        )
        return math.dist(point, projection)

    @staticmethod
    def _segment_intersects_bounds(
        first: Point,
        second: Point,
        bounds: Bounds,
    ) -> bool:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        lower, upper = 0.0, 1.0
        constraints = (
            (-x_delta, first[0] - bounds[0]),
            (x_delta, bounds[2] - first[0]),
            (-y_delta, first[1] - bounds[1]),
            (y_delta, bounds[3] - first[1]),
        )
        for direction, distance in constraints:
            clipped = HBDRouteLabelGeometryMixin._clip_constraint(
                direction, distance, lower, upper
            )
            if clipped is None:
                return False
            lower, upper = clipped
        return True

    @staticmethod
    def _clip_constraint(
        direction: float,
        distance: float,
        lower: float,
        upper: float,
    ) -> tuple[float, float] | None:
        if math.isclose(direction, 0.0):
            return (lower, upper) if distance >= 0 else None
        fraction = distance / direction
        if direction < 0:
            lower = max(lower, fraction)
        else:
            upper = min(upper, fraction)
        return (lower, upper) if lower <= upper else None

    @staticmethod
    def _route_parts(
        segments: dict[str, list[list[Point]]],
        excluded_route_id: str,
    ) -> list[tuple[Point, Point]]:
        return [
            (first, second)
            for route_id, route_segments in segments.items()
            if route_id != excluded_route_id
            for path in route_segments
            for first, second in zip(path, path[1:])
            if first != second
        ]
