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
        min_x = min(point[0] for point in projected.values())
        max_x = max(point[0] for point in projected.values())
        min_y = min(point[1] for point in projected.values())
        max_y = max(point[1] for point in projected.values())
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

    def _validate_projected_geometry(
        self,
        positions: dict[str, list[float]],
    ) -> None:
        edges, errors = self._edge_geometry_errors(positions)
        errors.extend(self._overlap_errors(positions))
        errors.extend(self._crossing_errors(positions, edges))
        for error in errors:
            log.warn(f"Harry Beck geometry: {error}")

    def _edge_geometry_error(
        self,
        route_id: str,
        first: str,
        second: str,
        x_delta: float,
        y_delta: float,
        positions: dict[str, list[float]],
    ) -> str:
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
            f"route {route_id} edge {first_label} to {second_label} {message}"
        )
