import html


class GDLegendMixin:
    def _svg_dimensions(self) -> tuple[int, int]:
        width, height = self._content_dimensions()
        size = max(width, height)
        return size, size

    def _content_dimensions(self) -> tuple[int, int]:
        return self.width + self.LEGEND_WIDTH, self.height + self.TITLE_HEIGHT

    def _content_offset(self) -> tuple[float, float]:
        width, height = self._content_dimensions()
        size = max(width, height)
        return ((size - width) / 2, (size - height) / 2)

    def _legend_origin(self) -> tuple[float, float]:
        return (self.width + 4, self.TITLE_HEIGHT + 2)

    def _title_and_legend_svg_lines(self) -> list[str]:
        legend_x, legend_title_y = self._legend_origin()
        title_x = self.padding + self.LOGO_WIDTH + 4
        footer_y = self._content_dimensions()[1] - 2
        title_y = self.TITLE_HEIGHT / 2 + self.TITLE_FONT_SIZE / 3
        lines = [
            self._logo_svg_line(),
            f'<text class="map-title" x="{title_x}" y="{title_y}">'
            f'{html.escape(self.MAP_SUBTITLE)}</text>',
            f'<text class="legend-label" x="{legend_x}" '
            f'y="{legend_title_y}" font-weight="bold">'
            f'{html.escape(self.LEGEND_TITLE)}</text>',
            *self._legend_route_svg_lines(legend_x, legend_title_y),
            *self._legend_note_svg_lines(legend_x, legend_title_y),
            f'<text class="footer-label" x="{self.padding}" '
            f'y="{footer_y}">{html.escape(self.FOOTER_TEXT)}</text>',
        ]
        return lines

    def _legend_route_svg_lines(
        self, legend_x: float, legend_title_y: float
    ) -> list[str]:
        lines = []
        for index, route in enumerate(self.legend_routes):
            y_coordinate = (
                legend_title_y + 4 + index * self.LEGEND_LINE_HEIGHT
            )
            lines.extend(
                [
                    f'<rect class="legend-swatch" x="{legend_x}" '
                    f'y="{y_coordinate - 0.65}" width="6" height="1.3" '
                    f'fill="{route.color}"/>',
                    f'<text class="legend-route-label" x="{legend_x + 8}" '
                    f'y="{y_coordinate}">{html.escape(route.id)}: '
                    f'{html.escape(route.name)}</text>',
                ]
            )
        return lines

    def _legend_note_svg_lines(
        self, legend_x: float, legend_title_y: float
    ) -> list[str]:
        note_y = (
            legend_title_y
            + 6
            + len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
        )
        return [
            f'<text class="legend-route-label" x="{legend_x}" '
            f'y="{note_y + index * 2.4}">{html.escape(text)}</text>'
            for index, text in enumerate(self.DESCRIPTION_LINES)
        ]
