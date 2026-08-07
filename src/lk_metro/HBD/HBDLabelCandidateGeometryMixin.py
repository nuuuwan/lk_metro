import math

from lk_metro.GD.Point import Point


class HBDLabelCandidateGeometryMixin:
    def _label_edge_distances(
        self,
        stop_name: str,
        route_ids: set[str],
    ) -> tuple[float, ...]:
        if len(route_ids) == 1:
            distance = self.STATION_TICK_LENGTH
            if self._is_terminus(stop_name):
                distance /= 2
            return (distance,)
        base_distance = self.ROUTE_STROKE_WIDTH / 2 + self.LABEL_OFFSET
        return tuple(
            base_distance * scale
            for scale in (1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0, 9.0)
        )

    @staticmethod
    def _label_directions(
        normal: Point,
        prefer_positive: bool,
    ) -> tuple[Point, ...]:
        base_angle = math.atan2(normal[1], normal[0])
        preferred = (0.0, math.pi) if prefer_positive else (math.pi, 0.0)
        angle_offsets = preferred + tuple(
            index * math.pi / 64
            for index in range(128)
            if index not in (0, 64)
        )
        return tuple(
            (math.cos(base_angle + offset), math.sin(base_angle + offset))
            for offset in angle_offsets
        )

    @staticmethod
    def _label_radius(
        direction: Point,
        half_width: float,
        half_height: float,
    ) -> float:
        x_radius = (
            half_width / abs(direction[0]) if direction[0] else math.inf
        )
        y_radius = (
            half_height / abs(direction[1]) if direction[1] else math.inf
        )
        return min(x_radius, y_radius)
