import math
from collections import Counter
from functools import cmp_to_key

from lk_metro.GD.Point import Point


class HBDGeometryPathMixin:
    def route_segments(
        self,
        positions: dict[str, Point] | None = None,
    ) -> dict[str, list[list[Point]]]:
        positions = positions or self.layout()
        self._parallel_lane_offsets = self._build_parallel_lane_offsets(
            positions
        )
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
        edges = []
        for segment in self._segments_by_route[route_id]:
            stops = segment["stops"]
            for first, second in zip(stops, stops[1:]):
                edge = self._edge_key(first, second)
                ref_first, ref_second = self._edge_directions[edge]
                is_ref = first == ref_first and second == ref_second
                path = [positions[ref_first], positions[ref_second]]
                if len(self._edge_routes[edge]) > 1:
                    offset_index = self._parallel_lane_offsets[edge][route_id]
                    path = self._offset_path(
                        path, offset_index * self.parallel_route_gap
                    )
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

    def _build_parallel_lane_offsets(
        self,
        positions: dict[str, Point],
    ) -> dict[tuple[str, str], dict[str, int]]:
        remaining = {
            edge
            for edge, route_ids in self._edge_routes.items()
            if len(route_ids) > 1
        }
        offsets = {}
        while remaining:
            component = self._parallel_corridor_component(
                remaining.pop(), remaining, positions
            )
            anchor = max(
                component, key=lambda edge: len(self._edge_routes[edge])
            )
            route_order = self._parallel_route_ids(anchor, positions)
            anchor_normal = self._edge_normal(anchor, positions)
            for edge in component:
                normal = self._edge_normal(edge, positions)
                orientation = (
                    1 if self._dot(anchor_normal, normal) >= 0 else -1
                )
                offsets[edge] = {
                    route_id: orientation * route_order.index(route_id)
                    for route_id in self._edge_routes[edge]
                }
        return offsets

    def _parallel_corridor_component(
        self,
        first: tuple[str, str],
        remaining: set[tuple[str, str]],
        positions: dict[str, Point],
    ) -> list[tuple[str, str]]:
        component = []
        pending = [first]
        while pending:
            edge = pending.pop()
            component.append(edge)
            neighbors = {
                candidate
                for candidate in remaining
                if self._edges_continue_straight(edge, candidate, positions)
            }
            remaining.difference_update(neighbors)
            pending.extend(neighbors)
        return component

    def _edges_continue_straight(
        self,
        first: tuple[str, str],
        second: tuple[str, str],
        positions: dict[str, Point],
    ) -> bool:
        if not set(first) & set(second):
            return False
        first_vector = self._edge_vector(first, positions)
        second_vector = self._edge_vector(second, positions)
        return math.isclose(
            first_vector[0] * second_vector[1]
            - first_vector[1] * second_vector[0],
            0.0,
            abs_tol=1e-9,
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

    @staticmethod
    def _dot(first: Point, second: Point) -> float:
        return first[0] * second[0] + first[1] * second[1]

    def _parallel_route_ids(
        self,
        edge: tuple[str, str],
        positions: dict[str, Point],
    ) -> list[str]:
        def compare(first: str, second: str) -> int:
            return self._compare_parallel_routes(
                first, second, edge, positions
            )

        return sorted(self._edge_routes[edge], key=cmp_to_key(compare))

    def _compare_parallel_routes(
        self,
        first: str,
        second: str,
        edge: tuple[str, str],
        positions: dict[str, Point],
    ) -> int:
        score = self._parallel_pair_side_score(first, second, edge, positions)
        if math.isclose(score, 0.0, abs_tol=1e-9):
            return self._route_order[first] - self._route_order[second]
        return -1 if score < 0 else 1

    def _parallel_pair_side_score(
        self,
        first_route: str,
        second_route: str,
        edge: tuple[str, str],
        positions: dict[str, Point],
    ) -> float:
        shared_edges = {
            candidate
            for candidate, route_ids in self._edge_routes.items()
            if first_route in route_ids and second_route in route_ids
        }
        degree = Counter(stop for shared in shared_edges for stop in shared)
        endpoints = [stop for stop, count in degree.items() if count == 1]
        ref_first, ref_second = self._edge_directions[edge]
        normal = self._path_normals(
            [positions[ref_first], positions[ref_second]]
        )[0]
        return sum(
            self._parallel_branch_offset(
                first_route, endpoint, shared_edges, normal, positions
            )
            - self._parallel_branch_offset(
                second_route, endpoint, shared_edges, normal, positions
            )
            for endpoint in endpoints
        )

    def _parallel_branch_offset(
        self,
        route_id: str,
        endpoint: str,
        shared_edges: set[tuple[str, str]],
        normal: Point,
        positions: dict[str, Point],
    ) -> float:
        segments = self._segments_by_route[route_id]
        route_stops = [segments[0]["stops"][0]] + [
            segment["stops"][1] for segment in segments
        ]
        for neighbor in self._route_neighbors(route_stops, endpoint):
            if self._edge_key(endpoint, neighbor) in shared_edges:
                continue
            return sum(
                (positions[neighbor][axis] - positions[endpoint][axis])
                * normal[axis]
                for axis in range(2)
            )
        return 0.0

    @staticmethod
    def _route_neighbors(route_stops: list[str], stop: str) -> list[str]:
        return [
            route_stops[neighbor_index]
            for index, candidate in enumerate(route_stops)
            if candidate == stop
            for neighbor_index in (index - 1, index + 1)
            if 0 <= neighbor_index < len(route_stops)
        ]

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
