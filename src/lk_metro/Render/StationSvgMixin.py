from lk_metro.GD.Point import Point


class StationSvgMixin:
    def _stop_svg_lines(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
    ) -> list[str]:
        lines = []
        route_colors = {route.id: route.color for route in self.routes}
        for stop in self.stops:
            lines.extend(
                self._single_stop_svg_lines(
                    stop.name,
                    positions,
                    memberships,
                    route_colors,
                )
            )
        return lines

    def _single_stop_svg_lines(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
    ) -> list[str]:
        x_coordinate, y_coordinate = positions[stop_name]
        if len(memberships[stop_name]) > 1:
            marker = (
                f'<circle class="interchange" cx="{x_coordinate}" '
                f'cy="{y_coordinate}" r="{self.INTERCHANGE_RADIUS}"/>'
            )
        else:
            marker = self._station_marker_svg_line(
                stop_name,
                (x_coordinate, y_coordinate),
                memberships,
                route_colors,
            )
        label_x, label_y, text_anchor = self._stop_label_placement(
            stop_name,
            (x_coordinate, y_coordinate),
        )
        label = self._label_svg_line(
            stop_name,
            label_x,
            label_y,
            text_anchor,
        )
        return [marker, label]

    def _station_marker_svg_line(
        self,
        stop_name: str,
        position: Point,
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
    ) -> str:
        route_id = next(iter(memberships[stop_name]))
        return (
            f'<circle class="station" cx="{position[0]}" cy="{position[1]}" '
            f'r="{self.STATION_RADIUS}" '
            f'stroke="{route_colors[route_id]}"/>'
        )
