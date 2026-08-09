import math

from utils_future import Log

from lk_metro.GD.Point import Point

log = Log("HBD")


class HBDLayoutProjectionMixin:
    def layout(self) -> dict[str, Point]:
        projected = self._project_positions(
            self._origin_positions,
            [
                {
                    "id": route.id,
                    "name": route.name,
                    "segments": self._segments_by_route[route.id],
                }
                for route in self.routes
            ],
        )
        self._logical_positions = projected
        self._validate_projected_geometry(projected)
        min_x, max_x, min_y, max_y = self._layout_bounds(projected)
        self._grid_min_x = min_x
        self._grid_min_y = min_y
        self.width = math.ceil(
            (max_x - min_x) * self.UNIT_SCALE + self.padding * 2
        )
        self.height = math.ceil(
            (max_y - min_y) * self.UNIT_SCALE + self.padding * 2
        )
        return {
            name: (
                (point[0] - min_x) * self.UNIT_SCALE + self.padding,
                (point[1] - min_y) * self.UNIT_SCALE + self.padding,
            )
            for name, point in projected.items()
        }

    def _layout_bounds(
        self,
        projected: dict[str, list[float]],
    ) -> tuple[float, float, float, float]:
        circle_extents = [
            (
                center[0] - self._circle_routes[route_id][1],
                center[0] + self._circle_routes[route_id][1],
                center[1] - self._circle_routes[route_id][2],
                center[1] + self._circle_routes[route_id][2],
            )
            for route_id, center in self._circle_centers.items()
        ]
        min_x = min(
            [point[0] for point in projected.values()]
            + [extent[0] for extent in circle_extents]
        )
        max_x = max(
            [point[0] for point in projected.values()]
            + [extent[1] for extent in circle_extents]
        )
        min_y = min(
            [point[1] for point in projected.values()]
            + [extent[2] for extent in circle_extents]
        )
        max_y = max(
            [point[1] for point in projected.values()]
            + [extent[3] for extent in circle_extents]
        )
        return min_x, max_x, min_y, max_y

    def _validate_projected_geometry(
        self,
        positions: dict[str, list[float]],
    ) -> None:
        edges, errors = self._edge_geometry_errors(positions)
        errors.extend(self._overlap_errors(positions))
        errors.extend(self._crossing_errors(positions, edges))
        for warning_type, stop_names, description in errors:
            names = ", ".join(stop_names)
            log.warning(f"[{warning_type}][{names}] {description}")

    def _edge_geometry_error(
        self,
        route_id: str,
        first: str,
        second: str,
        x_delta: float,
        y_delta: float,
        positions: dict[str, list[float]],
    ) -> tuple[str, tuple[str, ...], str]:
        if math.isclose(x_delta, 0.0) and math.isclose(y_delta, 0.0):
            message = "has zero length (angle undefined)"
        else:
            angle = math.degrees(math.atan2(y_delta, x_delta)) % 360
            message = (
                "is not a multiple of 45 degrees " f"(angle: {angle:.3f} deg)"
            )
        first_label = self._format_stop_at(first, positions[first])
        second_label = self._format_stop_at(second, positions[second])
        return (
            "line angle",
            (first, second),
            f"route {route_id} edge {first_label} to {second_label} {message}",
        )
