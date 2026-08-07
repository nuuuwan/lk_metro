import base64
from pathlib import Path


class GeographicDiagramIOMixin:
    def _logo_svg_line(self) -> str:
        logo_path = (
            Path(__file__).resolve().parents[3]
            / "source_data"
            / "lanka-metro-logo.png"
        )
        logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        logo_height = self.LOGO_WIDTH / self.LOGO_ASPECT_RATIO
        logo_y = (self.TITLE_HEIGHT - logo_height) / 2
        return (
            f'<image class="map-logo" x="{self.padding}" y="{logo_y}" '
            f'width="{self.LOGO_WIDTH}" height="{logo_height}" '
            f'href="data:image/png;base64,{logo_data}"/>'
        )

    def write_svg(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.write_text(self.to_svg(), encoding="utf-8")
        return output_path
