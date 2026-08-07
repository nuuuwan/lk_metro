from lk_metro.DiagramStyle import GRID_MAJOR_INTERVAL, GRID_SPACING


class GeographicDiagramSvgMixin:
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
            f".interchange {{ fill: white; stroke: #000000; stroke-width: "
            f"{self.INTERCHANGE_STROKE_WIDTH}; }}",
            f".label {{ font: {self.LABEL_FONT_SIZE}px {self.FONT_FAMILY}; "
            f"fill: {self.LABEL_COLOR}; dominant-baseline: middle; }}",
            f".map-title {{ font: bold {self.TITLE_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.TEXT_COLOR}; }}",
            f".legend-label {{ font: {self.LEGEND_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.TEXT_COLOR}; "
            "dominant-baseline: middle; }",
            f".legend-route-label {{ font: {self.LEGEND_FONT_SIZE}px "
            f"{self.FONT_FAMILY}; fill: {self.LABEL_COLOR}; "
            "dominant-baseline: middle; }",
        ]

    def _svg_header_lines(self) -> list[str]:
        svg_width, svg_height = self._svg_dimensions()
        content_x, content_y = self._content_offset()
        return [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
            f'height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}">',
            "<style>",
            *self._svg_style_lines(),
            "</style>",
            f'<rect width="{svg_width}" height="{svg_height}" '
            f'fill="{self.BACKGROUND_COLOR}"/>',
            f'<g transform="translate({content_x} {content_y})">',
            f'<g transform="translate(0 {self.TITLE_HEIGHT})">',
            *(self._grid_svg_lines() if self.SHOW_GRID else []),
        ]

    def _route_svg_lines(
        self,
        paths: dict[str, list[tuple[float, float]]],
    ) -> list[str]:
        lines = []
        for route in self.routes:
            points = " ".join(f"{x},{y}" for x, y in paths[route.id])
            lines.append(
                f'<polyline class="route" points="{points}" '
                f'stroke="{route.color}" '
                f'stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
            )
        return lines

    def _grid_svg_lines(self) -> list[str]:
        lines = ['<g class="coordinate-grid">']
        for x in range(0, self.width + 1, GRID_SPACING):
            grid_class = (
                "grid-major" if x % GRID_MAJOR_INTERVAL == 0 else "grid-minor"
            )
            lines.append(
                f'<line class="{grid_class}" x1="{x}" y1="0" '
                f'x2="{x}" y2="{self.height}"/>'
            )
        for y in range(0, self.height + 1, GRID_SPACING):
            grid_class = (
                "grid-major" if y % GRID_MAJOR_INTERVAL == 0 else "grid-minor"
            )
            lines.append(
                f'<line class="{grid_class}" x1="0" y1="{y}" '
                f'x2="{self.width}" y2="{y}"/>'
            )
        lines.append("</g>")
        return lines
