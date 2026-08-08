from lk_metro.GD.Point import Point


class StationSvgMixin:
    def _stop_marker_svg_lines(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        segments: dict[str, list[list[Point]]],
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
                    segments,
                )
            )
        return lines

    def _single_stop_marker_svg_lines(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
        segments: dict[str, list[list[Point]]],
    ) -> list[str]:
        x_coordinate, y_coordinate = positions[stop_name]
        if len(memberships[stop_name]) > 1:
            return self._interchange_marker_svg_lines(
                stop_name,
                memberships[stop_name],
                segments,
            )
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

    def _interchange_marker_svg_lines(
        self,
        stop_name: str,
        route_ids: set[str],
        segments: dict[str, list[list[Point]]],
    ) -> list[str]:
        return [
            f'<circle class="interchange" cx="{position[0]}" '
            f'cy="{position[1]}" r="{self.INTERCHANGE_RADIUS}"/>'
            for route_id in sorted(route_ids, key=self._route_order.get)
            for position in [
                self._route_stop_position(stop_name, route_id, segments)
            ]
        ]

    def _route_stop_position(
        self,
        stop_name: str,
        route_id: str,
        segments: dict[str, list[list[Point]]],
    ) -> Point:
        route_stops = self._route_stop_names(route_id)
        stop_index = route_stops.index(stop_name)
        if stop_index < len(segments[route_id]):
            return segments[route_id][stop_index][0]
        return segments[route_id][stop_index - 1][-1]

    def _route_stop_names(self, route_id: str) -> list[str]:
        if hasattr(self, "_segments_by_route"):
            segments = self._segments_by_route[route_id]
            return [segments[0]["stops"][0]] + [
                segment["stops"][1] for segment in segments
            ]
        route = next(route for route in self.routes if route.id == route_id)
        return route.stops

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
