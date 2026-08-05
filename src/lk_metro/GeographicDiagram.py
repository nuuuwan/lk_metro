import html
import math
from pathlib import Path

from .Route import Route
from .Stop import Stop


Point = tuple[float, float]


class GeographicDiagram:
	def __init__(
		self,
		routes: list[Route],
		stops: list[Stop],
		width: int = 2400,
		height: int = 2400,
		padding: int = 120,
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
			stop.name: self._web_mercator(stop.latlng[0], stop.latlng[1])
			for stop in self.stops
		}
		min_x = min(point[0] for point in projected.values())
		max_x = max(point[0] for point in projected.values())
		min_y = min(point[1] for point in projected.values())
		max_y = max(point[1] for point in projected.values())
		x_range = max_x - min_x
		y_range = max_y - min_y
		if math.isclose(x_range, 0.0) and math.isclose(y_range, 0.0):
			return {
				name: (self.width / 2, self.height / 2) for name in projected
			}

		x_scale = math.inf if math.isclose(x_range, 0.0) else (
			(self.width - self.padding * 2) / x_range
		)
		y_scale = math.inf if math.isclose(y_range, 0.0) else (
			(self.height - self.padding * 2) / y_range
		)
		scale = min(x_scale, y_scale)
		content_width = x_range * scale
		content_height = y_range * scale
		x_offset = (self.width - content_width) / 2
		y_offset = (self.height - content_height) / 2

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
			".route { fill: none; stroke-linecap: round; stroke-linejoin: round; }",
			".station { fill: white; stroke: #111; stroke-width: 3; }",
			".interchange { fill: white; stroke: #111; stroke-width: 5; }",
			".label { font: 7px sans-serif; fill: #111; dominant-baseline: middle; "
			"paint-order: stroke; stroke: #f7f5ef; stroke-width: 4px; }",
			"</style>",
			f'<rect width="{self.width}" height="{self.height}" fill="#f7f5ef"/>',
		]

		routes_to_draw = self.routes
		for route in routes_to_draw:
			points = " ".join(f"{x},{y}" for x, y in paths[route.id])
			lines.append(
				f'<polyline class="route" points="{points}" '
				f'stroke="{route.color}" stroke-width="10"/>'
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
			is_interchange = len(memberships[stop.name]) > 1
			css_class = "interchange" if is_interchange else "station"
			radius = 8 if is_interchange else 5
			lines.append(
				f'<circle class="{css_class}" cx="{x}" cy="{y}" r="{radius}"/>'
			)
			lines.append(
				f'<text class="label" x="{x + 11}" y="{y - 11}">'
				f"{html.escape(stop.name)}</text>"
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

		for stop in self.stops:
			if len(stop.latlng) != 2:
				raise ValueError(f"Stop {stop.name!r} must have a latitude and longitude")
			latitude, longitude = stop.latlng
			if (
				not math.isfinite(latitude)
				or not math.isfinite(longitude)
				or not -85.0 < latitude < 85.0
				or not -180.0 <= longitude <= 180.0
			):
				raise ValueError(f"Stop {stop.name!r} has invalid coordinates")

	@staticmethod
	def _web_mercator(latitude: float, longitude: float) -> Point:
		latitude_radians = math.radians(latitude)
		return (
			math.radians(longitude),
			math.log(math.tan(math.pi / 4 + latitude_radians / 2)),
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