import html
import math
from pathlib import Path

from .DiagramStyle import (
	GRID_MAJOR_INTERVAL,
	GRID_SPACING,
	INTERCHANGE_RADIUS,
	INTERCHANGE_STROKE_WIDTH,
	LABEL_FONT_SIZE,
	LABEL_OFFSET,
	ROUTE_STROKE_WIDTH,
)
from .Route import Route
from .Stop import Stop


Point = tuple[float, float]


class GeographicDiagram:
	def __init__(
		self,
		routes: list[Route],
		stops: list[Stop],
		width: int = 100,
		height: int = 100,
		padding: int = 6,
	) -> None:
		if width <= padding * 2 or height <= padding * 2:
			raise ValueError("width and height must be larger than twice the padding")

		self.routes = routes
		self.stops = stops
		self.width = width
		self.height = height
		self.padding = padding
		self._stops_by_name = {stop.name: stop for stop in stops}
		self._validate_data()

	def layout(self) -> dict[str, Point]:
		projected = {
			stop.name: (
				math.radians(stop.latlng[1]),
				math.log(
					math.tan(
						math.pi / 4 + math.radians(stop.latlng[0]) / 2
					)
				),
			)
			for stop in self.stops
		}
		min_x = min(point[0] for point in projected.values())
		max_x = max(point[0] for point in projected.values())
		min_y = min(point[1] for point in projected.values())
		max_y = max(point[1] for point in projected.values())
		x_range = max_x - min_x
		y_range = max_y - min_y
		if math.isclose(x_range, 0.0) or math.isclose(y_range, 0.0):
			raise ValueError("Geographic stops must span both latitude and longitude")
		scale = min(
			(self.width - self.padding * 2) / x_range,
			(self.height - self.padding * 2) / y_range,
		)
		x_offset = self.padding + (
			self.width - self.padding * 2 - x_range * scale
		) / 2
		y_offset = self.padding + (
			self.height - self.padding * 2 - y_range * scale
		) / 2
		return {
			name: (
				x_offset + (point[0] - min_x) * scale,
				y_offset + (max_y - point[1]) * scale,
			)
			for name, point in projected.items()
		}

	def route_paths(
		self,
		positions: dict[str, Point] | None = None,
	) -> dict[str, list[Point]]:
		positions = positions or self.layout()
		return {
			route.id: [positions[station] for station in route.stops]
			for route in self.routes
		}

	def to_svg(self) -> str:
		positions = self.layout()
		paths = self.route_paths(positions)
		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
			f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">',
			"<style>",
			".grid-minor { stroke: #777; stroke-opacity: 0.12; stroke-width: 0.25; }",
			".grid-major { stroke: #555; stroke-opacity: 0.2; stroke-width: 0.5; }",
			".route { fill: none; stroke-linecap: round; stroke-linejoin: round; }",
			f".interchange {{ fill: white; stroke: #111; "
			f"stroke-width: {INTERCHANGE_STROKE_WIDTH}; }}",
			f".label {{ font: {LABEL_FONT_SIZE}px sans-serif; fill: #111; "
			"dominant-baseline: middle; }",
			"</style>",
			f'<rect width="{self.width}" height="{self.height}" fill="#f7f5ef"/>',
			*self._grid_svg_lines(),
		]

		routes_to_draw = self.routes
		for route in routes_to_draw:
			points = " ".join(f"{x},{y}" for x, y in paths[route.id])
			lines.append(
				f'<polyline class="route" points="{points}" '
				f'stroke="{route.color}" stroke-width="{ROUTE_STROKE_WIDTH}"/>'
			)

		visible_stop_names = {
			stop_name
			for route in routes_to_draw
			for stop_name in route.stops
		}
		memberships = self._route_memberships(routes_to_draw)
		for stop in self.stops:
			if stop.name not in visible_stop_names:
				continue
			x, y = positions[stop.name]
			if len(memberships[stop.name]) > 1:
				lines.append(
					f'<circle class="interchange" cx="{x}" cy="{y}" '
					f'r="{INTERCHANGE_RADIUS}"/>'
				)
			lines.append(
				f'<text class="label" x="{x + LABEL_OFFSET}" '
				f'y="{y - LABEL_OFFSET}">'
				f"{html.escape(stop.name)}</text>"
			)

		lines.append("</svg>")
		return "\n".join(lines) + "\n"

	def write_svg(self, path: str | Path) -> Path:
		output_path = Path(path)
		output_path.write_text(self.to_svg(), encoding="utf-8")
		return output_path

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

		for stop in self.stops:
			if len(stop.latlng) != 2 or any(
				not math.isfinite(coordinate) for coordinate in stop.latlng
			):
				raise ValueError(
					f"Stop {stop.name!r} must have finite latitude and longitude"
				)
			latitude, longitude = stop.latlng
			if not -85.0 < latitude < 85.0 or not -180.0 <= longitude <= 180.0:
				raise ValueError(f"Stop {stop.name!r} has invalid latitude or longitude")
			if len(stop.xy) != 2 or any(
				type(coordinate) not in (int, float) or not math.isfinite(coordinate)
				for coordinate in stop.xy
			):
				raise ValueError(
					f"Stop {stop.name!r} must have finite x and y coordinates"
				)

	def _route_memberships(
		self,
		routes: list[Route] | None = None,
	) -> dict[str, set[str]]:
		memberships = {stop.name: set() for stop in self.stops}
		for route in routes or self.routes:
			for name in route.stops:
				memberships[name].add(route.id)
		return memberships