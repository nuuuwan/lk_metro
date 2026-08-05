import json
import math
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import ClassVar

from .GeographicDiagram import Point
from .ParallelGeographicDiagram import ParallelGeographicDiagram
from .Route import Route
from .Stop import Stop


class HarryBeckDiagram(ParallelGeographicDiagram):
	DATA_FILE: ClassVar[str] = "harry_beck.json"
	UNIT_SCALE: ClassVar[float] = 4.0
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
		super().__init__(routes, stops)
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
		self.stops = [stop for stop in stops if stop.name in designed_stop_names]
		self._route_order = {
			route.id: index for index, route in enumerate(self.routes)
		}
		self._edge_directions = {}
		self._edge_routes = self._build_edge_routes()

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
		min_x = min(point[0] for point in projected.values())
		max_x = max(point[0] for point in projected.values())
		min_y = min(point[1] for point in projected.values())
		max_y = max(point[1] for point in projected.values())
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
		with self.design_path.open(encoding="utf-8") as file:
			design = json.load(file)
		origin_records = design.get("origin_stops") if isinstance(design, dict) else None
		records = design.get("routes") if isinstance(design, dict) else None
		if not isinstance(origin_records, list) or not origin_records:
			raise ValueError("Harry Beck design must contain origin stops")
		if not isinstance(records, list):
			raise ValueError("Harry Beck design must contain a route list")

		routes_by_id = {route.id: route for route in self.routes}
		stop_names = {stop.name for stop in self.stops}
		origin_positions = {}
		for record in origin_records:
			if not isinstance(record, dict):
				raise ValueError("Harry Beck design contains an invalid origin stop")
			name = record.get("name")
			x_coordinate = record.get("x")
			y_coordinate = record.get("y")
			if (
				name not in stop_names
				or isinstance(x_coordinate, bool)
				or not isinstance(x_coordinate, (int, float))
				or isinstance(y_coordinate, bool)
				or not isinstance(y_coordinate, (int, float))
				or not math.isfinite(x_coordinate)
				or not math.isfinite(y_coordinate)
			):
				raise ValueError("Harry Beck design contains an invalid origin stop")
			if name in origin_positions:
				raise ValueError(f"Harry Beck design repeats origin stop {name!r}")
			origin_positions[name] = [float(x_coordinate), float(y_coordinate)]

		segments_by_route = {}
		designed_stops_by_route = {}
		for record in records:
			if not isinstance(record, dict) or record.get("id") not in routes_by_id:
				raise ValueError("Harry Beck design contains an invalid route")
			route_id = record["id"]
			if route_id in segments_by_route:
				raise ValueError(f"Harry Beck design repeats route {route_id}")
			segments = record.get("segments")
			if not isinstance(segments, list) or not segments:
				raise ValueError(f"Harry Beck route {route_id} has no segments")

			reconstructed_stops = []
			for index, segment in enumerate(segments):
				if not isinstance(segment, dict):
					raise ValueError(f"Harry Beck route {route_id} has an invalid segment")
				direction = segment.get("direction")
				stops = segment.get("stops")
				if direction not in self.DIRECTIONS:
					raise ValueError(
						f"Harry Beck route {route_id} segment {index} has an invalid direction"
					)
				if (
					not isinstance(stops, list)
					or len(stops) < 2
					or not all(isinstance(stop, str) for stop in stops)
				):
					raise ValueError(
						f"Harry Beck route {route_id} segment {index} has invalid stops"
					)
				reconstructed_stops.extend(stops if index == 0 else stops[1:])
				if index > 0 and stops[0] != reconstructed_stops[-len(stops)]:
					raise ValueError(
						f"Harry Beck route {route_id} segments are not connected"
					)

			route_stops = routes_by_id[route_id].stops
			try:
				start_index = route_stops.index(reconstructed_stops[0])
			except ValueError as error:
				raise ValueError(
					f"Harry Beck route {route_id} contains an unknown stop"
				) from error
			if route_stops[start_index : start_index + len(reconstructed_stops)] != reconstructed_stops:
				raise ValueError(
					f"Harry Beck route {route_id} stops are not a contiguous route section"
				)
			segments_by_route[route_id] = segments
			designed_stops_by_route[route_id] = reconstructed_stops

		if not segments_by_route:
			raise ValueError("Harry Beck design must contain at least one route")
		return origin_positions, segments_by_route, designed_stops_by_route

	@classmethod
	def _project_positions(
		cls,
		origin_positions: dict[str, list[float]],
		design_routes: list[dict[str, object]],
	) -> dict[str, list[float]]:
		constraints: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
		for route in design_routes:
			for segment in route["segments"]:
				direction_index = cls.DIRECTIONS.index(segment["direction"])
				x_delta, y_delta = cls.DIRECTION_VECTORS[direction_index]
				for first, second in zip(segment["stops"], segment["stops"][1:]):
					constraints[first].append((second, x_delta, y_delta))
					constraints[second].append((first, -x_delta, -y_delta))

		projected = {
			name: point[:] for name, point in origin_positions.items()
		}
		queue = deque(projected)
		while queue:
			first = queue.popleft()
			first_x, first_y = projected[first]
			for second, x_delta, y_delta in constraints[first]:
				expected = [first_x + x_delta, first_y + y_delta]
				if second not in projected:
					projected[second] = expected
					queue.append(second)
				elif projected[second] != expected:
					raise ValueError(
						f"Harry Beck unit steps conflict at {second!r}"
					)
		designed_stops = set(constraints)
		if set(projected) != designed_stops:
			missing_stops = sorted(designed_stops - set(projected))
			raise ValueError(
				"Harry Beck stops are not connected to an origin: "
				+ ", ".join(missing_stops)
			)
		return projected

	def _grid_svg_lines(self) -> list[str]:
		return []