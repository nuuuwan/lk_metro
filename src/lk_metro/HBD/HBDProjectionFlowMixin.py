import math


class HBDProjectionFlowMixin:
    def _project_positions(
        self,
        origin_positions: dict[str, list[float]],
        design_routes: list[dict[str, object]],
    ) -> dict[str, list[float]]:
        projected = {
            name: point[:] for name, point in origin_positions.items()
        }
        position_routes = {name: set() for name in origin_positions}
        self._circle_centers: dict[str, list[float]] = {}
        for route in design_routes:
            route_id = route["id"]
            if route_id in self._circle_routes:
                start_degrees, x_radius, y_radius, is_clockwise = (
                    self._circle_routes[route_id]
                )
                self._project_circle_route(
                    route_id,
                    start_degrees,
                    x_radius,
                    y_radius,
                    is_clockwise,
                    route["segments"],
                    projected,
                    position_routes,
                )
                continue
            pending_segments = self._pending_segments([route])
            while pending_segments:
                remaining = self._project_available_segments(
                    pending_segments,
                    projected,
                    position_routes,
                )
                if len(remaining) == len(pending_segments):
                    self._add_fallback_origin(
                        remaining[0], projected, position_routes
                    )
                else:
                    pending_segments = remaining
        return projected

    def _project_circle_routes(
        self,
        design_routes: list[dict[str, object]],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        self._circle_centers: dict[str, list[float]] = {}
        routes_by_id = {route["id"]: route for route in design_routes}
        for route_id, circle in self._circle_routes.items():
            start_degrees, x_radius, y_radius, is_clockwise = circle
            segments = routes_by_id[route_id]["segments"]
            self._project_circle_route(
                route_id,
                start_degrees,
                x_radius,
                y_radius,
                is_clockwise,
                segments,
                projected,
                position_routes,
            )

    def _project_circle_route(
        self,
        route_id: str,
        start_degrees: float,
        x_radius: float,
        y_radius: float,
        is_clockwise: bool,
        segments: list[dict[str, object]],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        stops = [segments[0]["stops"][0]] + [
            segment["stops"][1] for segment in segments
        ]
        local_positions = self._circle_local_positions(
            start_degrees,
            x_radius,
            y_radius,
            is_clockwise,
            len(stops),
        )
        anchor_index = self._circle_anchor_index(
            stops, projected, position_routes
        )
        center = [
            projected[stops[anchor_index]][axis]
            - local_positions[anchor_index][axis]
            for axis in range(2)
        ]
        self._circle_centers[route_id] = center
        for stop, local_position in zip(stops, local_positions):
            expected = [
                center[axis] + local_position[axis] for axis in range(2)
            ]
            self._record_projected_stop(
                stop,
                expected,
                route_id,
                projected,
                position_routes,
            )

    @staticmethod
    def _circle_local_positions(
        start_degrees: float,
        x_radius: float,
        y_radius: float,
        is_clockwise: bool,
        stop_count: int,
    ) -> list[list[float]]:
        edge_count = stop_count - 1
        direction = -1 if is_clockwise else 1
        return [
            [
                x_radius * math.cos(math.radians(angle)),
                -y_radius * math.sin(math.radians(angle)),
            ]
            for index in range(stop_count)
            for angle in [start_degrees + direction * index * 360 / edge_count]
        ]

    @staticmethod
    def _circle_anchor_index(
        stops: list[str],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> int:
        anchor_index = next(
            (index for index, stop in enumerate(stops) if stop in projected),
            None,
        )
        if anchor_index is not None:
            return anchor_index
        projected[stops[0]] = [
            max(point[0] for point in projected.values()) + 2.0,
            min(point[1] for point in projected.values()),
        ]
        position_routes[stops[0]] = set()
        return 0

    def _pending_segments(
        self,
        design_routes: list[dict[str, object]],
    ) -> list[tuple[str, list[str], int, int]]:
        pending = []
        for route in design_routes:
            for segment in route["segments"]:
                if segment.get("circle"):
                    continue
                direction_index = self.DIRECTIONS.index(segment["direction"])
                x_delta, y_delta = self.DIRECTION_VECTORS[direction_index]
                pending.append(
                    (route["id"], segment["stops"], x_delta, y_delta)
                )
        return pending

    def _project_available_segments(
        self,
        pending_segments: list[tuple[str, list[str], int, int]],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> list[tuple[str, list[str], int, int]]:
        remaining_segments = []
        for segment in pending_segments:
            if not self._project_segment(segment, projected, position_routes):
                remaining_segments.append(segment)
        return remaining_segments

    def _project_segment(
        self,
        segment: tuple[str, list[str], int, int],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> bool:
        route_id, stops, x_delta, y_delta = segment
        anchor_index = next(
            (index for index, stop in enumerate(stops) if stop in projected),
            None,
        )
        if anchor_index is None:
            return False
        anchor_x, anchor_y = projected[stops[anchor_index]]
        for index, stop in enumerate(stops):
            step_count = index - anchor_index
            expected = [
                anchor_x + step_count * x_delta,
                anchor_y + step_count * y_delta,
            ]
            self._record_projected_stop(
                stop,
                expected,
                route_id,
                projected,
                position_routes,
            )
        return True
