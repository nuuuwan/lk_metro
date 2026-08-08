import html


class GDStopsMixin:
    def _stop_svg_lines(
        self,
        positions: dict[str, tuple[float, float]],
    ) -> list[str]:
        lines = []
        routes_to_draw = self.routes
        visible_stop_names = {
            stop_name for route in routes_to_draw for stop_name in route.stops
        }
        memberships = self._route_memberships(routes_to_draw)
        route_colors = {route.id: route.color for route in routes_to_draw}
        for stop in self.stops:
            if stop.name not in visible_stop_names:
                continue
            x_coordinate, y_coordinate = positions[stop.name]
            if len(memberships[stop.name]) > 1:
                lines.append(
                    f'<circle class="interchange" cx="{x_coordinate}" '
                    f'cy="{y_coordinate}" '
                    f'r="{self.INTERCHANGE_RADIUS}"/>'
                )
            else:
                route_id = next(iter(memberships[stop.name]))
                lines.append(
                    f'<circle class="station" cx="{x_coordinate}" '
                    f'cy="{y_coordinate}" r="{self.STATION_RADIUS}" '
                    f'stroke="{route_colors[route_id]}"/>'
                )
            lines.append(
                self._stop_label_svg_line(
                    stop.name,
                    x_coordinate,
                    y_coordinate,
                )
            )
        return lines

    def _stop_label_svg_line(
        self,
        stop_name: str,
        x_coordinate: float,
        y_coordinate: float,
    ) -> str:
        words = stop_name.split()
        line_height = self.LABEL_FONT_SIZE * 1.05
        first_offset = -(len(words) - 1) * line_height / 2
        tspans = "".join(
            f'<tspan x="{x_coordinate}" dy="'
            f'{first_offset if index == 0 else line_height}">'
            f"{html.escape(word)}</tspan>"
            for index, word in enumerate(words)
        )
        return (
            f'<text class="label" x="{x_coordinate}" y="{y_coordinate}" '
            f'text-anchor="middle">{tspans}</text>'
        )
