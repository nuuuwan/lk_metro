import html

from lk_metro.GD.Point import Point


class HBDSvgMixin:
    def _route_svg_line(self, route, segments: list[list[Point]]) -> str:
        if route.id not in self._circle_routes:
            return super()._route_svg_line(route, segments)
        center = self._circle_centers[route.id]
        center_x = (
            center[0] - self._grid_min_x
        ) * self.UNIT_SCALE + self.padding
        center_y = (
            center[1] - self._grid_min_y
        ) * self.UNIT_SCALE + self.padding
        x_radius = self._circle_routes[route.id][1] * self.UNIT_SCALE
        y_radius = self._circle_routes[route.id][2] * self.UNIT_SCALE
        return (
            f'<ellipse class="route" cx="{center_x:g}" cy="{center_y:g}" '
            f'rx="{x_radius:g}" ry="{y_radius:g}" stroke="{route.color}" '
            f'stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
        )

    def _route_name_svg_lines(self) -> list[str]:
        routes_by_id = {route.id: route for route in self.routes}
        lines = []
        for route_id, (
            x_coordinate,
            y_coordinate,
            angle,
        ) in self._route_name_positions.items():
            route = routes_by_id[route_id]
            transform = f' transform="rotate({angle} {x_coordinate} '
            transform += f'{y_coordinate})"'
            transform = transform if angle else ""
            lines.append(
                f'<text class="route-name" x="{x_coordinate}" '
                f'y="{y_coordinate}" '
                f'text-anchor="middle" fill="{route.color}"{transform}>'
                f"{html.escape(route.id)}</text>"
            )
        return lines

    def _route_name_bounds(
        self,
    ) -> list[tuple[str, tuple[float, float, float, float]]]:
        return [
            (f"route ID {route_id}", bounds)
            for route_id, bounds in self._route_name_bounds_by_id.items()
        ]

    def _background_svg_lines(self) -> list[str]:
        if "New Kelani Br." not in self._logical_positions:
            return []
        bridge_x, bridge_y = self._logical_positions["New Kelani Br."]
        bridge_x = (
            bridge_x - self._grid_min_x
        ) * self.UNIT_SCALE + self.padding
        bridge_y = (
            bridge_y - self._grid_min_y
        ) * self.UNIT_SCALE + self.padding
        diagonal_half_span = 26
        upper_y = bridge_y - diagonal_half_span
        lower_y = bridge_y + diagonal_half_span
        river_path = (
            f"M -4,{upper_y:g} "
            f"L {bridge_x - diagonal_half_span:g},{upper_y:g} "
            f"L {bridge_x + diagonal_half_span:g},{lower_y:g} "
            f"L {self.width + 4:g},{lower_y:g}"
        )
        label_x = (bridge_x + diagonal_half_span + self.width + 4) / 2
        return [
            f'<path d="{river_path}" fill="none" stroke="#66b9d0" '
            'stroke-width="4.2" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            f'<path d="{river_path}" fill="none" stroke="#d9f1f7" '
            'stroke-width="3.5" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            f'<text x="{label_x:g}" y="{lower_y:g}" text-anchor="middle" '
            'dominant-baseline="middle" '
            'font-family="Gill Sans, sans-serif" font-size="1.6" '
            'font-style="italic" fill="#287f98">Kelani River</text>',
        ]

    def _svg_dimensions(self) -> tuple[int, int]:
        return super()._svg_dimensions()

    def _content_offset(self) -> Point:
        return super()._content_offset()

    @property
    def complexity_by_route(self) -> dict[str, int]:
        return {
            route.id: (
                1
                if route.id in self._circle_routes
                else sum(
                    index == 0
                    or segment["direction"]
                    != segments[index - 1]["direction"]
                    for index, segment in enumerate(segments)
                )
            )
            for route in self.routes
            for segments in [self._segments_by_route[route.id]]
        }

    @property
    def complexity(self) -> int:
        return sum(self.complexity_by_route.values())
