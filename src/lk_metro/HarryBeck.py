import html
import math
from collections import deque
from pathlib import Path

from .Route import Route
from .Stop import Stop


Point = tuple[float, float]


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

	def __init__(
		self,
		routes: list[Route],
		stops: list[Stop],
		spacing: int = 80,
	) -> None:
		if spacing <= 0:
			raise ValueError("spacing must be positive")

		self.routes = routes
		self.stops = stops
		self.spacing = spacing
		self._stops_by_name = {stop.name: stop for stop in stops}
		self._validate_data()

	def layout(self) -> dict[str, Point]:
		adjacency = self._build_adjacency()
		positions: dict[str, Point] = {}
		occupied: dict[Point, str] = {}
		component_origin_x = 0.0

		for root in self._ordered_stop_names():
			if root in positions:
				continue

			positions[root] = (component_origin_x, 0)
			occupied[(component_origin_x, 0)] = root
			queue = deque([root])

			while queue:
				current = queue.popleft()
				for neighbor in adjacency[current]:
					if neighbor in positions:
						continue

					position = self._place_neighbor(
						current,
						neighbor,
						positions[current],
						occupied,
					)
					positions[neighbor] = position
					occupied[position] = neighbor
					queue.append(neighbor)

			component_origin_x = max(point[0] for point in positions.values()) + 4

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

	def _ordered_stop_names(self) -> list[str]:
		ordered = list(dict.fromkeys(name for route in self.routes for name in route.stops))
		ordered.extend(stop.name for stop in self.stops if stop.name not in ordered)
		return ordered

	def _build_adjacency(self) -> dict[str, list[str]]:
		adjacency = {stop.name: [] for stop in self.stops}
		for route in self.routes:
			for first, second in zip(route.stops, route.stops[1:]):
				if second not in adjacency[first]:
					adjacency[first].append(second)
				if first not in adjacency[second]:
					adjacency[second].append(first)
		return adjacency

	def _place_neighbor(
		self,
		current_name: str,
		neighbor_name: str,
		current: Point,
		occupied: dict[Point, str],
	) -> Point:
		preferred_direction = self._geographic_direction(
			self._stops_by_name[current_name],
			self._stops_by_name[neighbor_name],
		)
		preferred_index = self.DIRECTIONS.index(preferred_direction)
		direction_indexes = sorted(
			range(len(self.DIRECTIONS)),
			key=lambda index: min(
				(index - preferred_index) % len(self.DIRECTIONS),
				(preferred_index - index) % len(self.DIRECTIONS),
			),
		)

		for distance in range(1, len(self.stops) + 1):
			for index in direction_indexes:
				direction = self.DIRECTIONS[index]
				candidate = (
					round(current[0] + direction[0] * distance, 10),
					round(current[1] + direction[1] * distance, 10),
				)
				if candidate not in occupied:
					return candidate

		raise RuntimeError(f"Unable to place stop {neighbor_name}")

	@staticmethod
	def _geographic_direction(first: Stop, second: Stop) -> Point:
		latitude_delta = second.latlng[0] - first.latlng[0]
		longitude_delta = second.latlng[1] - first.latlng[1]
		angle = math.atan2(-latitude_delta, longitude_delta)
		direction_index = round(angle / (math.pi / 4)) % 8
		return HarryBeck.DIRECTIONS[direction_index]

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