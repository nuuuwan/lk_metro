import html

from lk_metro.GD.Point import Point


class HBDLegendSvgMixin:
    def _title_and_legend_svg_lines(self) -> list[str]:
        legend_x, legend_title_y = self._legend_origin()
        lines = self._title_svg_lines()
        if self.SHOW_LEGEND:
            lines.append(
                self._legend_background_svg_line(legend_x, legend_title_y)
            )
            lines.extend(
                self._legend_route_svg_lines(legend_x, legend_title_y)
            )
            lines.extend(
                self._legend_interchange_svg_lines(legend_x, legend_title_y)
            )
        if self.SHOW_DESCRIPTION:
            lines.extend(self._description_svg_lines())
        center_x = self._content_dimensions()[0] / 2
        footer_y = self._svg_dimensions()[1] - self._content_offset()[1] - 2
        lines.append(
            f'<text class="footer-label" x="{center_x}" y="{footer_y}" '
            f'text-anchor="middle">{html.escape(self._footer_text())}</text>'
        )
        return lines

    def _legend_background_svg_line(
        self,
        legend_x: float,
        legend_title_y: float,
    ) -> str:
        left_padding = self.INFO_PANEL_PADDING
        right_padding = self.INFO_PANEL_PADDING / 4
        vertical_padding = self.INFO_PANEL_PADDING
        labels = [
            f"{route.id}: {self._legend_route_name(route)}"
            for route in self.legend_routes
        ] + [self._translated_text("Interchange: transfer between routes")]
        width = 8 + max(
            len(label) * self.LEGEND_FONT_SIZE * 0.48 for label in labels
        )
        first_y = legend_title_y + 4
        last_y = first_y + len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
        half_height = self.LEGEND_FONT_SIZE / 2
        return (
            f'<rect class="info-panel legend-background" '
            f'x="{legend_x - left_padding:g}" '
            f'y="{first_y - half_height - vertical_padding:g}" '
            f'width="{width + left_padding + right_padding:g}" '
            f'height="{last_y - first_y + 2 * half_height + 2 * vertical_padding:g}" '
            f'rx="1.5" '
            f'fill="{self.INFO_PANEL_COLOR}"/>'
        )

    def _title_svg_lines(self) -> list[str]:
        center_x = self._content_dimensions()[0] / 2
        logo_height = self.LOGO_WIDTH / self.LOGO_ASPECT_RATIO
        logo_top = (self.TITLE_HEIGHT - logo_height) / 2
        logo_bottom = logo_top + logo_height
        return [
            f'<text class="map-title" x="{center_x:g}" '
            f'y="{logo_top - 0.9:g}" '
            'text-anchor="middle" dominant-baseline="middle" '
            'letter-spacing="0.5">THE UNOFFICIAL</text>',
            self._logo_svg_line(),
            f'<text class="map-title" x="{center_x:g}" '
            f'y="{logo_bottom + 0.9:g}" text-anchor="middle" '
            'dominant-baseline="middle" letter-spacing="0.5">MAP</text>',
        ]

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

    def _description_svg_lines(self) -> list[str]:
        fort_x, fort_y = self._background_stop_position("Colombo Fort")
        note_x = fort_x - 4
        note_y = fort_y - 14
        note_lines = (
            "Inspired by Harry Beck's iconic 1933 diagram",
            "of the London Underground. By prioritising",
            "connections over geography, this format makes",
            "routes and interchanges easier to follow.",
        )
        left_padding = self.INFO_PANEL_PADDING
        right_padding = self.INFO_PANEL_PADDING / 4
        vertical_padding = self.INFO_PANEL_PADDING
        half_height = self.DESCRIPTION_FONT_SIZE / 2
        text_width = max(
            len(text) * self.DESCRIPTION_FONT_SIZE * 0.48
            for text in note_lines
        )
        text_height = (len(note_lines) - 1) * 2.6 + 2 * half_height
        lines = [
            f'<rect class="info-panel description-background" '
            f'x="{note_x - left_padding:g}" '
            f'y="{note_y - half_height - vertical_padding:g}" '
            f'width="{text_width + left_padding + right_padding:g}" '
            f'height="{text_height + 2 * vertical_padding:g}" rx="1.5" '
            f'fill="{self.INFO_PANEL_COLOR}"/>'
        ]
        lines.extend(
            f'<text class="map-description" x="{note_x:g}" '
            f'y="{note_y + index * 2.6:g}" '
            f'font-family="{self.FONT_FAMILY}" '
            f'font-size="{self.DESCRIPTION_FONT_SIZE:g}" '
            f'fill="{self.DESCRIPTION_COLOR}">'
            f"{html.escape(self._translated_text(text))}</text>"
            for index, text in enumerate(note_lines)
        )
        return lines

    @staticmethod
    def _note_class(is_heading: bool) -> str:
        return "legend-label" if is_heading else "legend-route-label"

    def _legend_origin(self) -> Point:
        return (self.width - 44, self.TITLE_HEIGHT + 18)
