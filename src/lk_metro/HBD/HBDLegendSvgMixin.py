import html

from lk_metro.GD.Point import Point


class HBDLegendSvgMixin:
    def _title_and_legend_svg_lines(self) -> list[str]:
        legend_x, legend_title_y = self._legend_origin()
        lines = [self._logo_svg_line()]
        for index, route in enumerate(self.legend_routes):
            y_coordinate = legend_title_y + 4 + index * self.LEGEND_LINE_HEIGHT
            lines.extend(
                [
                    f'<rect class="legend-swatch" x="{legend_x}" '
                    f'y="{y_coordinate - 0.65}" width="6" height="1.3" '
                    f'fill="{route.color}"/>',
                    f'<text class="legend-route-label" x="{legend_x + 8}" '
                    f'y="{y_coordinate}">{html.escape(route.id)}: '
                    f"{html.escape(self._legend_route_name(route))}</text>",
                ]
            )
        note_y = (
            legend_title_y
            + 6
            + len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
        )
        note_lines = (
            ("Inspired by Harry Beck's iconic diagrammatic", False),
            ("map of the London Underground, first published", False),
            ("in 1933.", False),
        )
        lines.extend(
            f'<text class="{self._note_class(is_heading)}" '
            f'x="{legend_x}" y="{note_y + index * 2.4}"'
            f'{" font-weight=\"bold\"" if is_heading else ""}>'
            f"{html.escape(self._translated_text(text))}</text>"
            for index, (text, is_heading) in enumerate(note_lines)
        )
        center_x = self._content_dimensions()[0] / 2
        footer_y = self._svg_dimensions()[1] - self._content_offset()[1] - 2
        lines.append(
            f'<text class="footer-label" x="{center_x}" y="{footer_y}" '
            f'text-anchor="middle">{html.escape(self._footer_text())}</text>'
        )
        return lines

    @staticmethod
    def _note_class(is_heading: bool) -> str:
        return "legend-label" if is_heading else "legend-route-label"

    def _legend_origin(self) -> Point:
        return (self.width - 44, self.TITLE_HEIGHT + 14)
