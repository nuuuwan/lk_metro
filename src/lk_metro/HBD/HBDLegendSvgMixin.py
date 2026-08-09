import html

from lk_metro.GD.Point import Point


class HBDLegendSvgMixin:
    def _title_and_legend_svg_lines(self) -> list[str]:
        legend_x, legend_title_y = self._legend_origin()
        lines = [self._logo_svg_line()]
        if self.SHOW_LEGEND:
            lines.extend(
                self._legend_route_svg_lines(legend_x, legend_title_y)
            )
            lines.extend(
                self._legend_interchange_svg_lines(legend_x, legend_title_y)
            )
        if self.SHOW_DESCRIPTION:
            lines.extend(
                self._description_svg_lines(legend_x, legend_title_y)
            )
        center_x = self._content_dimensions()[0] / 2
        footer_y = self._svg_dimensions()[1] - self._content_offset()[1] - 2
        lines.append(
            f'<text class="footer-label" x="{center_x}" y="{footer_y}" '
            f'text-anchor="middle">{html.escape(self._footer_text())}</text>'
        )
        return lines

    def _legend_interchange_svg_lines(
        self,
        legend_x: float,
        legend_title_y: float,
    ) -> list[str]:
        label = html.escape(
            self._translated_text("Interchange: transfer between routes")
        )
        y_coordinate = (
            legend_title_y
            + 4
            + len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
        )
        outer_width = 1.3 + 2 * self.INTERCHANGE_STROKE_WIDTH
        return [
            f'<line class="legend-interchange" x1="{legend_x + 0.65}" '
            f'y1="{y_coordinate}" x2="{legend_x + 5.35}" '
            f'y2="{y_coordinate}" stroke="#000000" '
            f'stroke-width="{outer_width:g}" stroke-linecap="round"/>',
            f'<line class="legend-interchange" x1="{legend_x + 0.65}" '
            f'y1="{y_coordinate}" x2="{legend_x + 5.35}" '
            f'y2="{y_coordinate}" stroke="#ffffff" '
            'stroke-width="1.3" stroke-linecap="round"/>',
            f'<text class="legend-route-label" x="{legend_x + 8}" '
            f'y="{y_coordinate}">{label}</text>',
        ]

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
                    f'<text class="legend-route-label" '
                    f'x="{legend_x + 8}" y="{y_coordinate}">'
                    f"{html.escape(route.id)}: "
                    f"{html.escape(self._legend_route_name(route))}</text>",
                ]
            )
        return lines

    def _description_svg_lines(
        self, legend_x: float, legend_title_y: float
    ) -> list[str]:
        legend_row_count = (
            len(self.legend_routes) + 1 if self.SHOW_LEGEND else 0
        )
        note_y = (
            legend_title_y + 6 + legend_row_count * self.LEGEND_LINE_HEIGHT
        )
        note_lines = (
            "Inspired by Harry Beck's iconic diagrammatic",
            "map of the London Underground, first published",
            "in 1933.",
        )
        return [
            f'<text class="legend-route-label" x="{legend_x}" '
            f'y="{note_y + index * 2.4}">'
            f"{html.escape(self._translated_text(text))}</text>"
            for index, text in enumerate(note_lines)
        ]

    @staticmethod
    def _note_class(is_heading: bool) -> str:
        return "legend-label" if is_heading else "legend-route-label"

    def _legend_origin(self) -> Point:
        return (self.width - 44, self.TITLE_HEIGHT + 14)
