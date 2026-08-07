import math

from ..GeographicDiagram import Point


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
            label_x, label_y, text_anchor = self._interchange_label_positions[
                stop_name
            ]
            label_transform = ""
        else:
            marker, label_x, label_y, text_anchor, label_transform = (
                self._station_svg_details(
                    stop_name, memberships, station_ticks, route_colors
                )
            )
        label = self._label_svg_line(
            stop_name, label_x, label_y, text_anchor, label_transform
        )
        return [marker, label]

    def _station_svg_details(
        self,
        stop_name: str,
        memberships: dict[str, set[str]],
        station_ticks: dict[str, tuple[Point, Point]],
        route_colors: dict[str, str],
    ) -> tuple[str, float, float, str, str]:
        first, second = station_ticks[stop_name]
        route_id = next(iter(memberships[stop_name]))
        marker = (
            f'<line class="station" x1="{first[0]}" y1="{first[1]}" '
            f'x2="{second[0]}" y2="{second[1]}" '
            f'stroke="{route_colors[route_id]}"/>'
        )
        label_x, label_y = self._station_label_positions[stop_name]
        text_anchor = self._station_label_text_anchors[stop_name]
        if not self.ROTATE_LABELS:
            return marker, label_x, label_y, text_anchor, ""
        label_angle = math.degrees(
            math.atan2(second[1] - first[1], second[0] - first[0])
        )
        text_anchor = "start"
        if label_angle > 90:
            label_angle -= 180
            text_anchor = "end"
        elif label_angle < -90:
            label_angle += 180
            text_anchor = "end"
        transform = f' transform="rotate({label_angle} {label_x} {label_y})"'
        return marker, label_x, label_y, text_anchor, transform
