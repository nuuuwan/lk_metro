from collections.abc import Iterable

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
        route_ids = memberships[stop_name]
        if len(route_ids) > 1:
            marker_positions = self._interchange_marker_positions(
                stop_name, positions, memberships
            )
            return [
                self._station_marker_svg_line(
                    position,
                    route_id,
                    route_colors,
                )
                for route_id, position in marker_positions.items()
            ]
        route_id = next(iter(route_ids))
        marker_position = (
            self._route_stop_positions[stop_name][route_id]
            if hasattr(self, "_route_stop_positions")
            else (x_coordinate, y_coordinate)
        )
        return [
            self._station_marker_svg_line(
                marker_position,
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

    def _interchange_boundary_svg_lines(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
    ) -> list[str]:
        return [
            line
            for stop in self.stops
            if len(memberships[stop.name]) > 1
            for line in self._interchange_boundary_svg_lines_for_positions(
                self._interchange_marker_positions(
                    stop.name, positions, memberships
                )
            )
        ]

    def _align_interchange_route_segments(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        segments: dict[str, list[list[Point]]],
    ) -> None:
        if hasattr(self, "_route_offsets"):
            self._route_stop_positions = {
                stop_name: {
                    route_id: self._route_stop_position(
                        stop_name, route_id, segments
                    )
                    for route_id in route_ids
                }
                for stop_name, route_ids in memberships.items()
            }
            self._interchange_positions_by_stop = {
                stop_name: route_positions
                for stop_name, route_positions in (
                    self._route_stop_positions.items()
                )
                if len(route_positions) > 1
            }
            return
        self._interchange_positions_by_stop = {}
        for stop_name, route_ids in memberships.items():
            if len(route_ids) < 2:
                continue
            marker_positions = self._route_aligned_marker_positions(
                stop_name, positions, memberships, segments
            )
            self._interchange_positions_by_stop[stop_name] = marker_positions
            for route_id, marker_position in marker_positions.items():
                self._align_route_stop_segments(
                    stop_name, route_id, marker_position, segments
                )

    def _route_aligned_marker_positions(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
        segments: dict[str, list[list[Point]]],
    ) -> dict[str, Point]:
        route_positions = {
            route_id: self._route_stop_position(stop_name, route_id, segments)
            for route_id in memberships[stop_name]
        }
        spans = [
            max(point[axis] for point in route_positions.values())
            - min(point[axis] for point in route_positions.values())
            for axis in range(2)
        ]
        spread_axis = self._interchange_spread_axis(
            stop_name, positions, spans
        )
        route_ids = sorted(
            route_positions,
            key=lambda route_id: (
                route_positions[route_id][spread_axis],
                self._route_order[route_id],
            ),
        )
        center = positions[stop_name]
        return {
            route_id: tuple(
                center[axis]
                + (
                    marker_index - (len(route_ids) - 1) / 2
                    if axis == spread_axis
                    else 0
                )
                * self.STATION_RADIUS
                * 2
                for axis in range(2)
            )
            for marker_index, route_id in enumerate(route_ids)
        }

    def _interchange_spread_axis(
        self,
        stop_name: str,
        positions: dict[str, Point],
        fallback_spans: list[float],
    ) -> int:
        incident_edges = [
            edge
            for edge, route_ids in self._edge_routes.items()
            if stop_name in edge and len(route_ids) > 1
        ]
        if not incident_edges:
            return 0 if fallback_spans[0] >= fallback_spans[1] else 1

        def corridor_score(edge: tuple[str, str]) -> tuple[int, int]:
            route_ids = set(self._edge_routes[edge])
            continuation = sum(
                route_ids <= set(candidate_route_ids)
                for candidate_route_ids in self._edge_routes.values()
            )
            return continuation, len(route_ids)

        corridor_edge = max(incident_edges, key=corridor_score)
        normal = self._edge_normal(corridor_edge, positions)
        return 0 if abs(normal[0]) >= abs(normal[1]) else 1

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

    def _align_route_stop_segments(
        self,
        stop_name: str,
        route_id: str,
        marker_position: Point,
        segments: dict[str, list[list[Point]]],
    ) -> None:
        route_stops = self._route_stop_names(route_id)
        stop_index = route_stops.index(stop_name)
        if stop_index > 0:
            segments[route_id][stop_index - 1][-1] = marker_position
        if stop_index < len(segments[route_id]):
            segments[route_id][stop_index][0] = marker_position

    def _interchange_marker_positions(
        self,
        stop_name: str,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
    ) -> dict[str, Point]:
        if hasattr(self, "_interchange_positions_by_stop"):
            return self._interchange_positions_by_stop[stop_name]
        x_coordinate, y_coordinate = positions[stop_name]
        route_ids = sorted(
            memberships[stop_name], key=self._route_order.__getitem__
        )
        return {
            route_id: (
                x_coordinate
                + (marker_index - (len(route_ids) - 1) / 2)
                * self.STATION_RADIUS
                * 2,
                y_coordinate,
            )
            for marker_index, route_id in enumerate(route_ids)
        }

    def _route_stop_names(self, route_id: str) -> list[str]:
        if hasattr(self, "_segments_by_route"):
            route_segments = self._segments_by_route[route_id]
            return [route_segments[0]["stops"][0]] + [
                segment["stops"][1] for segment in route_segments
            ]
        route = next(route for route in self.routes if route.id == route_id)
        return route.stops

    def _interchange_boundary_svg_lines_for_positions(
        self,
        marker_positions: dict[str, Point],
    ) -> list[str]:
        x_coordinates = [point[0] for point in marker_positions.values()]
        y_coordinates = [point[1] for point in marker_positions.values()]
        boundary_radius = self.STATION_RADIUS + self.INTERCHANGE_STROKE_WIDTH
        x_coordinate = min(x_coordinates) - boundary_radius
        y_coordinate = min(y_coordinates) - boundary_radius
        width = max(x_coordinates) - min(x_coordinates) + 2 * boundary_radius
        height = max(y_coordinates) - min(y_coordinates) + 2 * boundary_radius
        fill_path = self._interchange_fill_path(
            x_coordinate,
            y_coordinate,
            width,
            height,
            boundary_radius,
            marker_positions.values(),
        )
        return [
            f'<path class="interchange-fill" d="{fill_path}" '
            'fill-rule="evenodd"/>',
            f'<rect class="interchange-boundary" x="{x_coordinate}" '
            f'y="{y_coordinate}" width="{width}" height="{height}" '
            f'rx="{boundary_radius}" ry="{boundary_radius}"/>',
        ]

    def _interchange_fill_path(
        self,
        x_coordinate: float,
        y_coordinate: float,
        width: float,
        height: float,
        radius: float,
        marker_positions: Iterable[Point],
    ) -> str:
        right = x_coordinate + width
        bottom = y_coordinate + height
        parts = [
            f"M {x_coordinate + radius},{y_coordinate}",
            f"H {right - radius} A {radius},{radius} 0 0 1 "
            f"{right},{y_coordinate + radius}",
            f"V {bottom - radius} A {radius},{radius} 0 0 1 "
            f"{right - radius},{bottom}",
            f"H {x_coordinate + radius} A {radius},{radius} 0 0 1 "
            f"{x_coordinate},{bottom - radius}",
            f"V {y_coordinate + radius} A {radius},{radius} 0 0 1 "
            f"{x_coordinate + radius},{y_coordinate} Z",
        ]
        hole_radius = self.STATION_RADIUS + self.STATION_TICK_STROKE_WIDTH / 2
        for center_x, center_y in marker_positions:
            parts.extend(
                [
                    f"M {center_x + hole_radius},{center_y}",
                    f"A {hole_radius},{hole_radius} 0 1 0 "
                    f"{center_x - hole_radius},{center_y}",
                    f"A {hole_radius},{hole_radius} 0 1 0 "
                    f"{center_x + hole_radius},{center_y} Z",
                ]
            )
        return " ".join(parts)

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
