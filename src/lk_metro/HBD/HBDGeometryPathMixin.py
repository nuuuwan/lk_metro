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
                path = self._three_segment_octilinear_path(
                    positions[ref_first], positions[ref_second]
                )
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

    @staticmethod
    def _three_segment_octilinear_path(
        first: Point,
        second: Point,
    ) -> list[Point]:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        x_distance, y_distance = abs(x_delta), abs(y_delta)
        if (
            math.isclose(x_delta, 0.0, abs_tol=1e-9)
            or math.isclose(y_delta, 0.0, abs_tol=1e-9)
            or math.isclose(x_distance, y_distance, abs_tol=1e-9)
        ):
            return [first, second]
        x_sign, y_sign = math.copysign(1, x_delta), math.copysign(1, y_delta)
        diagonal_vector = (x_sign, y_sign)
        if x_distance > y_distance:
            axis_vector = (x_sign, 0.0)
            axis_distance = x_distance - y_distance
            diagonal_distance = y_distance
        else:
            axis_vector = (0.0, y_sign)
            axis_distance = y_distance - x_distance
            diagonal_distance = x_distance
        if axis_distance >= diagonal_distance * math.sqrt(2):
            outer_vector, outer_distance = axis_vector, axis_distance
            middle_vector, middle_distance = (
                diagonal_vector,
                diagonal_distance,
            )
        else:
            outer_vector, outer_distance = (
                diagonal_vector,
                diagonal_distance,
            )
            middle_vector, middle_distance = axis_vector, axis_distance
        first_bend = (
            first[0] + outer_vector[0] * outer_distance / 2,
            first[1] + outer_vector[1] * outer_distance / 2,
        )
        second_bend = (
            first_bend[0] + middle_vector[0] * middle_distance,
            first_bend[1] + middle_vector[1] * middle_distance,
        )
        return [first, first_bend, second_bend, second]

    def _circle_route_segments(
        self,
        route_id: str,
        positions: dict[str, Point],
    ) -> list[list[Point]]:
        start_degrees, x_radius, y_radius, is_clockwise = (
            self._circle_routes[route_id]
        )
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
        sample_count = 8
        paths = []
        for index, segment in enumerate(segments):
            first, second = segment["stops"]
            path = [positions[first]]
            for sample in range(1, sample_count):
                angle = math.radians(
                    start_degrees
                    + direction
                    * (index + sample / sample_count)
                    * 360
                    / edge_count
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
