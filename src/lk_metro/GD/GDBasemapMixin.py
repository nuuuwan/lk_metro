import base64
import math
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


class GDBasemapMixin:
    TILE_URL = "https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    TILE_USER_AGENT = "lk_metro/1.0 (https://github.com/nuuuwan/lk_metro)"
    TILE_CACHE_DIR = Path(tempfile.gettempdir()) / "lk_metro" / "osm"

    def _basemap_svg_lines(self) -> list[str]:
        if not self.SHOW_BASEMAP:
            return []
        zoom = self.BASEMAP_ZOOM
        tile_count = 2**zoom
        tile_span = 2 * math.pi / tile_count
        min_x, min_y, max_x, max_y = self._visible_mercator_bounds()
        first_x = max(0, math.floor((min_x + math.pi) / tile_span))
        last_x = min(
            tile_count - 1, math.floor((max_x + math.pi) / tile_span)
        )
        first_y = max(0, math.floor((math.pi - max_y) / tile_span))
        last_y = min(
            tile_count - 1, math.floor((math.pi - min_y) / tile_span)
        )
        lines = [
            '<defs><clipPath id="geographic-map-clip">'
            f'<rect width="{self.width}" height="{self.height}"/>'
            "</clipPath></defs>",
            f'<g class="basemap" opacity="{self.BASEMAP_OPACITY:g}" '
            'clip-path="url(#geographic-map-clip)">',
        ]
        for tile_y in range(first_y, last_y + 1):
            for tile_x in range(first_x, last_x + 1):
                lines.append(
                    self._basemap_tile_svg_line(
                        zoom, tile_x, tile_y, tile_span
                    )
                )
        lines.extend(
            [
                "</g>",
                '<a href="https://www.openstreetmap.org/copyright">'
                '<text class="basemap-attribution" '
                f'x="{self.width - 1}" y="{self.height - 1}" '
                'text-anchor="end">&#169; OpenStreetMap contributors</text>'
                "</a>",
            ]
        )
        return lines

    def _visible_mercator_bounds(self) -> tuple[float, float, float, float]:
        min_x, _, _, max_y = self._mercator_bounds
        x_offset, y_offset = self._mercator_offset
        scale = self._mercator_scale
        return (
            min_x - x_offset / scale,
            max_y - (self.height - y_offset) / scale,
            min_x + (self.width - x_offset) / scale,
            max_y + y_offset / scale,
        )

    def _basemap_tile_svg_line(
        self,
        zoom: int,
        tile_x: int,
        tile_y: int,
        tile_span: float,
    ) -> str:
        left = tile_x * tile_span - math.pi
        top = math.pi - tile_y * tile_span
        x_coordinate, y_coordinate = self._mercator_to_canvas(left, top)
        size = tile_span * self._mercator_scale + 0.02
        tile_data = base64.b64encode(
            self._osm_tile_bytes(zoom, tile_x, tile_y)
        ).decode("ascii")
        return (
            f'<image class="basemap-tile" x="{x_coordinate:g}" '
            f'y="{y_coordinate:g}" width="{size:g}" height="{size:g}" '
            'preserveAspectRatio="none" '
            f'href="data:image/png;base64,{tile_data}"/>'
        )

    def _mercator_to_canvas(
        self, x_coordinate: float, y_coordinate: float
    ) -> tuple[float, float]:
        min_x, _, _, max_y = self._mercator_bounds
        x_offset, y_offset = self._mercator_offset
        return (
            x_offset + (x_coordinate - min_x) * self._mercator_scale,
            y_offset + (max_y - y_coordinate) * self._mercator_scale,
        )

    def _osm_tile_bytes(self, zoom: int, tile_x: int, tile_y: int) -> bytes:
        path = self.TILE_CACHE_DIR / str(zoom) / str(tile_x) / f"{tile_y}.png"
        if path.exists():
            return path.read_bytes()
        url = self.TILE_URL.format(zoom=zoom, x=tile_x, y=tile_y)
        request = Request(url, headers={"User-Agent": self.TILE_USER_AGENT})
        with urlopen(request, timeout=15) as response:
            tile_data = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tile_data)
        return tile_data
