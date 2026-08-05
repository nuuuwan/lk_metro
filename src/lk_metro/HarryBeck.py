import html
import json
import math
from collections import deque
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
		regenerate_design: bool = False,
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
		if regenerate_design:
			self.origin, self.segments = self._generate_design()
			self.segments = self._segments_by_route_order(self.segments)
			self.write_design()
		else:
			self.origin, self.segments = self._read_design()

	def layout(self) -> dict[str, Point]:
		positions: dict[str, Point] = {self.origin: (0.0, 0.0)}
		occupied: dict[Point, str] = {(0.0, 0.0): self.origin}
		pending = list(enumerate(self.segments))

		while pending:
			remaining = []
			for index, segment in pending:
				anchor = segment.stations[0]
				if anchor not in positions:
					remaining.append((index, segment))
					continue

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

			if len(remaining) == len(pending):
				anchors = ", ".join(
					segment.stations[0] for _, segment in remaining
				)
				raise ValueError(
					"Design contains segments with unreachable anchors: " + anchors
				)
			pending = remaining

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

		for route in self.routes:
			for path in paths[route.id]:
				points = " ".join(
					f"{x},{y}" for x, y in (svg_point(point) for point in path)
				)
				lines.append(
					f'<polyline class="route" points="{points}" '
					f'stroke="{route.color}" stroke-width="12"/>'
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

	def write_design(self) -> Path:
		segments_by_route = {route.id: [] for route in self.routes}
		for segment in self.segments:
			segments_by_route[self._segment_route_id(segment)].append(
				{
					"orientation": segment.orientation,
					"stations": list(segment.stations),
				}
			)
		design = {
			"origin": self.origin,
			"routes": [
				{
					"id": route.id,
					"name": route.name,
					"segments": segments_by_route[route.id],
				}
				for route in self.routes
			],
		}
		self.design_path.parent.mkdir(parents=True, exist_ok=True)
		self.design_path.write_text(
			json.dumps(design, indent=2) + "\n",
			encoding="utf-8",
		)
		return self.design_path

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
		invalid_colors = [route.id for route in self.routes if not self._is_hex_color(route.color)]
		if invalid_colors:
			raise ValueError(
				"Routes have invalid colors: " + ", ".join(invalid_colors)
			)

	def _read_design(self) -> tuple[str, tuple[HarryBeckSegment, ...]]:
		with self.design_path.open(encoding="utf-8") as file:
			design = json.load(file)

		if not isinstance(design, dict):
			raise ValueError("Harry Beck design must be a JSON object")
		origin = design.get("origin")
		if not isinstance(origin, str) or origin not in self._stops_by_name:
			raise ValueError("Harry Beck design has an invalid origin")
		route_records = design.get("routes")
		if isinstance(route_records, list):
			records = []
			valid_route_ids = {route.id for route in self.routes}
			seen_route_ids = set()
			for route_record in route_records:
				if not isinstance(route_record, dict):
					raise ValueError("Harry Beck route design must be an object")
				route_id = route_record.get("id")
				if route_id not in valid_route_ids or route_id in seen_route_ids:
					raise ValueError("Harry Beck design has an invalid route ID")
				seen_route_ids.add(route_id)
				route_segments = route_record.get("segments")
				if not isinstance(route_segments, list):
					raise ValueError(f"Route {route_id} must contain a segment list")
				records.extend(route_segments)
		else:
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

	def _generate_design(self) -> tuple[str, tuple[HarryBeckSegment, ...]]:
		adjacency = self._build_adjacency()
		origin = self._ordered_stop_names()[0]
		positions: dict[str, Point] = {origin: (0.0, 0.0)}
		occupied: dict[Point, str] = {(0.0, 0.0): origin}
		segments: list[HarryBeckSegment] = []
		queue = deque([origin])

		while queue:
			current = queue.popleft()
			for neighbor in adjacency[current]:
				if neighbor in positions:
					continue
				point, orientation = self._place_neighbor(
					current,
					neighbor,
					positions[current],
					occupied,
				)
				positions[neighbor] = point
				occupied[point] = neighbor
				segments.append(
					HarryBeckSegment(orientation, (current, neighbor))
				)
				queue.append(neighbor)

		missing = sorted(set(self._stops_by_name) - set(positions))
		if missing:
			raise ValueError(
				"Cannot generate one connected Harry Beck design; unreachable stops: "
				+ ", ".join(missing)
			)
		return origin, self._aggregate_segments(segments)

	def _aggregate_segments(
		self,
		segments: list[HarryBeckSegment],
	) -> tuple[HarryBeckSegment, ...]:
		aggregated = list(segments)
		while True:
			for first_index, first in enumerate(aggregated):
				matching_index = next(
					(
						second_index
						for second_index, second in enumerate(aggregated)
						if second_index != first_index
						and second.orientation == first.orientation
						and second.stations[0] == first.stations[-1]
						and self._segment_route_id(second) == self._segment_route_id(first)
					),
					None,
				)
				if matching_index is None:
					continue

				matching = aggregated.pop(matching_index)
				if matching_index < first_index:
					first_index -= 1
				aggregated[first_index] = HarryBeckSegment(
					first.orientation,
					first.stations + matching.stations[1:],
				)
				break
			else:
				return tuple(aggregated)

	def _segment_route_id(self, segment: HarryBeckSegment) -> str:
		first, second = segment.stations[:2]
		for route in self.routes:
			if any(
				{route_first, route_second} == {first, second}
				for route_first, route_second in zip(route.stops, route.stops[1:])
			):
				return route.id
		raise ValueError(
			f"Segment edge {first!r} to {second!r} does not belong to a route"
		)

	def _segments_by_route_order(
		self,
		segments: tuple[HarryBeckSegment, ...],
	) -> tuple[HarryBeckSegment, ...]:
		return tuple(
			segment
			for route in self.routes
			for segment in segments
			if self._segment_route_id(segment) == route.id
		)

	def _ordered_stop_names(self) -> list[str]:
		ordered = list(
			dict.fromkeys(name for route in self.routes for name in route.stops)
		)
		ordered.extend(
			stop.name for stop in self.stops if stop.name not in ordered
		)
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
	) -> tuple[Point, str]:
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
		orientation_by_direction = {
			vector: orientation
			for orientation, vector in self.ORIENTATION_VECTORS.items()
		}

		for distance in range(1, len(self.stops) + 1):
			for index in direction_indexes:
				direction = self.DIRECTIONS[index]
				candidate = (
					round(current[0] + direction[0] * distance, 10),
					round(current[1] + direction[1] * distance, 10),
				)
				if candidate not in occupied:
					if distance != 1:
						raise ValueError(
							f"Cannot encode generated segment from {current_name!r} "
							f"to {neighbor_name!r} with length {distance}"
						)
					return candidate, orientation_by_direction[direction]

		raise RuntimeError(f"Unable to place stop {neighbor_name!r}")

	@classmethod
	def _geographic_direction(cls, first: Stop, second: Stop) -> Point:
		latitude_delta = second.latlng[0] - first.latlng[0]
		longitude_delta = second.latlng[1] - first.latlng[1]
		angle = math.atan2(-latitude_delta, longitude_delta)
		direction_index = round(angle / (math.pi / 4)) % len(cls.DIRECTIONS)
		return cls.DIRECTIONS[direction_index]

	@staticmethod
	def _is_hex_color(color: str) -> bool:
		if len(color) != 7 or not color.startswith("#"):
			return False
		try:
			int(color[1:], 16)
		except ValueError:
			return False
		return True

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