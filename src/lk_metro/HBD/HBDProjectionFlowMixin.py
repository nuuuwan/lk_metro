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
        self._circle_route_angles: dict[str, list[float]] = {}
        for route in design_routes:
            route_id = route["id"]
            if (
                route_id in self._circle_routes
                and route_id not in self._fitted_circle_routes
            ):
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
            self._project_linear_route(route, projected, position_routes)
        if self._fitted_circle_routes:
            projected = self._fit_and_reflow_circle_routes(
                origin_positions, design_routes, projected
            )
        return projected

    def _fit_and_reflow_circle_routes(
        self,
        origin_positions: dict[str, list[float]],
        design_routes: list[dict[str, object]],
        projected: dict[str, list[float]],
    ) -> dict[str, list[float]]:
        routes_by_id = {route["id"]: route for route in design_routes}
        fitted_positions = self._fit_circle_routes(routes_by_id, projected)
        reflowed = self._reflow_around_circles(
            origin_positions, design_routes, fitted_positions
        )
        circle_stops = {
            stop
            for route_id in self._circle_routes
            for segment in routes_by_id[route_id]["segments"]
            for stop in segment["stops"]
        }
        return self._snap_non_circle_positions(reflowed, circle_stops)

    @staticmethod
    def _snap_non_circle_positions(
        positions: dict[str, list[float]],
        circle_stops: set[str],
    ) -> dict[str, list[float]]:
        return {
            stop: (
                point
                if stop in circle_stops
                else [round(point[0]), round(point[1])]
            )
            for stop, point in positions.items()
        }

    def _fit_circle_routes(
        self,
        routes_by_id: dict[str, dict[str, object]],
        projected: dict[str, list[float]],
    ) -> dict[str, list[float]]:
        fitted_positions = {}
        for route_id in self._fitted_circle_routes:
            segments = routes_by_id[route_id]["segments"]
            stops = [segment["stops"][0] for segment in segments]
            center, circle, positions, angles = self._fit_circle_positions(
                [projected[stop] for stop in stops],
                self._fitted_circle_routes[route_id],
            )
            self._circle_centers[route_id] = center
            self._circle_routes[route_id] = circle
            self._circle_route_angles[route_id] = angles
            fitted_positions.update(zip(stops, positions))
        return fitted_positions

    def _reflow_around_circles(
        self,
        origin_positions: dict[str, list[float]],
        design_routes: list[dict[str, object]],
        fitted_positions: dict[str, list[float]],
    ) -> dict[str, list[float]]:
        routes_by_id = {route["id"]: route for route in design_routes}
        reflowed = {name: point[:] for name, point in origin_positions.items()}
        reflowed.update(fitted_positions)
        position_routes = {name: set() for name in reflowed}
        for route_id in self._fitted_circle_routes:
            route = routes_by_id[route_id]
            for segment in route["segments"]:
                for stop in segment["stops"]:
                    position_routes[stop].add(route_id)
        for route in design_routes:
            self._reflow_route(route, reflowed, position_routes)
        return reflowed

    def _reflow_route(
        self,
        route: dict[str, object],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        route_id = route["id"]
        if route_id in self._fitted_circle_routes:
            return
        if route_id not in self._circle_routes:
            self._project_linear_route(route, projected, position_routes)
            return
        start, x_radius, y_radius, clockwise = self._circle_routes[route_id]
        self._project_circle_route(
            route_id,
            start,
            x_radius,
            y_radius,
            clockwise,
            route["segments"],
            projected,
            position_routes,
        )

    @classmethod
    def _fit_circle_positions(
        cls,
        points: list[list[float]],
        radii: tuple[float, float] | None = None,
    ) -> tuple[
        list[float],
        tuple[float, float, float, bool],
        list[list[float]],
        list[float],
    ]:
        center = [
            sum(point[axis] for point in points) / len(points)
            for axis in range(2)
        ]
        if radii is not None:
            return cls._nearest_ellipse_positions(points, center, radii)
        candidates = [
            cls._fit_circle_direction(points, center, direction)
            for direction in (1, -1)
        ]
        _, start, x_radius, y_radius, direction, positions = min(candidates)
        circle = (
            math.degrees(start) % 360,
            x_radius,
            y_radius,
            direction < 0,
        )
        angles = [
            start + direction * index * 2 * math.pi / len(points)
            for index in range(len(points))
        ]
        return center, circle, positions, angles

    @classmethod
    def _nearest_ellipse_positions(
        cls,
        points: list[list[float]],
        center: list[float],
        radii: tuple[float, float],
    ) -> tuple[
        list[float],
        tuple[float, float, float, bool],
        list[list[float]],
        list[float],
    ]:
        x_radius, y_radius = radii
        angles = [
            cls._nearest_ellipse_angle(point, center, radii)
            for point in points
        ]
        angles = cls._spread_close_ellipse_angles(angles)
        positions = [
            [
                center[0] + x_radius * math.cos(angle),
                center[1] - y_radius * math.sin(angle),
            ]
            for angle in angles
        ]
        direction = sum(
            cls._wrapped_angle(second - first)
            for first, second in zip(angles, angles[1:] + angles[:1])
        )
        circle = (
            math.degrees(angles[0]) % 360,
            x_radius,
            y_radius,
            direction < 0,
        )
        return center, circle, positions, angles

    @classmethod
    def _spread_close_ellipse_angles(
        cls,
        angles: list[float],
    ) -> list[float]:
        minimum_gap = math.radians(cls.CIRCLE_MIN_STOP_GAP_DEGREES)
        spread_angles = angles[:]
        for index, first in enumerate(angles):
            next_index = (index + 1) % len(angles)
            delta = cls._wrapped_angle(angles[next_index] - first)
            if abs(delta) >= minimum_gap:
                continue
            direction = 1 if delta >= 0 else -1
            adjustment = (minimum_gap - abs(delta)) / 2
            spread_angles[index] -= direction * adjustment
            spread_angles[next_index] += direction * adjustment
        return spread_angles

    @classmethod
    def _nearest_ellipse_angle(
        cls,
        point: list[float],
        center: list[float],
        radii: tuple[float, float],
    ) -> float:
        sample_count = 256
        angles = [
            index * 2 * math.pi / sample_count for index in range(sample_count)
        ]
        best_index = min(
            range(sample_count),
            key=lambda index: cls._ellipse_distance_squared(
                point, center, radii, angles[index]
            ),
        )
        step = 2 * math.pi / sample_count
        lower = angles[best_index] - step
        upper = angles[best_index] + step
        for _ in range(40):
            first = lower + (upper - lower) / 3
            second = upper - (upper - lower) / 3
            first_distance = cls._ellipse_distance_squared(
                point, center, radii, first
            )
            second_distance = cls._ellipse_distance_squared(
                point, center, radii, second
            )
            if first_distance < second_distance:
                upper = second
            else:
                lower = first
        return (lower + upper) / 2 % (2 * math.pi)

    @staticmethod
    def _ellipse_distance_squared(
        point: list[float],
        center: list[float],
        radii: tuple[float, float],
        angle: float,
    ) -> float:
        x_radius, y_radius = radii
        x_delta = center[0] + x_radius * math.cos(angle) - point[0]
        y_delta = center[1] - y_radius * math.sin(angle) - point[1]
        return x_delta**2 + y_delta**2

    @staticmethod
    def _wrapped_angle(angle: float) -> float:
        return (angle + math.pi) % (2 * math.pi) - math.pi

    @staticmethod
    def _fit_circle_direction(
        points: list[list[float]],
        center: list[float],
        direction: int,
    ) -> tuple[float, float, float, float, int, list[list[float]]]:
        count = len(points)
        correlation = (
            sum(
                complex(point[0] - center[0], center[1] - point[1])
                * complex(
                    math.cos(-direction * index * 2 * math.pi / count),
                    math.sin(-direction * index * 2 * math.pi / count),
                )
                for index, point in enumerate(points)
            )
            / count
        )
        start = math.atan2(correlation.imag, correlation.real)
        x_radius = y_radius = abs(correlation)
        positions = [
            [
                center[0] + x_radius * math.cos(angle),
                center[1] - y_radius * math.sin(angle),
            ]
            for index in range(count)
            for angle in [start + direction * index * 2 * math.pi / count]
        ]
        error = sum(
            math.dist(point, fitted) ** 2
            for point, fitted in zip(points, positions)
        )
        return error, start, x_radius, y_radius, direction, positions

    def _project_linear_route(
        self,
        route: dict[str, object],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        route_id = route["id"]
        segments = route["segments"]
        stops = [segments[0]["stops"][0]] + [
            segment["stops"][1] for segment in segments
        ]
        deltas = [
            self.DIRECTION_VECTORS[self.DIRECTIONS.index(segment["direction"])]
            for segment in segments
        ]
        anchor_index = next(
            (index for index, stop in enumerate(stops) if stop in projected),
            None,
        )
        if anchor_index is None:
            anchor_index = 0
            self._add_fallback_origin(
                (route_id, stops[:2], *deltas[0]),
                projected,
                position_routes,
            )
        position_routes[stops[anchor_index]].add(route_id)
        self._project_route_direction(
            route_id,
            stops,
            deltas,
            range(anchor_index, len(deltas)),
            1,
            projected,
            position_routes,
        )
        self._project_route_direction(
            route_id,
            stops,
            deltas,
            range(anchor_index - 1, -1, -1),
            -1,
            projected,
            position_routes,
        )

    def _project_route_direction(
        self,
        route_id: str,
        stops: list[str],
        deltas: list[tuple[int, int]],
        edge_indices: range,
        step: int,
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        for edge_index in edge_indices:
            source_index = edge_index if step > 0 else edge_index + 1
            target_index = source_index + step
            source = stops[source_index]
            target = stops[target_index]
            x_delta, y_delta = deltas[edge_index]
            expected = [
                projected[source][0] + step * x_delta,
                projected[source][1] + step * y_delta,
            ]
            self._record_projected_stop(
                target,
                expected,
                route_id,
                projected,
                position_routes,
            )

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
