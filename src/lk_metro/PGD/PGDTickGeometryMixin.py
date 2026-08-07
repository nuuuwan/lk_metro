import math

from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Tick


class PGDTickGeometryMixin:
    def _tick_endpoints(
        self,
        first: Point,
        second: Point,
        position: Point,
        is_terminus: bool,
    ) -> Tick:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        length = math.hypot(x_delta, y_delta)
        x_normal = -y_delta / length
        y_normal = x_delta / length
        x_offset = x_normal * self.STATION_TICK_LENGTH
        y_offset = y_normal * self.STATION_TICK_LENGTH
        if x_offset - y_offset < 0:
            x_normal, y_normal = -x_normal, -y_normal
            x_offset, y_offset = -x_offset, -y_offset
        x_coordinate, y_coordinate = position
        outer = (
            x_coordinate + x_normal * self.ROUTE_STROKE_WIDTH / 2 + x_offset,
            y_coordinate + y_normal * self.ROUTE_STROKE_WIDTH / 2 + y_offset,
        )
        if is_terminus:
            return (
                2 * x_coordinate - outer[0],
                2 * y_coordinate - outer[1],
            ), outer
        return (x_coordinate, y_coordinate), outer

    @staticmethod
    def _tick_candidate_segments(
        route_segments: list[list[Point]],
        stop_index: int,
    ) -> list[tuple[Point, Point]]:
        candidates = []
        for path in route_segments[stop_index:]:
            candidates.extend(zip(path, path[1:]))
        for path in reversed(route_segments[:stop_index]):
            candidates.extend(zip(reversed(path), reversed(path[:-1])))
        return candidates
