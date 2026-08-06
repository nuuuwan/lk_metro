import html
import math
from pathlib import Path

from utils_future import Log

from .DiagramStyle import (
	INTERCHANGE_RADIUS,
	INTERCHANGE_STROKE_WIDTH,
	PARALLEL_ROUTE_GAP,
	STATION_TICK_LENGTH,
	STATION_TICK_STROKE_WIDTH,
)
from .GeographicDiagram import GeographicDiagram, Point
from .Route import Route
from .Stop import Stop


Edge = tuple[str, str]
Bounds = tuple[float, float, float, float]


log = Log("ParallelGeographicDiagram")


class ParallelGeographicDiagram(GeographicDiagram):
	MAP_SUBTITLE = "PARALLEL GEOGRAPHIC MAP"
	DESCRIPTION_LINES = (
		"Routes follow the geographic positions of their stops,",
		"with shared corridors separated for clarity.",
	)
	STATION_TICK_LENGTH = STATION_TICK_LENGTH
	STATION_TICK_STROKE_WIDTH = STATION_TICK_STROKE_WIDTH
	ROUTE_CURVE_RADIUS = 1.5
	ROTATE_LABELS = True
	WARN_LABEL_OVERLAPS = False
	LABEL_BASELINE_COMPENSATION = 0.25
	LABEL_DIRECTIONS = (
		(1.0, 0.0),
		(1.0, 1.0),
		(0.0, 1.0),
		(-1.0, 1.0),
		(-1.0, 0.0),
		(-1.0, -1.0),
		(0.0, -1.0),
		(1.0, -1.0),
	)

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
			f".terminal-label {{ font-size: {self._terminal_label_font_size()}px; "
			"font-weight: bold; }",
			f".route-name {{ font: bold {self._route_name_font_size()}px "
			f"{self.FONT_FAMILY}; paint-order: stroke fill; stroke: white; "
			"stroke-width: 0.7; stroke-linejoin: round; }",
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
			*self._background_svg_lines(),
			*(self._grid_svg_lines() if self.SHOW_GRID else []),
		]

		for route in self.routes:
			path_data = self._route_path_data(segments[route.id])
			lines.append(
				f'<path class="route" d="{path_data}" stroke="{route.color}" '
				f'stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
			)
		lines.extend(self._route_name_svg_lines())

		memberships = self._route_memberships()
		route_colors = {route.id: route.color for route in self.routes}
		station_ticks = self.station_ticks(positions, segments, memberships)
		for stop in self.stops:
			x, y = positions[stop.name]
			if len(memberships[stop.name]) > 1:
				lines.append(
					f'<circle class="interchange" cx="{x}" cy="{y}" '
					f'r="{self.INTERCHANGE_RADIUS}"/>'
				)
				label_x, label_y, text_anchor = self._interchange_label_positions[
					stop.name
				]
				label_transform = ""
			else:
				first, second = station_ticks[stop.name]
				route_id = next(iter(memberships[stop.name]))
				lines.append(
					f'<line class="station" x1="{first[0]}" y1="{first[1]}" '
					f'x2="{second[0]}" y2="{second[1]}" '
					f'stroke="{route_colors[route_id]}"/>'
				)
				label_x, label_y = self._station_label_positions[stop.name]
				tick_angle = math.degrees(
					math.atan2(second[1] - first[1], second[0] - first[0])
				)
				if self.ROTATE_LABELS:
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
				else:
					text_anchor = self._station_label_text_anchors[stop.name]
					label_transform = ""
			label_lines = self._label_lines(self._stop_label(stop.name))
			label_font_size = self._label_font_size(stop.name)
			line_height = label_font_size * 1.05
			first_line_offset = -(len(label_lines) - 1) * line_height / 2
			label_class = (
				"label terminal-label"
				if self._is_terminus(stop.name)
				else "label"
			)
			lines.append(
				f'<text class="{label_class}" x="{label_x}" y="{label_y}" '
				f'text-anchor="{text_anchor}"{label_transform}>'
				+ "".join(
					f'<tspan x="{label_x}" dy="'
					f'{first_line_offset if index == 0 else line_height}">'
					f'{html.escape(label_line)}</tspan>'
					for index, label_line in enumerate(label_lines)
				)
				+ "</text>"
			)

		lines.extend(
			["</g>", *self._title_and_legend_svg_lines(), "</g>", "</svg>"]
		)
		return "\n".join(lines) + "\n"

	def _background_svg_lines(self) -> list[str]:
		return []

	def _route_name_svg_lines(self) -> list[str]:
		return []

	def _route_name_bounds(self) -> list[tuple[str, Bounds]]:
		return []

	def _route_name_font_size(self) -> float:
		return self.LABEL_FONT_SIZE

	def _terminal_label_font_size(self) -> float:
		return self.LABEL_FONT_SIZE

	def _is_terminus(self, stop_name: str) -> bool:
		return any(
			stop_name in (route.stops[0], route.stops[-1])
			for route in self.routes
		)

	def _label_font_size(self, stop_name: str) -> float:
		return (
			self._terminal_label_font_size()
			if self._is_terminus(stop_name)
			else self.LABEL_FONT_SIZE
		)

	def _route_path_data(
		self,
		segments: list[list[Point]],
	) -> str:
		points = []
		for segment in segments:
			if points and points[-1] != segment[0]:
				points.append(
					(
						(points[-1][0] + segment[0][0]) / 2,
						(points[-1][1] + segment[0][1]) / 2,
					)
				)
			for point in segment:
				if not points or point != points[-1]:
					points.append(point)
		return self._rounded_path_data(points)

	def _rounded_path_data(self, points: list[Point]) -> str:
		commands = [f"M {points[0][0]},{points[0][1]}"]
		for previous, point, following in zip(points, points[1:], points[2:]):
			incoming = (previous[0] - point[0], previous[1] - point[1])
			outgoing = (following[0] - point[0], following[1] - point[1])
			incoming_length = math.hypot(*incoming)
			outgoing_length = math.hypot(*outgoing)
			cross_product = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
			if math.isclose(cross_product, 0.0, abs_tol=1e-9):
				commands.append(f"L {point[0]},{point[1]}")
				continue
			radius = min(
				self.ROUTE_CURVE_RADIUS,
				incoming_length / 2,
				outgoing_length / 2,
			)
			entry = (
				point[0] + incoming[0] / incoming_length * radius,
				point[1] + incoming[1] / incoming_length * radius,
			)
			exit_point = (
				point[0] + outgoing[0] / outgoing_length * radius,
				point[1] + outgoing[1] / outgoing_length * radius,
			)
			commands.extend(
				(
					f"L {entry[0]},{entry[1]}",
					f"Q {point[0]},{point[1]} {exit_point[0]},{exit_point[1]}",
				)
			)
		commands.append(f"L {points[-1][0]},{points[-1][1]}")
		return " ".join(commands)

	def _stop_label(self, stop_name: str) -> str:
		return stop_name

	def _label_lines(self, label: str) -> tuple[str, ...]:
		return (label,)

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
			x_offset = x_normal * self.STATION_TICK_LENGTH
			y_offset = y_normal * self.STATION_TICK_LENGTH
			if x_offset - y_offset < 0:
				x_normal = -x_normal
				y_normal = -y_normal
				x_offset = -x_offset
				y_offset = -y_offset
			x, y = positions[stop.name]
			outer = (
				x + x_normal * self.ROUTE_STROKE_WIDTH / 2 + x_offset,
				y + y_normal * self.ROUTE_STROKE_WIDTH / 2 + y_offset,
			)
			is_terminus = stop_index in (0, len(route.stops) - 1)
			inner = (
				(2 * x - outer[0], 2 * y - outer[1])
				if is_terminus
				else (x, y)
			)
			ticks[stop.name] = (inner, outer)

		return self._avoid_label_overlaps(
			positions,
			ticks,
			memberships,
			segments,
		)

	def _avoid_label_overlaps(
		self,
		positions: dict[str, Point],
		ticks: dict[str, tuple[Point, Point]],
		memberships: dict[str, set[str]],
		segments: dict[str, list[list[Point]]],
	) -> dict[str, tuple[Point, Point]]:
		placed_labels = self._route_name_bounds()
		occupied = [bounds for _, bounds in placed_labels]
		route_margin = self.ROUTE_STROKE_WIDTH / 2 + 0.15
		route_bounds = [
			(
				min(first[0], second[0]) - route_margin,
				min(first[1], second[1]) - route_margin,
				max(first[0], second[0]) + route_margin,
				max(first[1], second[1]) + route_margin,
			)
			for route_segments in segments.values()
			for path in route_segments
			for first, second in zip(path, path[1:])
		]
		canvas_bounds = (0.0, 0.0, float(self.width), float(self.height))

		def score(
			bounds: tuple[float, float, float, float],
		) -> tuple[float, float, float]:
			return (
				self._outside_area(bounds, canvas_bounds),
				sum(self._overlap_area(bounds, other) for other in occupied),
				sum(self._overlap_area(bounds, route) for route in route_bounds),
			)

		self._interchange_label_positions = {}
		for stop in sorted(
			(stop for stop in self.stops if len(memberships[stop.name]) > 1),
			key=lambda stop: (positions[stop.name][1], positions[stop.name][0]),
		):
			x, y = positions[stop.name]
			base_offset = self.INTERCHANGE_RADIUS + self.LABEL_OFFSET
			candidates = []
			for extra in range(0, 25, 2):
				for x_direction, y_direction in self.LABEL_DIRECTIONS:
					length = math.hypot(x_direction, y_direction)
					x_direction /= length
					y_direction /= length
					text_direction = (
						x_direction
						if not math.isclose(x_direction, 0.0)
						else (-1.0 if x > self.width / 2 else 1.0)
					)
					candidates.append(
						(
							x + x_direction * (base_offset + extra),
							y + y_direction * (base_offset + extra),
							"start" if text_direction > 0 else "end",
							(text_direction, 0.0),
						)
					)
			candidate_bounds = [
				self._label_bounds(
					(candidate[0], candidate[1]),
					self._stop_label(stop.name),
					candidate[3],
					self._label_font_size(stop.name),
				)
				for candidate in candidates
			]
			scores = [score(bounds) for bounds in candidate_bounds]
			selected_index = min(range(len(candidates)), key=scores.__getitem__)
			selected = candidates[selected_index]
			self._interchange_label_positions[stop.name] = selected[:3]
			occupied.append(candidate_bounds[selected_index])
			placed_labels.append(
				(stop.name, candidate_bounds[selected_index])
			)
		selected_ticks = {}
		self._station_label_positions = {}
		self._station_label_text_anchors = {}
		fixed_bounds = list(occupied)
		route_label_side_counts = {
			route.id: {"above": 0, "below": 0} for route in self.routes
		}
		label_options = {}
		selected_indices = {}

		def station_score(
			bounds: tuple[float, float, float, float],
		) -> tuple[float, float, float]:
			return (
				self._outside_area(bounds, canvas_bounds),
				sum(self._overlap_area(bounds, fixed) for fixed in fixed_bounds),
				sum(
					self._overlap_area(bounds, other)
					for other in occupied[len(fixed_bounds) :]
				),
			)

		for stop in sorted(
			(stop for stop in self.stops if stop.name in ticks),
			key=lambda stop: (
				-max(map(len, self._label_lines(self._stop_label(stop.name)))),
				positions[stop.name][1],
				positions[stop.name][0],
			),
		):
			x, y = positions[stop.name]
			first, second = ticks[stop.name]
			mirrored = (
				(2 * x - first[0], 2 * y - first[1]),
				(2 * x - second[0], 2 * y - second[1]),
			)
			base_candidates = [ticks[stop.name], mirrored]
			font_size = self._label_font_size(stop.name)
			label_clearance = self._label_half_height(
				self._stop_label(stop.name),
				font_size,
			) + 0.2
			candidate_outwards = []
			candidate_extra_distances = []
			if not self.ROTATE_LABELS:
				left = min(first[0], second[0])
				right = max(first[0], second[0])
				candidates = []
				candidate_anchors = []
				for extra_distance in (0.0, font_size * 1.1, font_size * 2.2):
					top = (
						min(first[1], second[1])
						- label_clearance
						- extra_distance
					)
					bottom = (
						max(first[1], second[1])
						+ label_clearance
						+ font_size * self.LABEL_BASELINE_COMPENSATION
						+ extra_distance
					)
					candidates.extend([ticks[stop.name]] * 4)
					candidate_anchors.extend(
						[(left, top), (right, top), (left, bottom), (right, bottom)]
					)
					candidate_outwards.extend(
						[(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)]
					)
					candidate_extra_distances.extend([extra_distance] * 4)
			else:
				candidates = []
				candidate_anchors = []
				for extra in range(0, 25, 2):
					for candidate in base_candidates:
						candidates.append(candidate)
						outward_x = candidate[1][0] - x
						outward_y = candidate[1][1] - y
						outward_length = math.hypot(outward_x, outward_y)
						clearance = label_clearance + extra
						candidate_anchors.append(
							(
								candidate[1][0]
								+ outward_x / outward_length * clearance,
								candidate[1][1]
								+ outward_y / outward_length * clearance,
							)
						)
						candidate_outwards.append(
							(outward_x, outward_y)
						)
						candidate_extra_distances.append(extra)
				for extra in range(0, 25, 2):
					radius = (
						self.ROUTE_STROKE_WIDTH / 2
						+ self.STATION_TICK_LENGTH
						+ label_clearance
						+ extra
					)
					for x_direction, y_direction in self.LABEL_DIRECTIONS:
						direction_length = math.hypot(x_direction, y_direction)
						x_direction /= direction_length
						y_direction /= direction_length
						candidate = max(
							base_candidates,
							key=lambda tick: (
								(tick[1][0] - x) * x_direction
								+ (tick[1][1] - y) * y_direction
							),
						)
						candidates.append(candidate)
						candidate_anchors.append(
							(
								x + x_direction * radius,
								y + y_direction * radius,
							)
						)
						candidate_outwards.append(
							(x_direction, y_direction)
						)
						candidate_extra_distances.append(extra)
			candidate_bounds = [
				self._label_bounds(
					anchor,
					self._stop_label(stop.name),
					outward,
					font_size,
				)
				for anchor, outward in zip(candidate_anchors, candidate_outwards)
			]
			route_id = next(iter(memberships[stop.name]))
			scores = [
				station_score(bounds)
				+ (
					extra_distance,
					route_label_side_counts[route_id][
						"above" if outward[1] < 0 else "below"
					]
					if not self.ROTATE_LABELS
					else 0,
					sum(
						self._overlap_area(bounds, route)
						for route in route_bounds
					),
				)
				for bounds, outward, extra_distance in zip(
					candidate_bounds,
					candidate_outwards,
					candidate_extra_distances,
				)
			]
			selected_index = min(range(len(candidates)), key=scores.__getitem__)
			label_options[stop.name] = list(
				zip(
					candidate_bounds,
					zip(
						candidates,
						candidate_anchors,
						candidate_outwards,
						candidate_extra_distances,
					),
				)
			)
			selected_indices[stop.name] = selected_index
			if not self.ROTATE_LABELS:
				selected_side = (
					"above"
					if candidate_outwards[selected_index][1] < 0
					else "below"
				)
				route_label_side_counts[route_id][selected_side] += 1
			selected_ticks[stop.name] = candidates[selected_index]
			self._station_label_positions[stop.name] = candidate_anchors[
				selected_index
			]
			self._station_label_text_anchors[stop.name] = (
				"end" if candidate_outwards[selected_index][0] < 0 else "start"
			)
			occupied.append(candidate_bounds[selected_index])
			placed_labels.append(
				(stop.name, candidate_bounds[selected_index])
			)
		if not self.ROTATE_LABELS:
			label_names = list(label_options)
			for pass_index in range(4):
				ordered_names = (
					label_names if pass_index % 2 == 0 else reversed(label_names)
				)
				for stop_name in ordered_names:
					route_id = next(iter(memberships[stop_name]))
					other_bounds = [
						label_options[name][selected_indices[name]][0]
						for name in label_names
						if name != stop_name
					]
					candidate_scores = [
						(
							self._outside_area(bounds, canvas_bounds),
							sum(
								self._overlap_area(bounds, fixed)
								for fixed in fixed_bounds
							),
							sum(
								self._overlap_area(bounds, other)
								for other in other_bounds
							),
							payload[3],
							route_label_side_counts[route_id][
								"above" if payload[2][1] < 0 else "below"
							],
							sum(
								self._overlap_area(bounds, route)
								for route in route_bounds
							),
						)
						for bounds, payload in label_options[stop_name]
					]
					selected_indices[stop_name] = min(
						range(len(candidate_scores)),
						key=candidate_scores.__getitem__,
					)
			placed_labels = placed_labels[: len(fixed_bounds)]
			for stop_name, options in label_options.items():
				bounds, payload = options[selected_indices[stop_name]]
				selected_tick, label_position, outward, _ = payload
				selected_ticks[stop_name] = selected_tick
				self._station_label_positions[stop_name] = label_position
				self._station_label_text_anchors[stop_name] = (
					"end" if outward[0] < 0 else "start"
				)
				placed_labels.append((stop_name, bounds))
		if self.WARN_LABEL_OVERLAPS:
			self._warn_label_overlaps(placed_labels)
		return selected_ticks

	def _warn_label_overlaps(
		self,
		placed_labels: list[tuple[str, Bounds]],
	) -> None:
		for index, (first_name, first_bounds) in enumerate(placed_labels):
			for second_name, second_bounds in placed_labels[index + 1 :]:
				overlap = self._overlap_area(first_bounds, second_bounds)
				if overlap > 0.01:
					log.warn(
						"Label overlap: "
						f"{first_name!r} overlaps {second_name!r} "
						f"by {overlap:.2f} square units"
					)

	def _label_bounds(
		self,
		anchor: Point,
		label: str,
		outward: Point,
		font_size: float,
	) -> tuple[float, float, float, float]:
		label_lines = self._label_lines(label)
		text_width = max(
			font_size,
			max(map(len, label_lines)) * font_size * 0.52,
		)
		half_height = self._label_half_height(label, font_size)
		if not self.ROTATE_LABELS:
			if outward[0] < 0:
				return (
					anchor[0] - text_width,
					anchor[1] - half_height,
					anchor[0],
					anchor[1] + half_height,
				)
			return (
				anchor[0],
				anchor[1] - half_height,
				anchor[0] + text_width,
				anchor[1] + half_height,
			)
		length = math.hypot(*outward)
		x_direction = outward[0] / length
		y_direction = outward[1] / length
		x_normal = -y_direction
		y_normal = x_direction
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

	def _label_half_height(self, label: str, font_size: float) -> float:
		return font_size * (
			0.6 + (len(self._label_lines(label)) - 1) * 1.05 / 2
		)

	@staticmethod
	def _overlap_area(
		first: tuple[float, float, float, float],
		second: tuple[float, float, float, float],
	) -> float:
		width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
		height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
		return width * height

	@classmethod
	def _outside_area(
		cls,
		bounds: tuple[float, float, float, float],
		container: tuple[float, float, float, float],
	) -> float:
		area = max(0.0, bounds[2] - bounds[0]) * max(
			0.0, bounds[3] - bounds[1]
		)
		return area - cls._overlap_area(bounds, container)

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