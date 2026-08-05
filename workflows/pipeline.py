import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from lk_metro.GeographicDiagram import GeographicDiagram
from lk_metro.HarryBeckDiagram import HarryBeckDiagram
from lk_metro.ParallelGeographicDiagram import ParallelGeographicDiagram
from lk_metro.Route import Route
from lk_metro.Stop import Stop


PNG_SIZE = 6000


def generate_png(svg_path: Path, png_path: Path) -> None:
	qlmanage = shutil.which("qlmanage")
	if qlmanage is None:
		raise RuntimeError("qlmanage is required to generate the PNG")

	with tempfile.TemporaryDirectory() as directory:
		subprocess.run(
			[
				qlmanage,
				"-t",
				"-s",
				str(PNG_SIZE),
				"-o",
				directory,
				str(svg_path),
			],
			check=True,
			stdout=subprocess.DEVNULL,
		)
		generated_path = Path(directory) / f"{svg_path.name}.png"
		generated_path.replace(png_path)


def main() -> None:
	images_dir = ROOT_DIR / "images"
	images_dir.mkdir(parents=True, exist_ok=True)
	Stop.generate_xy()
	routes = Route.read_all()
	stops = Stop.read_all()
	outputs = (
		(GeographicDiagram(routes, stops), "lk_metro_geographic"),
		(
			ParallelGeographicDiagram(routes, stops),
			"lk_metro_parallel_geographic",
		),
		(HarryBeckDiagram(routes, stops), "lk_metro_harry_beck"),
	)

	for diagram, filename in outputs:
		svg_path = images_dir / f"{filename}.svg"
		png_path = images_dir / f"{filename}.png"
		diagram.write_svg(svg_path)
		generate_png(svg_path, png_path)
		print(f"Generated {svg_path}")
		print(f"Generated {png_path}")


if __name__ == "__main__":
	main()
