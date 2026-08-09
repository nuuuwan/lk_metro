import math

from utils_future import Log

log = Log("HBD")


class HBDProjectionStateMixin:
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
            math.isclose(actual, candidate, abs_tol=1e-9)
            for actual, candidate in zip(projected[stop], expected)
        ):
            position_routes[stop].add(route_id)
            return
        position_routes[stop].add(route_id)

    @staticmethod
    def _add_fallback_origin(
        segment: tuple[str, list[str], int, int],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> None:
        route_id, stops, _, _ = segment
        fallback_origin = stops[0]
        log.warning(
            f"[disconnected stop][{fallback_origin}] "
            "not connected to an origin; placing it separately"
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
        x_coordinates = range(
            self.padding,
            self.width - self.padding + 1,
            round(self.UNIT_SCALE),
        )
        y_coordinates = range(
            self.padding,
            self.height - self.padding + 1,
            round(self.UNIT_SCALE),
        )
        return [
            '<g class="coordinate-grid" stroke="#ccc" '
            'stroke-opacity="0.1" stroke-width="0.25">',
            *(
                f'<line x1="{x}" y1="{self.padding}" x2="{x}" '
                f'y2="{self.height - self.padding}"/>'
                for x in x_coordinates
            ),
            *(
                f'<line x1="{self.padding}" y1="{y}" '
                f'x2="{self.width - self.padding}" y2="{y}"/>'
                for y in y_coordinates
            ),
            "</g>",
        ]
