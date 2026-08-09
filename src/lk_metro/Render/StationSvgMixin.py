from lk_metro.GD.Point import Point


class StationSvgMixin:
    def _stop_marker_svg_lines(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
    ) -> list[str]:
        lines = []
        route_colors = {route.id: route.color for route in self.routes}
        for stop in self.stops:
            lines.extend(
                self._single_stop_marker_svg_lines(
                    stop.name,
                    positions,
                    memberships,
                    route_colors,
                )
            )
        return lines

    def _single_stop_marker_svg_lines(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
    ) -> list[str]:
        x_coordinate, y_coordinate = positions[stop_name]
        return [
            self._station_marker_svg_line(
                stop_name,
                (x_coordinate, y_coordinate),
                memberships,
                route_colors,
            )
        ]

    def _stop_label_svg_lines(
        self,
        positions: dict[str, Point],
    ) -> list[str]:
        lines = []
        for stop in self.stops:
            x_coordinate, y_coordinate = positions[stop.name]
            label_x, label_y, text_anchor = self._stop_label_placement(
                stop.name,
                (x_coordinate, y_coordinate),
            )
            lines.append(
                self._label_svg_line(
                    stop.name,
                    label_x,
                    label_y,
                    text_anchor,
                )
            )
        return lines

    def _station_marker_svg_line(
        self,
        stop_name: str,
        position: Point,
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
    ) -> str:
        route_id = min(
            memberships[stop_name], key=self._route_order.__getitem__
        )
        return (
            f'<circle class="station" cx="{position[0]}" cy="{position[1]}" '
            f'r="{self.STATION_RADIUS}" '
            f'stroke="{route_colors[route_id]}"/>'
        )
