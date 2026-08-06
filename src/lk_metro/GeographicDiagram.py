import base64
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
	STATION_TICK_LENGTH,
	STATION_TICK_STROKE_WIDTH,
)
from .Route import Route
from .Stop import Stop


Point = tuple[float, float]


class GeographicDiagram:
	MAP_TITLE = "Lanka Metro"
	MAP_SUBTITLE = "GEOGRAPHIC MAP"
	DESCRIPTION_LINES = (
		"Routes follow the geographic positions of their stops,",
		"preserving the network's real-world shape and orientation.",
	)
	FOOTER_TEXT = (		
		"Data from https://lankametro.lk"
		" · Design and Visualisation by https://github.com/nuuuwan"
	)
	LEGEND_TITLE = "Routes"
	TITLE_HEIGHT = 12
	LOGO_WIDTH = 36
	LOGO_ASPECT_RATIO = 607 / 190
	LEGEND_WIDTH = 58
	LEGEND_LINE_HEIGHT = 3.5
	LEGEND_FONT_SIZE = 1.55
	TITLE_FONT_SIZE = 3.8
	BACKGROUND_COLOR = "#ffffff"
	TEXT_COLOR = "#991f1d"
	LABEL_COLOR = "#000000"
	FONT_FAMILY = "sans-serif"
	SHOW_GRID = False
	ROUTE_STROKE_WIDTH = ROUTE_STROKE_WIDTH
	INTERCHANGE_RADIUS = INTERCHANGE_RADIUS
	INTERCHANGE_STROKE_WIDTH = INTERCHANGE_STROKE_WIDTH
	STATION_TICK_LENGTH = STATION_TICK_LENGTH
	STATION_TICK_STROKE_WIDTH = STATION_TICK_STROKE_WIDTH
	LABEL_FONT_SIZE = LABEL_FONT_SIZE
	LABEL_OFFSET = LABEL_OFFSET
	LABEL_HALO_WIDTH = 0.0

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
		self.legend_routes = routes
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
		svg_width, svg_height = self._svg_dimensions()
		content_x, content_y = self._content_offset()
		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
			f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">',
			"<style>",
			".grid-minor { stroke: #777; stroke-opacity: 0.12; stroke-width: 0.25; }",
			".grid-major { stroke: #555; stroke-opacity: 0.2; stroke-width: 0.5; }",
			".route { fill: none; stroke-linecap: butt; stroke-linejoin: round; }",
			f".station {{ stroke-width: "
			f"{self.STATION_TICK_STROKE_WIDTH}; stroke-linecap: square; }}",
			f".interchange {{ fill: white; stroke: #000000; "
			f"stroke-width: {self.INTERCHANGE_STROKE_WIDTH}; }}",
			f".label {{ font: {self.LABEL_FONT_SIZE}px {self.FONT_FAMILY}; "
			f"fill: {self.LABEL_COLOR}; "
			"dominant-baseline: middle; }",
			f".map-title {{ font: bold {self.TITLE_FONT_SIZE}px {self.FONT_FAMILY}; "
			f"fill: {self.TEXT_COLOR}; }}",
			f".legend-label {{ font: {self.LEGEND_FONT_SIZE}px {self.FONT_FAMILY}; "
			f"fill: {self.TEXT_COLOR}; "
			"dominant-baseline: middle; }",
			f".legend-route-label {{ font: {self.LEGEND_FONT_SIZE}px "
			f"{self.FONT_FAMILY}; fill: {self.LABEL_COLOR}; "
			"dominant-baseline: middle; }",
			"</style>",
			f'<rect width="{svg_width}" height="{svg_height}" '
			f'fill="{self.BACKGROUND_COLOR}"/>',
			f'<g transform="translate({content_x} {content_y})">',
			f'<g transform="translate(0 {self.TITLE_HEIGHT})">',
			*(self._grid_svg_lines() if self.SHOW_GRID else []),
		]

		routes_to_draw = self.routes
		for route in routes_to_draw:
			points = " ".join(f"{x},{y}" for x, y in paths[route.id])
			lines.append(
				f'<polyline class="route" points="{points}" '
				f'stroke="{route.color}" stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
			)

		visible_stop_names = {
			stop_name
			for route in routes_to_draw
			for stop_name in route.stops
		}
		memberships = self._route_memberships(routes_to_draw)
		route_colors = {route.id: route.color for route in routes_to_draw}
		for stop in self.stops:
			if stop.name not in visible_stop_names:
				continue
			x, y = positions[stop.name]
			if len(memberships[stop.name]) > 1:
				lines.append(
					f'<circle class="interchange" cx="{x}" cy="{y}" '
					f'r="{self.INTERCHANGE_RADIUS}"/>'
				)
			else:
				first, second = self._station_tick(stop.name, positions, paths)
				route_id = next(iter(memberships[stop.name]))
				lines.append(
					f'<line class="station" x1="{first[0]}" y1="{first[1]}" '
					f'x2="{second[0]}" y2="{second[1]}" '
					f'stroke="{route_colors[route_id]}"/>'
				)
			lines.append(
				f'<text class="label" x="{x + self.LABEL_OFFSET}" '
				f'y="{y - self.LABEL_OFFSET}">'
				f"{html.escape(stop.name)}</text>"
			)

		lines.extend(
			["</g>", *self._title_and_legend_svg_lines(), "</g>", "</svg>"]
		)
		return "\n".join(lines) + "\n"

	def _station_tick(
		self,
		stop_name: str,
		positions: dict[str, Point],
		paths: dict[str, list[Point]],
	) -> tuple[Point, Point]:
		route = next(route for route in self.routes if stop_name in route.stops)
		stop_index = route.stops.index(stop_name)
		neighbor_index = 1 if stop_index == 0 else stop_index - 1
		neighbor = paths[route.id][neighbor_index]
		x_coordinate, y_coordinate = positions[stop_name]
		x_delta = neighbor[0] - x_coordinate
		y_delta = neighbor[1] - y_coordinate
		length = math.hypot(x_delta, y_delta)
		x_offset = -y_delta / length * self.STATION_TICK_LENGTH / 2
		y_offset = x_delta / length * self.STATION_TICK_LENGTH / 2
		return (
			(x_coordinate - x_offset, y_coordinate - y_offset),
			(x_coordinate + x_offset, y_coordinate + y_offset),
		)

	def _svg_dimensions(self) -> tuple[int, int]:
		width, height = self._content_dimensions()
		size = max(width, height)
		return size, size

	def _content_dimensions(self) -> tuple[int, int]:
		return self.width + self.LEGEND_WIDTH, self.height + self.TITLE_HEIGHT

	def _content_offset(self) -> Point:
		width, height = self._content_dimensions()
		size = max(width, height)
		return ((size - width) / 2, (size - height) / 2)

	def _legend_origin(self) -> Point:
		return (self.width + 4, self.TITLE_HEIGHT + 2)

	def _title_and_legend_svg_lines(self) -> list[str]:
		legend_x, legend_title_y = self._legend_origin()
		lines = [
			self._logo_svg_line(),
			f'<text class="map-title" x="{self.padding + self.LOGO_WIDTH + 4}" '
			f'y="{self.TITLE_HEIGHT / 2 + self.TITLE_FONT_SIZE / 3}">'
			f'{html.escape(self.MAP_SUBTITLE)}</text>',
			f'<text class="legend-label" x="{legend_x}" y="{legend_title_y}" '
			f'font-weight="bold">{html.escape(self.LEGEND_TITLE)}</text>',
		]
		for index, route in enumerate(self.legend_routes):
			y_coordinate = legend_title_y + 4 + index * self.LEGEND_LINE_HEIGHT
			lines.extend(
				[
					f'<rect class="legend-swatch" x="{legend_x}" '
					f'y="{y_coordinate - 0.65}" width="6" height="1.3" '
					f'fill="{route.color}"/>',
					f'<text class="legend-route-label" x="{legend_x + 8}" '
					f'y="{y_coordinate}">{html.escape(route.id)}: '
					f'{html.escape(route.name)}</text>',
				]
			)
		note_y = legend_title_y + 6 + len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
		lines.extend(
			f'<text class="legend-route-label" x="{legend_x}" '
			f'y="{note_y + index * 2.4}">{html.escape(text)}</text>'
			for index, text in enumerate(self.DESCRIPTION_LINES)
		)
		footer_y = self._content_dimensions()[1] - 2
		lines.append(
			f'<text class="legend-route-label" x="{self.padding}" '
			f'y="{footer_y}">{html.escape(self.FOOTER_TEXT)}</text>'
		)
		return lines

	def _logo_svg_line(self) -> str:
		logo_path = (
			Path(__file__).resolve().parents[2]
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