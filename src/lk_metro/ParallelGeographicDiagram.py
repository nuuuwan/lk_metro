import html
import math
from pathlib import Path

from .DiagramStyle import (
	INTERCHANGE_RADIUS,
	INTERCHANGE_STROKE_WIDTH,
	LABEL_FONT_SIZE,
	LABEL_OFFSET,
	PARALLEL_ROUTE_GAP,
	ROUTE_STROKE_WIDTH,
	STATION_TICK_LENGTH,
	STATION_TICK_STROKE_WIDTH,
)
from .GeographicDiagram import GeographicDiagram, Point
from .Route import Route
from .Stop import Stop


Edge = tuple[str, str]


class ParallelGeographicDiagram(GeographicDiagram):
	def __init__(
		self,
		routes: list[Route],
		stops: list[Stop],
		width: int = 200,
		height: int = 200,
		padding: int = 6,
		parallel_route_gap: float = PARALLEL_ROUTE_GAP,
	) -> None:
		if parallel_route_gap <= 0:
			raise ValueError("parallel_route_gap must be positive")
		super().__init__(routes, stops, width, height, padding)
		active_stop_names = {
			stop_name for route in self.routes for stop_name in route.stops
		}
		self.stops = [
			stop for stop in self.stops if stop.name in active_stop_names
		]
		self.parallel_route_gap = parallel_route_gap
		self._route_order = {
			route.id: index for index, route in enumerate(self.routes)
		}
		self._edge_directions: dict[Edge, tuple[str, str]] = {}
		self._edge_routes = self._build_edge_routes()

	def layout(self) -> dict[str, Point]:
		positions = {
			stop.name: (stop.xy[0], stop.xy[1]) for stop in self.stops
		}
		min_x = min(point[0] for point in positions.values())
		max_x = max(point[0] for point in positions.values())
		min_y = min(point[1] for point in positions.values())
		max_y = max(point[1] for point in positions.values())
		x_range = max_x - min_x
		y_range = max_y - min_y
		x_scale = (self.width - self.padding * 2) / x_range
		y_scale = (self.height - self.padding * 2) / y_range
		return {
			name: (
				self.padding + (point[0] - min_x) * x_scale,
				self.padding + (point[1] - min_y) * y_scale,
			)
			for name, point in positions.items()
		}

	def route_segments(
		self,
		positions: dict[str, Point] | None = None,
	) -> dict[str, list[list[Point]]]:
		positions = positions or self.layout()
		return {
			route.id: [
				self._route_edge_path(
					first,
					second,
					positions[first],
					positions[second],
					route.id,
				)
				for first, second in zip(route.stops, route.stops[1:])
			]
			for route in self.routes
		}

	def to_svg(self) -> str:
		positions = self.layout()
		segments = self.route_segments(positions)
		svg_width, svg_height = self._svg_dimensions()
		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
			f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">',
			"<style>",
			".grid-minor { stroke: #777; stroke-opacity: 0.12; stroke-width: 0.25; }",
			".grid-major { stroke: #555; stroke-opacity: 0.2; stroke-width: 0.5; }",
			".route { fill: none; stroke-linecap: round; stroke-linejoin: round; }",
			f".station-tick {{ stroke-linecap: round; "
			f"stroke-width: {STATION_TICK_STROKE_WIDTH}; }}",
			f".interchange {{ fill: white; stroke: #111; "
			f"stroke-width: {INTERCHANGE_STROKE_WIDTH}; }}",
			f".label {{ font: {LABEL_FONT_SIZE}px sans-serif; fill: #111; "
			"dominant-baseline: middle; }",
			f".map-title {{ font: bold {self.TITLE_FONT_SIZE}px sans-serif; fill: #111; }}",
			f".legend-label {{ font: {self.LEGEND_FONT_SIZE}px sans-serif; fill: #111; "
			"dominant-baseline: middle; }}",
			"</style>",
			f'<rect width="{svg_width}" height="{svg_height}" fill="#f7f5ef"/>',
			f'<g transform="translate(0 {self.TITLE_HEIGHT})">',
			*self._grid_svg_lines(),
		]

		for route in self.routes:
			for path in segments[route.id]:
				points = " ".join(f"{x},{y}" for x, y in path)
				lines.append(
					f'<polyline class="route" points="{points}" '
					f'stroke="{route.color}" stroke-width="{ROUTE_STROKE_WIDTH}"/>'
				)

		memberships = self._route_memberships()
		station_ticks = self.station_ticks(positions, segments, memberships)
		routes_by_id = {route.id: route for route in self.routes}
		for stop in self.stops:
			x, y = positions[stop.name]
			if len(memberships[stop.name]) > 1:
				lines.append(
					f'<circle class="interchange" cx="{x}" cy="{y}" '
					f'r="{INTERCHANGE_RADIUS}"/>'
				)
				label_x = x + LABEL_OFFSET
				label_y = y - LABEL_OFFSET
				text_anchor = "start"
				label_transform = ""
			else:
				first, second = station_ticks[stop.name]
				route_id = next(iter(memberships[stop.name]))
				lines.append(
					f'<line class="station-tick" x1="{first[0]}" y1="{first[1]}" '
					f'x2="{second[0]}" y2="{second[1]}" '
					f'stroke="{routes_by_id[route_id].color}"/>'
				)
				label_x, label_y = second
				tick_angle = math.degrees(
					math.atan2(second[1] - first[1], second[0] - first[0])
				)
				label_angle = tick_angle
				text_anchor = "start"
				if label_angle > 90:
					label_angle -= 180
					text_anchor = "end"
				elif label_angle < -90:
					label_angle += 180
					text_anchor = "end"
				label_transform = (
					f' transform="rotate({label_angle} {label_x} {label_y})"'
				)
			lines.append(
				f'<text class="label" x="{label_x}" y="{label_y}" '
				f'text-anchor="{text_anchor}"{label_transform}>'
				f'{html.escape(self._stop_label(stop.name))}</text>'
			)

		lines.extend(["</g>", *self._title_and_legend_svg_lines(), "</svg>"])
		return "\n".join(lines) + "\n"

	def _stop_label(self, stop_name: str) -> str:
		return stop_name

	def station_ticks(
		self,
		positions: dict[str, Point] | None = None,
		segments: dict[str, list[list[Point]]] | None = None,
		memberships: dict[str, set[str]] | None = None,
	) -> dict[str, tuple[Point, Point]]:
		positions = positions or self.layout()
		segments = segments or self.route_segments(positions)
		memberships = memberships or self._route_memberships()
		routes_by_id = {route.id: route for route in self.routes}
		ticks = {}

		for stop in self.stops:
			if len(memberships[stop.name]) != 1:
				continue
			route_id = next(iter(memberships[stop.name]))
			route = routes_by_id[route_id]
			stop_index = route.stops.index(stop.name)
			candidate_segments = []
			for path in segments[route_id][stop_index:]:
				candidate_segments.extend(zip(path, path[1:]))
			for path in reversed(segments[route_id][:stop_index]):
				candidate_segments.extend(
					zip(reversed(path), reversed(path[:-1]))
				)

			first, second = next(
				(
					(first, second)
					for first, second in candidate_segments
					if not math.isclose(math.dist(first, second), 0.0)
				),
				(None, None),
			)
			if first is None or second is None:
				raise ValueError(
					f"Cannot orient station tick for {stop.name!r}"
				)

			x_delta = second[0] - first[0]
			y_delta = second[1] - first[1]
			length = math.hypot(x_delta, y_delta)
			x_normal = -y_delta / length
			y_normal = x_delta / length
			x_offset = x_normal * STATION_TICK_LENGTH
			y_offset = y_normal * STATION_TICK_LENGTH
			if x_offset - y_offset < 0:
				x_normal = -x_normal
				y_normal = -y_normal
				x_offset = -x_offset
				y_offset = -y_offset
			x, y = positions[stop.name]
			ticks[stop.name] = (
				(
					x + x_normal * ROUTE_STROKE_WIDTH / 2,
					y + y_normal * ROUTE_STROKE_WIDTH / 2,
				),
				(
					x + x_normal * ROUTE_STROKE_WIDTH / 2 + x_offset,
					y + y_normal * ROUTE_STROKE_WIDTH / 2 + y_offset,
				),
			)

		return self._avoid_label_overlaps(positions, ticks, memberships)

	def _avoid_label_overlaps(
		self,
		positions: dict[str, Point],
		ticks: dict[str, tuple[Point, Point]],
		memberships: dict[str, set[str]],
	) -> dict[str, tuple[Point, Point]]:
		occupied = [
			self._label_bounds(
				(x + LABEL_OFFSET, y - LABEL_OFFSET),
				self._stop_label(stop.name),
				(1.0, 0.0),
			)
			for stop in self.stops
			if len(memberships[stop.name]) > 1
			for x, y in [positions[stop.name]]
		]
		selected_ticks = {}
		for stop in sorted(
			(stop for stop in self.stops if stop.name in ticks),
			key=lambda stop: (positions[stop.name][1], positions[stop.name][0]),
		):
			x, y = positions[stop.name]
			first, second = ticks[stop.name]
			mirrored = (
				(2 * x - first[0], 2 * y - first[1]),
				(2 * x - second[0], 2 * y - second[1]),
			)
			candidates = [ticks[stop.name], mirrored]
			candidate_bounds = [
				self._label_bounds(
					candidate[1],
					self._stop_label(stop.name),
					(candidate[1][0] - x, candidate[1][1] - y),
				)
				for candidate in candidates
			]
			scores = [
				sum(self._overlap_area(bounds, other) for other in occupied)
				for bounds in candidate_bounds
			]
			selected_index = min(range(len(candidates)), key=scores.__getitem__)
			selected_ticks[stop.name] = candidates[selected_index]
			occupied.append(candidate_bounds[selected_index])
		return selected_ticks

	@staticmethod
	def _label_bounds(
		anchor: Point,
		label: str,
		outward: Point,
	) -> tuple[float, float, float, float]:
		length = math.hypot(*outward)
		x_direction = outward[0] / length
		y_direction = outward[1] / length
		x_normal = -y_direction
		y_normal = x_direction
		text_width = max(LABEL_FONT_SIZE, len(label) * LABEL_FONT_SIZE * 0.55)
		half_height = LABEL_FONT_SIZE / 2
		corners = [
			(
				anchor[0] + x_direction * distance + x_normal * offset,
				anchor[1] + y_direction * distance + y_normal * offset,
			)
			for distance in (0.0, text_width)
			for offset in (-half_height, half_height)
		]
		return (
			min(point[0] for point in corners),
			min(point[1] for point in corners),
			max(point[0] for point in corners),
			max(point[1] for point in corners),
		)

	@staticmethod
	def _overlap_area(
		first: tuple[float, float, float, float],
		second: tuple[float, float, float, float],
	) -> float:
		width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
		height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
		return width * height

	def write_svg(self, path: str | Path) -> Path:
		output_path = Path(path)
		output_path.write_text(self.to_svg(), encoding="utf-8")
		return output_path

	def _build_edge_routes(self) -> dict[Edge, list[str]]:
		edge_routes: dict[Edge, list[str]] = {}
		for route in self.routes:
			for first, second in zip(route.stops, route.stops[1:]):
				edge = self._edge_key(first, second)
				if edge not in edge_routes:
					edge_routes[edge] = []
					self._edge_directions[edge] = (first, second)
				edge_routes[edge].append(route.id)
		return edge_routes

	def _route_edge_path(
		self,
		first_name: str,
		second_name: str,
		first_point: Point,
		second_point: Point,
		route_id: str,
	) -> list[Point]:
		edge = self._edge_key(first_name, second_name)
		route_ids = sorted(
			self._edge_routes[edge],
			key=self._route_order.__getitem__,
		)
		reference_first, reference_second = self._edge_directions[edge]
		is_reference_direction = (
			first_name == reference_first and second_name == reference_second
		)
		canonical_first, canonical_second = (
			(first_point, second_point)
			if is_reference_direction
			else (second_point, first_point)
		)
		path = self._octilinear_path(canonical_first, canonical_second)
		if len(route_ids) > 1:
			offset_index = route_ids.index(route_id) - (len(route_ids) - 1) / 2
			path = self._offset_path(
				path,
				offset_index * self.parallel_route_gap,
			)
		return path if is_reference_direction else list(reversed(path))

	@staticmethod
	def _octilinear_path(first: Point, second: Point) -> list[Point]:
		x_delta = second[0] - first[0]
		y_delta = second[1] - first[1]
		if math.isclose(x_delta, 0.0, abs_tol=1e-9) or math.isclose(
			y_delta, 0.0, abs_tol=1e-9
		) or math.isclose(abs(x_delta), abs(y_delta), abs_tol=1e-9):
			midpoint = (
				(first[0] + second[0]) / 2,
				(first[1] + second[1]) / 2,
			)
			return [first, midpoint, second]

		if abs(x_delta) > abs(y_delta):
			bend = (
				first[0] + math.copysign(abs(y_delta), x_delta),
				second[1],
			)
		else:
			bend = (
				second[0],
				first[1] + math.copysign(abs(x_delta), y_delta),
			)
		return [first, bend, second]

	@staticmethod
	def _offset_path(path: list[Point], offset: float) -> list[Point]:
		if math.isclose(offset, 0.0):
			return path
		if all(first == second for first, second in zip(path, path[1:])):
			return path

		normals = []
		for first, second in zip(path, path[1:]):
			x_delta = second[0] - first[0]
			y_delta = second[1] - first[1]
			length = math.hypot(x_delta, y_delta)
			normals.append((-y_delta / length, x_delta / length))

		offset_points = [
			(
				path[0][0] + normals[0][0] * offset,
				path[0][1] + normals[0][1] * offset,
			)
		]
		for point, first_normal, second_normal in zip(
			path[1:-1], normals, normals[1:]
		):
			miter = (
				first_normal[0] + second_normal[0],
				first_normal[1] + second_normal[1],
			)
			miter_scale = offset / (
				miter[0] * first_normal[0] + miter[1] * first_normal[1]
			)
			offset_points.append(
				(
					point[0] + miter[0] * miter_scale,
					point[1] + miter[1] * miter_scale,
				)
			)
		offset_points.append(
			(
				path[-1][0] + normals[-1][0] * offset,
				path[-1][1] + normals[-1][1] * offset,
			)
		)
		return offset_points

	@staticmethod
	def _edge_key(first: str, second: str) -> Edge:
		return tuple(sorted((first, second)))