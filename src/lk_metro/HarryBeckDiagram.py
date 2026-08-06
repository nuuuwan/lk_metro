import html
import json
import math
import re
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import ClassVar

from utils_future import Log

from .GeographicDiagram import Point
from .ParallelGeographicDiagram import ParallelGeographicDiagram
from .Route import Route
from .Stop import Stop


log = Log("HarryBeckDiagram")


class HarryBeckDiagram(ParallelGeographicDiagram):
	DATA_FILE: ClassVar[str] = "harry_beck.json"
	UNIT_SCALE: ClassVar[float] = 8.0
	MAP_TITLE = "LANKA METRO"
	LEGEND_TITLE = "Key"
	TITLE_HEIGHT = 12
	LOGO_WIDTH = 36
	LEGEND_WIDTH = 0
	LEGEND_LINE_HEIGHT = 3.5
	LEGEND_FONT_SIZE = 1.55
	TITLE_FONT_SIZE = 3.8
	BACKGROUND_COLOR = "#ffffff"
	TEXT_COLOR = "#991f1d"
	FONT_FAMILY = (
		"'Johnston Sans', 'Johnston 100', Johnston100, 'Gill Sans', sans-serif"
	)
	SHOW_GRID = False
	ROUTE_STROKE_WIDTH = 1.0
	PARALLEL_ROUTE_GAP = 1.0
	INTERCHANGE_RADIUS = 1.014
	INTERCHANGE_STROKE_WIDTH = 0.34
	LABEL_FONT_SIZE = 1.8
	TERMINAL_LABEL_FONT_SIZE = LABEL_FONT_SIZE
	ROUTE_NAME_FONT_SIZE = 3.2
	WARN_LABEL_OVERLAPS = True
	LABEL_OFFSET = 0.95
	LABEL_HALO_WIDTH = 0.2
	STATION_TICK_LENGTH = 0.58
	STATION_TICK_STROKE_WIDTH = 0.42
	ROTATE_LABELS = False
	RIVER_PATH = (
		"M -4,17 L 33,17 L 38,22 L 44,28 L 44,34 L 78,34 "
		"L 98,54 L 160,54"
	)
	ROUTE_NAME_POSITIONS: ClassVar[dict[str, tuple[float, float, float]]] = {
		"CM01": (110.0, 98.5, 0.0),
		"CM02": (126.0, 74.5, 0.0),
		"CM03": (58.0, 26.5, 0.0),
		"CM04": (108.0, 122.5, 0.0),
		"CM05": (94.0, 10.0, 0.0),
		"CM06": (8.5, 82.0, -90.0),
		"CM08": (78.0, 106.5, 0.0),
	}
	DIRECTIONS: ClassVar[tuple[str, ...]] = (
		"E",
		"SE",
		"S",
		"SW",
		"W",
		"NW",
		"N",
		"NE",
	)
	DIRECTION_VECTORS: ClassVar[tuple[tuple[int, int], ...]] = (
		(1, 0),
		(1, 1),
		(0, 1),
		(-1, 1),
		(-1, 0),
		(-1, -1),
		(0, -1),
		(1, -1),
	)

	def __init__(self, routes: list[Route], stops: list[Stop]) -> None:
		super().__init__(
			routes,
			stops,
			parallel_route_gap=self.PARALLEL_ROUTE_GAP,
		)
		self.legend_routes = routes
		self.design_path = (
			Path(__file__).resolve().parents[2] / "data" / self.DATA_FILE
		)
		(
			self._origin_positions,
			self._segments_by_route,
			designed_stops_by_route,
		) = self._read_design()
		routes_by_id = {route.id: route for route in routes}
		self.routes = [
			replace(routes_by_id[route_id], stops=route_stops)
			for route_id, route_stops in designed_stops_by_route.items()
		]
		designed_stop_names = {
			name for route_stops in designed_stops_by_route.values() for name in route_stops
		}
		stops_by_name = {stop.name: stop for stop in stops}
		self.stops = [
			stops_by_name.get(name, Stop(name=name, latlng=[0.0, 0.0], xy=[0.0, 0.0]))
			for name in designed_stop_names
		]
		self._route_order = {
			route.id: index for index, route in enumerate(self.routes)
		}
		self._edge_directions = {}
		self._edge_routes = self._build_design_edge_routes()
		self._stop_numbers = {
			stop.name: [
				str(route.stops.index(stop.name) + 1)
				for route in self.routes
				if stop.name in route.stops
			]
			for stop in self.stops
		}

	def _stop_label(self, stop_name: str) -> str:
		return stop_name

	def _label_lines(self, label: str) -> tuple[str, ...]:
		lines = []
		for word in label.split():
			if lines and len(lines[-1]) + len(word) + 1 <= 12:
				lines[-1] = f"{lines[-1]} {word}"
			else:
				lines.append(word)
		return tuple(lines)

	def _terminal_label_font_size(self) -> float:
		return self.TERMINAL_LABEL_FONT_SIZE

	def _route_name_font_size(self) -> float:
		return self.ROUTE_NAME_FONT_SIZE

	def _route_name_svg_lines(self) -> list[str]:
		routes_by_id = {route.id: route for route in self.routes}
		lines = []
		for route_id, (x, y, angle) in self.ROUTE_NAME_POSITIONS.items():
			route = routes_by_id[route_id]
			transform = f' transform="rotate({angle} {x} {y})"' if angle else ""
			lines.append(
				f'<text class="route-name" x="{x}" y="{y}" '
				f'text-anchor="middle" fill="{route.color}"{transform}>'
				f'{html.escape(route.id)}</text>'
			)
		return lines

	def _route_name_bounds(self) -> list[tuple[str, tuple[float, float, float, float]]]:
		text_width = 4 * self.ROUTE_NAME_FONT_SIZE * 0.6
		half_height = self.ROUTE_NAME_FONT_SIZE * 0.6
		bounds = []
		for route_id, (x, y, angle) in self.ROUTE_NAME_POSITIONS.items():
			half_width = text_width / 2
			if angle:
				half_width, rotated_half_height = half_height, half_width
			else:
				rotated_half_height = half_height
			bounds.append(
				(
					f"route ID {route_id}",
					(
						x - half_width,
						y - rotated_half_height,
						x + half_width,
						y + rotated_half_height,
					),
				)
			)
		return bounds

	def _background_svg_lines(self) -> list[str]:
		return [
			f'<path d="{self.RIVER_PATH}" fill="none" stroke="#66b9d0" '
			'stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>',
			f'<path d="{self.RIVER_PATH}" fill="none" stroke="#d9f1f7" '
			'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>',
			'<text x="58" y="33.6" text-anchor="middle" '
			'font-family="Gill Sans, sans-serif" font-size="0.8" '
			'font-style="italic" fill="#287f98">Kelani River</text>',
		]

	def _svg_dimensions(self) -> tuple[int, int]:
		width, height = super()._svg_dimensions()
		size = max(width, height)
		return size, size

	def _content_offset(self) -> Point:
		width, height = super()._svg_dimensions()
		size = max(width, height)
		return (0.0, (size - height) / 2)

	@property
	def complexity_by_route(self) -> dict[str, int]:
		return {
			route.id: sum(
				index == 0
				or segment["direction"] != segments[index - 1]["direction"]
				for index, segment in enumerate(segments)
			)
			for route in self.routes
			for segments in [self._segments_by_route[route.id]]
		}

	@property
	def complexity(self) -> int:
		return sum(self.complexity_by_route.values())

	def _title_and_legend_svg_lines(self) -> list[str]:
		legend_x, legend_title_y = self._legend_origin()
		lines = [
			self._logo_svg_line(),
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
		note_y = (
			legend_title_y
			+ 6
			+ len(self.legend_routes) * self.LEGEND_LINE_HEIGHT
		)
		note_lines = (
			("Diagrammatic map", True),
			("Routes are simplified so they are easier to follow.", False),
			("Stops and connections are shown, but distances", False),
			("and locations are not drawn to geographic scale.", False),
		)
		lines.extend(
			f'<text class="{("legend-label" if is_heading else "legend-route-label")}" '
			f'x="{legend_x}" y="{note_y + index * 2.4}"'
			f'{" font-weight=\"bold\"" if is_heading else ""}>'
			f'{html.escape(text)}</text>'
			for index, (text, is_heading) in enumerate(note_lines)
		)
		footer_y = self._svg_dimensions()[1] - self._content_offset()[1] - 2
		lines.append(
			f'<text class="legend-route-label" x="{self.padding}" '
			f'y="{footer_y}">Source data: https://lankametro.lk</text>'
		)
		return lines

	def _legend_origin(self) -> Point:
		return (self.width - 44, self.TITLE_HEIGHT + 10)

	def layout(self) -> dict[str, Point]:
		projected = self._project_positions(
			self._origin_positions,
			[
				{
					"id": route.id,
					"name": route.name,
					"segments": self._segments_by_route[route.id],
				}
				for route in self.routes
			],
		)
		self._logical_positions = projected
		self._validate_projected_geometry(projected)
		min_x = min(point[0] for point in projected.values())
		max_x = max(point[0] for point in projected.values())
		min_y = min(point[1] for point in projected.values())
		max_y = max(point[1] for point in projected.values())
		self._grid_min_x = min_x
		self._grid_min_y = min_y
		self.width = math.ceil(
			(max_x - min_x) * self.UNIT_SCALE + self.padding * 2
		)
		self.height = math.ceil(
			(max_y - min_y) * self.UNIT_SCALE + self.padding * 2
		)
		return {
			name: (
				(point[0] - min_x) * self.UNIT_SCALE + self.padding,
				(point[1] - min_y) * self.UNIT_SCALE + self.padding,
			)
			for name, point in projected.items()
		}

	def _validate_projected_geometry(
		self,
		positions: dict[str, list[float]],
	) -> None:
		errors = []
		edges = []
		for route in self.routes:
			for segment in self._segments_by_route[route.id]:
				first, second = segment["stops"]
				edges.append((route.id, first, second))
				x_delta = positions[second][0] - positions[first][0]
				y_delta = positions[second][1] - positions[first][1]
				is_zero_length = math.isclose(x_delta, 0.0) and math.isclose(
					y_delta,
					0.0,
				)
				is_octilinear = (
					not is_zero_length
					and (
						math.isclose(x_delta, 0.0)
						or math.isclose(y_delta, 0.0)
						or math.isclose(abs(x_delta), abs(y_delta))
					)
				)
				if not is_octilinear:
					if is_zero_length:
						geometry_error = "has zero length (angle undefined)"
					else:
						angle = math.degrees(math.atan2(y_delta, x_delta)) % 360
						geometry_error = (
							f"is not a multiple of 45 degrees (angle: {angle:.3f}°)"
						)
					errors.append(
						f"route {route.id} edge "
						f"{self._format_stop_at(first, positions[first])} to "
						f"{self._format_stop_at(second, positions[second])} "
						f"{geometry_error}"
					)

		stops_by_position = defaultdict(list)
		for stop_name, position in positions.items():
			stops_by_position[tuple(position)].append(stop_name)
		for position, stop_names in stops_by_position.items():
			if len(stop_names) > 1:
				errors.append(
					f"stops {', '.join(self._format_stop_at(name, positions[name]) for name in sorted(stop_names))} "
					f"overlap at ({position[0]:g}, {position[1]:g})"
				)

		for index, (first_route, first_start, first_end) in enumerate(edges):
			for second_route, second_start, second_end in edges[index + 1:]:
				if {first_start, first_end} & {second_start, second_end}:
					continue
				intersection = self._proper_segment_intersection(
					positions[first_start],
					positions[first_end],
					positions[second_start],
					positions[second_end],
				)
				if intersection is None:
					continue
				errors.append(
					f"route {first_route} edge "
					f"{self._format_stop_at(first_start, positions[first_start])} to "
					f"{self._format_stop_at(first_end, positions[first_end])} crosses "
					f"route {second_route} edge "
					f"{self._format_stop_at(second_start, positions[second_start])} to "
					f"{self._format_stop_at(second_end, positions[second_end])} at "
					f"({intersection[0]:g}, {intersection[1]:g}) without a shared stop"
				)

		for error in errors:
			log.warn(f"Harry Beck geometry: {error}")

	@staticmethod
	def _proper_segment_intersection(
		first_start: list[float],
		first_end: list[float],
		second_start: list[float],
		second_end: list[float],
	) -> Point | None:
		first_delta = (
			first_end[0] - first_start[0],
			first_end[1] - first_start[1],
		)
		second_delta = (
			second_end[0] - second_start[0],
			second_end[1] - second_start[1],
		)
		denominator = (
			first_delta[0] * second_delta[1]
			- first_delta[1] * second_delta[0]
		)
		if math.isclose(denominator, 0.0):
			return None

		start_delta = (
			second_start[0] - first_start[0],
			second_start[1] - first_start[1],
		)
		first_fraction = (
			start_delta[0] * second_delta[1]
			- start_delta[1] * second_delta[0]
		) / denominator
		second_fraction = (
			start_delta[0] * first_delta[1]
			- start_delta[1] * first_delta[0]
		) / denominator
		if not 0.0 < first_fraction < 1.0 or not 0.0 < second_fraction < 1.0:
			return None
		return (
			first_start[0] + first_fraction * first_delta[0],
			first_start[1] + first_fraction * first_delta[1],
		)

	def route_segments(
		self,
		positions: dict[str, Point] | None = None,
	) -> dict[str, list[list[Point]]]:
		positions = positions or self.layout()
		paths_by_route = {}
		for route in self.routes:
			paths = []
			for segment in self._segments_by_route[route.id]:
				stops = segment["stops"]
				for first, second in zip(stops, stops[1:]):
					edge = self._edge_key(first, second)
					reference_first, reference_second = self._edge_directions[edge]
					is_reference_direction = (
						first == reference_first and second == reference_second
					)
					path = [
						positions[reference_first],
						positions[reference_second],
					]
					route_ids = sorted(
						self._edge_routes[edge],
						key=self._route_order.__getitem__,
					)
					if len(route_ids) > 1:
						offset_index = (
							route_ids.index(route.id) - (len(route_ids) - 1) / 2
						)
						path = self._offset_path(
							path,
							offset_index * self.parallel_route_gap,
						)
					paths.append(
						path if is_reference_direction else list(reversed(path))
					)
			paths_by_route[route.id] = paths
		return paths_by_route

	def _read_design(
		self,
	) -> tuple[
		dict[str, list[float]],
		dict[str, list[dict[str, object]]],
		dict[str, list[str]],
	]:
		try:
			with self.design_path.open(encoding="utf-8") as file:
				design = json.load(file)
		except (OSError, json.JSONDecodeError) as error:
			log.warn(f"Could not read Harry Beck design: {error}")
			design = {}
		origin_records = design.get("origin_stops") if isinstance(design, dict) else None
		records = design.get("routes") if isinstance(design, dict) else None
		if not isinstance(origin_records, dict) or not origin_records:
			log.warn("Harry Beck design must contain origin stops")
			origin_records = {}
		if not isinstance(records, dict):
			log.warn("Harry Beck design must contain routes")
			records = {}

		routes_by_id = {route.id: route for route in self.routes}
		origin_positions = {}
		for name, coordinates in origin_records.items():
			if not isinstance(coordinates, list) or len(coordinates) != 2:
				log.warn(f"Harry Beck origin stop {name!r} is invalid")
				continue
			x_coordinate, y_coordinate = coordinates
			if (
				not isinstance(name, str)
				or not name
				or isinstance(x_coordinate, bool)
				or not isinstance(x_coordinate, (int, float))
				or isinstance(y_coordinate, bool)
				or not isinstance(y_coordinate, (int, float))
				or not math.isfinite(x_coordinate)
				or not math.isfinite(y_coordinate)
			):
				log.warn(f"Harry Beck origin stop {name!r} is invalid")
				continue
			origin_positions[name] = [float(x_coordinate), float(y_coordinate)]

		segments_by_route = {}
		designed_stops_by_route = {}
		for route_id, direction_sequence in records.items():
			if route_id not in routes_by_id:
				log.warn(f"Harry Beck route {route_id!r} does not exist")
				continue

			designed_stops = routes_by_id[route_id].stops
			expected_count = len(designed_stops) - 1
			directions = self._parse_directions(
				route_id,
				direction_sequence,
				expected_count,
			)
			segments = []
			current_stop = designed_stops[0]
			next_stop_index = 1
			blank_index = 0
			for direction, is_blank in directions:
				if is_blank:
					blank_index += 1
					next_stop = f"__blank__:{route_id}:{blank_index}"
				else:
					next_stop = designed_stops[next_stop_index]
					next_stop_index += 1
				segments.append(
					{"direction": direction, "stops": [current_stop, next_stop]}
				)
				current_stop = next_stop
			segments_by_route[route_id] = segments
			designed_stops_by_route[route_id] = designed_stops

		if not segments_by_route:
			log.warn("Harry Beck design must contain at least one valid route")
			fallback_route = self.routes[0]
			designed_stops = fallback_route.stops
			segments_by_route[fallback_route.id] = [
				{"direction": "N", "stops": [first, second]}
				for first, second in zip(designed_stops, designed_stops[1:])
			]
			designed_stops_by_route[fallback_route.id] = designed_stops
		if not origin_positions:
			fallback_origin = next(iter(designed_stops_by_route.values()))[0]
			log.warn(f"Using {fallback_origin!r} as the origin stop")
			origin_positions[fallback_origin] = [0.0, 0.0]
		return origin_positions, segments_by_route, designed_stops_by_route

	def _parse_directions(
		self,
		route_id: str,
		direction_sequence: object,
		expected_count: int,
	) -> list[tuple[str, bool]]:
		directions = []
		if not isinstance(direction_sequence, str) or not direction_sequence:
			raise ValueError(
				f"Harry Beck route {route_id} has no direction sequence"
			)
		else:
			for token in direction_sequence.split("-"):
				match = re.fullmatch(
					r"(\d+)?(b)?(E|SE|S|SW|W|NW|N|NE)", token
				)
				if match is None or int(match.group(1) or 1) == 0:
					raise ValueError(
						f"Harry Beck route {route_id} has invalid direction {token!r}"
					)
				directions.extend(
					[(match.group(3), match.group(2) == "b")]
					* int(match.group(1) or 1)
				)

		direction_count = sum(not is_blank for _, is_blank in directions)
		if direction_count != expected_count:
			raise ValueError(
				f"Harry Beck route {route_id} requires {expected_count} directions, "
				f"but the sequence defines {direction_count}"
			)
		return directions

	def _build_design_edge_routes(self) -> dict[tuple[str, str], list[str]]:
		edge_routes = {}
		for route in self.routes:
			for segment in self._segments_by_route[route.id]:
				for first, second in zip(segment["stops"], segment["stops"][1:]):
					edge = self._edge_key(first, second)
					if edge not in edge_routes:
						edge_routes[edge] = []
						self._edge_directions[edge] = (first, second)
					if route.id not in edge_routes[edge]:
						edge_routes[edge].append(route.id)
		return edge_routes

	def _project_positions(
		self,
		origin_positions: dict[str, list[float]],
		design_routes: list[dict[str, object]],
	) -> dict[str, list[float]]:
		pending_segments = []
		for route in design_routes:
			for segment in route["segments"]:
				direction_index = self.DIRECTIONS.index(segment["direction"])
				x_delta, y_delta = self.DIRECTION_VECTORS[direction_index]
				pending_segments.append(
					(route["id"], segment["stops"], x_delta, y_delta)
				)

		projected = {
			name: point[:] for name, point in origin_positions.items()
		}
		position_routes = {name: set() for name in origin_positions}
		while pending_segments:
			remaining_segments = []
			for route_id, stops, x_delta, y_delta in pending_segments:
				anchor_index = next(
					(index for index, stop in enumerate(stops) if stop in projected),
					None,
				)
				if anchor_index is None:
					remaining_segments.append((route_id, stops, x_delta, y_delta))
					continue

				anchor_x, anchor_y = projected[stops[anchor_index]]
				for index, stop in enumerate(stops):
					step_count = index - anchor_index
					expected = [
						anchor_x + step_count * x_delta,
						anchor_y + step_count * y_delta,
					]
					if stop not in projected:
						projected[stop] = expected
						position_routes[stop] = {route_id}
					elif not all(
						math.isclose(actual, candidate)
						for actual, candidate in zip(projected[stop], expected)
					):
						retained_route_ids = "/".join(
							sorted(position_routes[stop])
						) or "origin"
						log.warn(
							"Harry Beck position conflict: "
							f"{self._format_stop_at(stop, projected[stop])} "
							f"(route {retained_route_ids}) and "
							f"{self._format_stop_at(stop, expected)} (route {route_id})"
						)
					else:
						position_routes[stop].add(route_id)
			if len(remaining_segments) == len(pending_segments):
				first_route_id, first_stops, _, _ = remaining_segments[0]
				fallback_origin = first_stops[0]
				log.warn(
					f"Harry Beck stops are not connected to an origin; "
					f"placing {fallback_origin!r} separately"
				)
				projected[fallback_origin] = [
					max(point[0] for point in projected.values()) + 2.0,
					min(point[1] for point in projected.values()),
				]
				position_routes[fallback_origin] = {first_route_id}
				continue
			pending_segments = remaining_segments
		return projected

	def _format_stop_at(self, stop_name: str, position: list[float]) -> str:
		x_coordinate, y_coordinate = position
		if stop_name.startswith("__blank__:"):
			_, route_id, blank_index = stop_name.split(":")
			return f"[{x_coordinate:g}, {y_coordinate:g}]<blank {route_id}.{blank_index}>"
		return (
			f"[{x_coordinate:g}, {y_coordinate:g}]"
			f"{stop_name} ({'/'.join(self._stop_numbers[stop_name])})"
		)

	def _grid_svg_lines(self) -> list[str]:
		return []