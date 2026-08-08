import math

from lk_metro.GD.Point import Point


class HBDGeometryPathMixin:
    def route_segments(
        self,
        positions: dict[str, Point] | None = None,
    ) -> dict[str, list[list[Point]]]:
        positions = positions or self.layout()
        paths_by_route = {}
        for route in self.routes:
            if route.id in self._circle_routes:
                paths = self._circle_route_segments(route.id, positions)
            else:
                paths = self._linear_route_segments(route.id, positions)
            paths_by_route[route.id] = paths
        return paths_by_route

    def _linear_route_segments(
        self,
        route_id: str,
        positions: dict[str, Point],
    ) -> list[list[Point]]:
        paths = []
        for segment in self._segments_by_route[route_id]:
            stops = segment["stops"]
            for first, second in zip(stops, stops[1:]):
                edge = self._edge_key(first, second)
                ref_first, ref_second = self._edge_directions[edge]
                is_ref = first == ref_first and second == ref_second
                path = [positions[ref_first], positions[ref_second]]
                route_ids = sorted(
                    self._edge_routes[edge], key=self._route_order.get
                )
                if len(route_ids) > 1:
                    offset_index = (
                        route_ids.index(route_id) - (len(route_ids) - 1) / 2
                    )
                    path = self._offset_path(
                        path, offset_index * self.parallel_route_gap
                    )
                paths.append(path if is_ref else list(reversed(path)))
        return paths

    def _circle_route_segments(
        self,
        route_id: str,
        positions: dict[str, Point],
    ) -> list[list[Point]]:
        start_degrees, x_radius, y_radius, is_clockwise = self._circle_routes[
            route_id
        ]
        direction = -1 if is_clockwise else 1
        x_radius *= self.UNIT_SCALE
        y_radius *= self.UNIT_SCALE
        logical_center = self._circle_centers[route_id]
        center = (
            (logical_center[0] - self._grid_min_x) * self.UNIT_SCALE
            + self.padding,
            (logical_center[1] - self._grid_min_y) * self.UNIT_SCALE
            + self.padding,
        )
        segments = self._segments_by_route[route_id]
        edge_count = len(segments)
        route_angles = self._circle_route_angles.get(route_id)
        sample_count = 8
        paths = []
        for index, segment in enumerate(segments):
            first, second = segment["stops"]
            path = [positions[first]]
            for sample in range(1, sample_count):
                angle = self._circle_sample_angle(
                    start_degrees,
                    direction,
                    edge_count,
                    index,
                    sample / sample_count,
                    route_angles,
                )
                path.append(
                    (
                        center[0] + x_radius * math.cos(angle),
                        center[1] - y_radius * math.sin(angle),
                    )
                )
            path.append(positions[second])
            paths.append(path)
        return paths

    @staticmethod
    def _circle_sample_angle(
        start_degrees: float,
        direction: int,
        edge_count: int,
        index: int,
        fraction: float,
        route_angles: list[float] | None,
    ) -> float:
        if route_angles is None:
            return math.radians(
                start_degrees
                + direction * (index + fraction) * 360 / edge_count
            )
        start = route_angles[index]
        end = route_angles[(index + 1) % edge_count]
        delta = (end - start) % (2 * math.pi)
        if direction < 0:
            delta = -((start - end) % (2 * math.pi))
        return start + delta * fraction
