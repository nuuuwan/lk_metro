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
        circle_paths_by_edge = self._circle_paths_by_edge(paths_by_route)
        return {
            route.id: self._follow_circle_paths(
                route.id,
                paths_by_route[route.id],
                circle_paths_by_edge,
            )
            for route in self.routes
        }

    def _circle_paths_by_edge(
        self,
        paths_by_route: dict[str, list[list[Point]]],
    ) -> dict[tuple[str, str], list[Point]]:
        circle_paths = {}
        for route_id in self._circle_routes:
            for segment, path in zip(
                self._segments_by_route[route_id],
                paths_by_route[route_id],
            ):
                first, second = segment["stops"]
                edge = self._edge_key(first, second)
                circle_paths[edge] = (
                    path
                    if (first, second) == self._edge_directions[edge]
                    else list(reversed(path))
                )
        return circle_paths

    def _follow_circle_paths(
        self,
        route_id: str,
        paths: list[list[Point]],
        circle_paths_by_edge: dict[tuple[str, str], list[Point]],
    ) -> list[list[Point]]:
        if route_id in self._circle_routes:
            return paths
        return [
            self._circle_path_for_segment(segment, path, circle_paths_by_edge)
            for segment, path in zip(self._segments_by_route[route_id], paths)
        ]

    def _circle_path_for_segment(
        self,
        segment: dict[str, object],
        path: list[Point],
        circle_paths_by_edge: dict[tuple[str, str], list[Point]],
    ) -> list[Point]:
        first, second = segment["stops"]
        edge = self._edge_key(first, second)
        circle_path = circle_paths_by_edge.get(edge)
        if circle_path is None:
            return path
        return (
            circle_path[:]
            if (first, second) == self._edge_directions[edge]
            else list(reversed(circle_path))
        )

    def _linear_route_segments(
        self,
        route_id: str,
        positions: dict[str, Point],
    ) -> list[list[Point]]:
        paths = []
        edges = []
        for segment in self._segments_by_route[route_id]:
            stops = segment["stops"]
            for first, second in zip(stops, stops[1:]):
                edge = self._edge_key(first, second)
                ref_first, ref_second = self._edge_directions[edge]
                is_ref = first == ref_first and second == ref_second
                path = [positions[ref_first], positions[ref_second]]
                paths.append(path if is_ref else list(reversed(path)))
                edges.append(edge)
        return self._join_linear_route_paths(paths, edges)

    def _join_linear_route_paths(
        self,
        paths: list[list[Point]],
        edges: list[tuple[str, str]],
    ) -> list[list[Point]]:
        for index, (first, second) in enumerate(zip(paths, paths[1:])):
            if first[-1] == second[0]:
                continue
            first_shared = len(self._edge_routes[edges[index]]) > 1
            second_shared = len(self._edge_routes[edges[index + 1]]) > 1
            self._join_linear_route_pair(
                first, second, first_shared, second_shared
            )
        return paths

    def _join_linear_route_pair(
        self,
        first: list[Point],
        second: list[Point],
        first_shared: bool,
        second_shared: bool,
    ) -> None:
        if first_shared and not second_shared:
            second[0] = first[-1]
            return
        if second_shared and not first_shared:
            first[-1] = second[0]
            return
        intersection = self._line_intersection(
            first[-2], first[-1], second[0], second[1]
        )
        if intersection is None:
            second[0] = first[-1]
            return
        first[-1] = intersection
        second[0] = intersection

    @staticmethod
    def _line_intersection(
        first_start: Point,
        first_end: Point,
        second_start: Point,
        second_end: Point,
    ) -> Point | None:
        first_delta = (
            first_end[0] - first_start[0],
            first_end[1] - first_start[1],
        )
        second_delta = (
            second_end[0] - second_start[0],
            second_end[1] - second_start[1],
        )
        denominator = (
            first_delta[0] * second_delta[1] - first_delta[1] * second_delta[0]
        )
        if math.isclose(denominator, 0.0, abs_tol=1e-9):
            return None
        start_delta = (
            second_start[0] - first_start[0],
            second_start[1] - first_start[1],
        )
        fraction = (
            start_delta[0] * second_delta[1] - start_delta[1] * second_delta[0]
        ) / denominator
        return (
            first_start[0] + fraction * first_delta[0],
            first_start[1] + fraction * first_delta[1],
        )

    def _edge_vector(
        self,
        edge: tuple[str, str],
        positions: dict[str, Point],
    ) -> Point:
        first, second = self._edge_directions[edge]
        return (
            positions[second][0] - positions[first][0],
            positions[second][1] - positions[first][1],
        )

    def _edge_normal(
        self,
        edge: tuple[str, str],
        positions: dict[str, Point],
    ) -> Point:
        vector = self._edge_vector(edge, positions)
        length = math.hypot(*vector)
        return (-vector[1] / length, vector[0] / length)

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
