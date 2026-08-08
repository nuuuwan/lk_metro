from collections import defaultdict

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
        route_ids = memberships[stop_name]
        if len(route_ids) > 1:
            route_ids_by_position = defaultdict(list)
            for route_id in sorted(
                route_ids, key=self._route_order.__getitem__
            ):
                position = self._route_stop_position(
                    stop_name, route_id, segments
                )
                route_ids_by_position[position].append(route_id)
            return [
                self._station_marker_svg_line(
                    (
                        position[0]
                        + (
                            marker_index
                            - (len(position_route_ids) - 1) / 2
                        )
                        * self.STATION_RADIUS
                        * 2,
                        position[1],
                    ),
                    route_id,
                    route_colors,
                )
                for position, position_route_ids in (
                    route_ids_by_position.items()
                )
                for marker_index, route_id in enumerate(position_route_ids)
            ]
        route_id = next(iter(route_ids))
        return [
            self._station_marker_svg_line(
                (x_coordinate, y_coordinate),
                route_id,
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
        position: Point,
        route_id: str,
        route_colors: dict[str, str],
    ) -> str:
        return (
            f'<circle class="station" cx="{position[0]}" cy="{position[1]}" '
            f'r="{self.STATION_RADIUS}" '
            f'stroke="{route_colors[route_id]}"/>'
        )
