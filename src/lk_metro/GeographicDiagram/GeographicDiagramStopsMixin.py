import html


class GeographicDiagramStopsMixin:
    def _stop_svg_lines(
        self,
        positions: dict[str, tuple[float, float]],
        paths: dict[str, list[tuple[float, float]]],
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
                first, second = self._station_tick(
                    stop.name, positions, paths
                )
                route_id = next(iter(memberships[stop.name]))
                lines.append(
                    f'<line class="station" x1="{first[0]}" '
                    f'y1="{first[1]}" x2="{second[0]}" '
                    f'y2="{second[1]}" '
                    f'stroke="{route_colors[route_id]}"/>'
                )
            lines.append(
                f'<text class="label" '
                f'x="{x_coordinate + self.LABEL_OFFSET}" '
                f'y="{y_coordinate - self.LABEL_OFFSET}">'
                f'{html.escape(stop.name)}</text>'
            )
        return lines
