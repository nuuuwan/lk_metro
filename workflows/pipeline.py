import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from utils_future import File, Log

from lk_metro.GD.GD import GD
from lk_metro.HBD.HBD import HBD
from lk_metro.Route import Route
from lk_metro.Stop.Stop import Stop

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))


PNG_SIZE = 6000
log = Log("pipeline")


def generate_png(svg_path: Path, png_path: Path) -> None:
    qlmanage = shutil.which("qlmanage")
    if qlmanage is None:
        raise RuntimeError("qlmanage is required to generate the PNG")

    with tempfile.TemporaryDirectory() as directory:
        render_path = Path(directory) / svg_path.name
        tree = ET.parse(svg_path)
        root = tree.getroot()
        width = float(root.attrib["width"])
        height = float(root.attrib["height"])
        scale = PNG_SIZE / max(width, height)
        root.set("width", str(round(width * scale)))
        root.set("height", str(round(height * scale)))
        tree.write(render_path, encoding="utf-8", xml_declaration=True)
        subprocess.run(
            [
                qlmanage,
                "-t",
                "-s",
                str(PNG_SIZE),
                "-o",
                directory,
                str(render_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        generated_path = Path(directory) / f"{render_path.name}.png"
        generated_path.replace(png_path)


def main() -> None:
    images_dir = ROOT_DIR / "images" / date.today().isoformat()
    images_dir.mkdir(parents=True, exist_ok=True)
    Stop.generate_xy()
    routes = Route.read_all()
    stops = Stop.read_all()
    outputs = (
        (
            GD(routes, stops, width=300, height=300),
            "lk_metro_geographic",
        ),
        (HBD(routes, stops), "lk_metro_harry_beck"),
        (HBD(routes, stops, language="si"), "lk_metro_harry_beck_si"),
        (HBD(routes, stops, language="ta"), "lk_metro_harry_beck_ta"),
    )

    for diagram, filename in outputs:
        svg_path = images_dir / f"{filename}.svg"
        png_path = images_dir / f"{filename}.png"
        diagram.write_svg(svg_path)
        generate_png(svg_path, png_path)
        log.info(f"Wrote {File(str(svg_path))}")
        log.info(f"Wrote {File(str(png_path))}")


if __name__ == "__main__":
    main()
