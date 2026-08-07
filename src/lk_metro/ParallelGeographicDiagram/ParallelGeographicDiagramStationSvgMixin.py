from lk_metro.GeographicDiagram.Point import Point


class ParallelGeographicDiagramStationSvgMixin:
    def _stop_svg_lines(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        station_ticks: dict[str, tuple[Point, Point]],
    ) -> list[str]:
        lines = []
        route_colors = {route.id: route.color for route in self.routes}
        for stop in self.stops:
            lines.extend(
                self._single_stop_svg_lines(
                    stop.name,
                    positions,
                    memberships,
                    station_ticks,
                    route_colors,
                )
            )
        return lines

    def _single_stop_svg_lines(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        station_ticks: dict[str, tuple[Point, Point]],
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
                memberships,
                station_ticks,
                route_colors,
            )
        label = self._label_svg_line(
            stop_name,
            x_coordinate,
            y_coordinate,
        )
        return [marker, label]

    def _station_marker_svg_line(
        self,
        stop_name: str,
        memberships: dict[str, set[str]],
        station_ticks: dict[str, tuple[Point, Point]],
        route_colors: dict[str, str],
    ) -> str:
        first, second = station_ticks[stop_name]
        route_id = next(iter(memberships[stop_name]))
        return (
            f'<line class="station" x1="{first[0]}" y1="{first[1]}" '
            f'x2="{second[0]}" y2="{second[1]}" '
            f'stroke="{route_colors[route_id]}"/>'
        )
