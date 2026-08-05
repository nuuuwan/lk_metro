import html
import json
import math
from dataclasses import dataclass
from pathlib import Path

from .Route import Route
from .Stop import Stop


Point = tuple[float, float]


@dataclass(frozen=True)
class HarryBeckSegment:
	orientation: str
	stations: tuple[str, ...]


class HarryBeck:
	DIAGONAL = math.sqrt(0.5)
	ROUTE_COLORS = (
		"#d71920",
		"#0057a8",
		"#00853f",
		"#f2a900",
		"#7b3f98",
		"#00a6b2",
		"#e86a10",
	)
	DIRECTIONS: tuple[Point, ...] = (
		(1.0, 0.0),
		(DIAGONAL, DIAGONAL),
		(0.0, 1.0),
		(-DIAGONAL, DIAGONAL),
		(-1.0, 0.0),
		(-DIAGONAL, -DIAGONAL),
		(0.0, -1.0),
		(DIAGONAL, -DIAGONAL),
	)
	ORIENTATION_VECTORS: dict[str, Point] = {
		"N": (0.0, -1.0),
		"NE": (DIAGONAL, -DIAGONAL),
		"E": (1.0, 0.0),
		"SE": (DIAGONAL, DIAGONAL),
		"S": (0.0, 1.0),
		"SW": (-DIAGONAL, DIAGONAL),
		"W": (-1.0, 0.0),
		"NW": (-DIAGONAL, -DIAGONAL),
	}

	def __init__(
		self,
		routes: list[Route],
		stops: list[Stop],
		spacing: int = 80,
		design_path: str | Path | None = None,
	) -> None:
		if spacing <= 0:
			raise ValueError("spacing must be positive")

		self.routes = routes
		self.stops = stops
		self.spacing = spacing
		self._stops_by_name = {stop.name: stop for stop in stops}
		self._validate_data()
		self.design_path = Path(design_path) if design_path else (
			Path(__file__).resolve().parents[2] / "data" / "harry_beck.json"
		)
		self.origin, self.segments = self._read_design()

	def layout(self) -> dict[str, Point]:
		positions: dict[str, Point] = {self.origin: (0.0, 0.0)}
		occupied: dict[Point, str] = {(0.0, 0.0): self.origin}

		for index, segment in enumerate(self.segments):
			anchor = segment.stations[0]
			if anchor not in positions:
				raise ValueError(
					f"Segment {index} starts at unplaced station {anchor!r}"
				)

			direction = self.ORIENTATION_VECTORS[segment.orientation]
			anchor_point = positions[anchor]
			for offset, station in enumerate(segment.stations[1:], 1):
				point = (
					round(anchor_point[0] + direction[0] * offset, 10),
					round(anchor_point[1] + direction[1] * offset, 10),
				)
				if station in positions and not self._same_point(positions[station], point):
					raise ValueError(
						f"Segment {index} places {station!r} inconsistently"
					)
				occupant = occupied.get(point)
				if occupant is not None and occupant != station:
					raise ValueError(
						f"Segment {index} overlaps {station!r} with {occupant!r}"
					)
				positions[station] = point
				occupied[point] = station

		missing = sorted(set(self._stops_by_name) - set(positions))
		if missing:
			raise ValueError("Design omits stations: " + ", ".join(missing))
		return positions

	def route_paths(
		self,
		positions: dict[str, Point] | None = None,
	) -> dict[str, list[list[Point]]]:
		positions = positions or self.layout()
		return {
			route.id: [
				self._octilinear_path(positions[first], positions[second])
				for first, second in zip(route.stops, route.stops[1:])
			]
			for route in self.routes
		}

	def to_svg(self) -> str:
		positions = self.layout()
		paths = self.route_paths(positions)
		min_x = min(point[0] for point in positions.values())
		max_x = max(point[0] for point in positions.values())
		min_y = min(point[1] for point in positions.values())
		max_y = max(point[1] for point in positions.values())
		margin = self.spacing * 2
		width = (max_x - min_x) * self.spacing + margin * 2
		height = (max_y - min_y) * self.spacing + margin * 2

		def svg_point(point: Point) -> tuple[float, float]:
			return (
				(point[0] - min_x) * self.spacing + margin,
				(point[1] - min_y) * self.spacing + margin,
			)

		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
			f'height="{height}" viewBox="0 0 {width} {height}">',
			"<style>",
			".route { fill: none; stroke-linecap: round; stroke-linejoin: round; }",
			".station { fill: white; stroke: #111; stroke-width: 3; }",
			".interchange { fill: white; stroke: #111; stroke-width: 5; }",
			".label { font: 14px sans-serif; fill: #111; dominant-baseline: middle; }",
			"</style>",
			f'<rect width="{width}" height="{height}" fill="#f7f5ef"/>',
		]

		for index, route in enumerate(self.routes):
			color = self.ROUTE_COLORS[index % len(self.ROUTE_COLORS)]
			for path in paths[route.id]:
				points = " ".join(
					f"{x},{y}" for x, y in (svg_point(point) for point in path)
				)
				lines.append(
					f'<polyline class="route" points="{points}" '
					f'stroke="{color}" stroke-width="12"/>'
				)

		memberships = self._route_memberships()
		for name, point in positions.items():
			x, y = svg_point(point)
			css_class = "interchange" if len(memberships[name]) > 1 else "station"
			radius = 9 if css_class == "interchange" else 6
			lines.append(
				f'<circle class="{css_class}" cx="{x}" cy="{y}" r="{radius}"/>'
			)
			lines.append(
				f'<text class="label" x="{x + 13}" y="{y - 13}">'
				f"{html.escape(name)}</text>"
			)

		lines.append("</svg>")
		return "\n".join(lines) + "\n"

	def write_svg(self, path: str | Path) -> Path:
		output_path = Path(path)
		output_path.write_text(self.to_svg(), encoding="utf-8")
		return output_path

	def _validate_data(self) -> None:
		if not self.routes:
			raise ValueError("At least one route is required")
		if not self.stops:
			raise ValueError("At least one stop is required")
		if len(self._stops_by_name) != len(self.stops):
			raise ValueError("Stop names must be unique")

		unknown_stops = sorted(
			{
				name
				for route in self.routes
				for name in route.stops
				if name not in self._stops_by_name
			}
		)
		if unknown_stops:
			raise ValueError(
				"Routes reference unknown stops: " + ", ".join(unknown_stops)
			)

	def _read_design(self) -> tuple[str, tuple[HarryBeckSegment, ...]]:
		with self.design_path.open(encoding="utf-8") as file:
			design = json.load(file)

		if not isinstance(design, dict):
			raise ValueError("Harry Beck design must be a JSON object")
		origin = design.get("origin")
		if not isinstance(origin, str) or origin not in self._stops_by_name:
			raise ValueError("Harry Beck design has an invalid origin")
		records = design.get("segments")
		if not isinstance(records, list) or not records:
			raise ValueError("Harry Beck design must contain segments")

		segments = []
		for index, record in enumerate(records):
			if not isinstance(record, dict):
				raise ValueError(f"Segment {index} must be an object")
			orientation = record.get("orientation")
			stations = record.get("stations")
			if not isinstance(orientation, str) or orientation not in self.ORIENTATION_VECTORS:
				raise ValueError(f"Segment {index} has invalid orientation")
			if (
				not isinstance(stations, list)
				or len(stations) < 2
				or not all(isinstance(station, str) for station in stations)
			):
				raise ValueError(f"Segment {index} must contain multiple stations")
			unknown = sorted(set(stations) - set(self._stops_by_name))
			if unknown:
				raise ValueError(
					f"Segment {index} references unknown stations: {', '.join(unknown)}"
				)
			segments.append(HarryBeckSegment(orientation, tuple(stations)))

		return origin, tuple(segments)

	@staticmethod
	def _same_point(first: Point, second: Point) -> bool:
		return math.isclose(first[0], second[0], abs_tol=1e-8) and math.isclose(
			first[1], second[1], abs_tol=1e-8
		)

	@staticmethod
	def _octilinear_path(first: Point, second: Point) -> list[Point]:
		x_delta = second[0] - first[0]
		y_delta = second[1] - first[1]
		if (
			math.isclose(x_delta, 0.0, abs_tol=1e-9)
			or math.isclose(y_delta, 0.0, abs_tol=1e-9)
			or math.isclose(abs(x_delta), abs(y_delta), abs_tol=1e-9)
		):
			return [first, second]

		diagonal_length = min(abs(x_delta), abs(y_delta))
		bend = (
			first[0] + (1 if x_delta > 0 else -1) * diagonal_length,
			first[1] + (1 if y_delta > 0 else -1) * diagonal_length,
		)
		return [first, bend, second]

	def _route_memberships(self) -> dict[str, set[str]]:
		memberships = {stop.name: set() for stop in self.stops}
		for route in self.routes:
			for name in route.stops:
				memberships[name].add(route.id)
		return memberships