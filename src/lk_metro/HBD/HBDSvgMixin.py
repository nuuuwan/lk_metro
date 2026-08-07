import html

from lk_metro.GD.Point import Point


class HBDSvgMixin:
    def _route_name_svg_lines(self) -> list[str]:
        routes_by_id = {route.id: route for route in self.routes}
        lines = []
        for route_id, (
            x_coordinate,
            y_coordinate,
            angle,
        ) in self.ROUTE_NAME_POSITIONS.items():
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
        text_width = 4 * self.ROUTE_NAME_FONT_SIZE * 0.6
        half_height = self.ROUTE_NAME_FONT_SIZE * 0.6
        bounds = []
        for route_id, (
            x_coordinate,
            y_coordinate,
            angle,
        ) in self.ROUTE_NAME_POSITIONS.items():
            half_width = text_width / 2
            if angle:
                half_width, rotated_half_height = half_height, half_width
            else:
                rotated_half_height = half_height
            bounds.append(
                (
                    f"route ID {route_id}",
                    (
                        x_coordinate - half_width,
                        y_coordinate - rotated_half_height,
                        x_coordinate + half_width,
                        y_coordinate + rotated_half_height,
                    ),
                )
            )
        return bounds

    def _background_svg_lines(self) -> list[str]:
        return [
            f'<path d="{self.RIVER_PATH}" fill="none" stroke="#66b9d0" '
            'stroke-width="4.2" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            f'<path d="{self.RIVER_PATH}" fill="none" stroke="#d9f1f7" '
            'stroke-width="3.5" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            '<text x="58" y="33.6" text-anchor="middle" '
            'font-family="Gill Sans, sans-serif" font-size="0.8" '
            'font-style="italic" fill="#287f98">Kelani River</text>',
        ]

    def _svg_dimensions(self) -> tuple[int, int]:
        return super()._svg_dimensions()

    def _content_offset(self) -> Point:
        return super()._content_offset()

    @property
    def complexity_by_route(self) -> dict[str, int]:
        return {
            route.id: sum(
                index == 0
                or segment["direction"] != segments[index - 1]["direction"]
                for index, segment in enumerate(segments)
            )
            for route in self.routes
            for segments in [self._segments_by_route[route.id]]
        }

    @property
    def complexity(self) -> int:
        return sum(self.complexity_by_route.values())
