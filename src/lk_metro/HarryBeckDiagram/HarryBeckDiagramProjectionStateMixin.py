import math

from utils_future import Log

log = Log("HarryBeckDiagram")


class HarryBeckDiagramProjectionStateMixin:
    def _record_projected_stop(
        self,
        stop: str,
        expected: list[float],
        route_id: str,
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        if stop not in projected:
            projected[stop] = expected
            position_routes[stop] = {route_id}
            return
        if all(
            math.isclose(actual, candidate)
            for actual, candidate in zip(projected[stop], expected)
        ):
            position_routes[stop].add(route_id)
            return
        retained_routes = "/".join(sorted(position_routes[stop]))
        retained_routes = retained_routes or "origin"
        log.warn(
            "Harry Beck position conflict: "
            f"{self._format_stop_at(stop, projected[stop])} "
            f"(route {retained_routes}) and "
            f"{self._format_stop_at(stop, expected)} (route {route_id})"
        )

    @staticmethod
    def _add_fallback_origin(
        segment: tuple[str, list[str], int, int],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        route_id, stops, _, _ = segment
        fallback_origin = stops[0]
        log.warn(
            "Harry Beck stops are not connected to an origin; "
            f"placing {fallback_origin!r} separately"
        )
        projected[fallback_origin] = [
            max(point[0] for point in projected.values()) + 2.0,
            min(point[1] for point in projected.values()),
        ]
        position_routes[fallback_origin] = {route_id}

    def _format_stop_at(self, stop_name: str, position: list[float]) -> str:
        x_coordinate, y_coordinate = position
        if stop_name.startswith("__blank__:"):
            _, route_id, blank_index = stop_name.split(":")
            return (
                f"[{x_coordinate:g}, {y_coordinate:g}]"
                f"<blank {route_id}.{blank_index}>"
            )
        numbers = "/".join(self._stop_numbers[stop_name])
        return f"[{x_coordinate:g}, {y_coordinate:g}]{stop_name} ({numbers})"

    def _grid_svg_lines(self) -> list[str]:
        return []
