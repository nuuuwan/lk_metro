import html

from lk_metro.GD.Point import Point


class HBDLegendSvgMixin:
    def _title_and_legend_svg_lines(self) -> list[str]:
        lines = [self._logo_svg_line()]
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
