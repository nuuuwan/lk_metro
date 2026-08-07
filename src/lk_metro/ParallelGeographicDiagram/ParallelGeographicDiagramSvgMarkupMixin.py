from lk_metro.GeographicDiagram.Point import Point


class ParallelGeographicDiagramSvgMarkupMixin:
    def _svg_header_lines(self) -> list[str]:
        svg_width, svg_height = self._svg_dimensions()
        content_x, content_y = self._content_offset()
        return [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">',
            "<style>",
            *self._svg_style_lines(),
            "</style>",
            f'<rect width="{svg_width}" height="{svg_height}" '
            f'fill="{self.BACKGROUND_COLOR}"/>',
            f'<g transform="translate({content_x} {content_y})">',
            f'<g transform="translate(0 {self.TITLE_HEIGHT})">',
            *self._background_svg_lines(),
            *(self._grid_svg_lines() if self.SHOW_GRID else []),
        ]

    def _svg_style_lines(self) -> list[str]:
        return [
            ".grid-minor { stroke: #777; stroke-opacity: 0.12; "
            "stroke-width: 0.25; }",
            ".grid-major { stroke: #555; stroke-opacity: 0.2; "
            "stroke-width: 0.5; }",
            ".route { fill: none; stroke-linecap: butt; "
            "stroke-linejoin: round; }",
            f".station {{ stroke-width: {self.STATION_TICK_STROKE_WIDTH}; "
            "stroke-linecap: square; }",
            f".interchange {{ fill: white; stroke: #000000; "
            f"stroke-width: {self.INTERCHANGE_STROKE_WIDTH}; }}",
            f".label {{ font: {self.LABEL_FONT_SIZE}px {self.FONT_FAMILY}; "
            f"fill: {self.LABEL_COLOR}; dominant-baseline: middle; }}",
            f".terminal-label {{ font-size: "
            f"{self._terminal_label_font_size()}px; font-weight: bold; }}",
            f".route-name {{ font: bold {self._route_name_font_size()}px "
            f"{self.FONT_FAMILY}; paint-order: stroke fill; stroke: white; "
            "stroke-width: 0.7; stroke-linejoin: round; }",
            f".map-title {{ font: bold {self.TITLE_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.TEXT_COLOR}; }}",
            f".legend-label {{ font: {self.LEGEND_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.TEXT_COLOR}; "
            "dominant-baseline: middle; }",
            f".legend-route-label {{ font: {self.LEGEND_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.LABEL_COLOR}; "
            "dominant-baseline: middle; }",
        ]

    def _route_svg_lines(
        self,
        segments: dict[str, list[list[Point]]],
    ) -> list[str]:
        lines = []
        for route in self.routes:
            path_data = self._route_path_data(segments[route.id])
            lines.append(
                f'<path class="route" d="{path_data}" stroke="{route.color}" '
                f'stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
            )
        return lines
