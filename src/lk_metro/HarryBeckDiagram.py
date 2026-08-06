import json
import math
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
		if not isinstance(origin_records, dict) or not origin_records:
			raise ValueError("Harry Beck design must contain origin stops")
		if not isinstance(records, dict):
			raise ValueError("Harry Beck design must contain routes")

		routes_by_id = {route.id: route for route in self.routes}
		origin_positions = {}
		for name, coordinates in origin_records.items():
			if not isinstance(coordinates, list) or len(coordinates) != 2:
				raise ValueError("Harry Beck design contains an invalid origin stop")
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
				raise ValueError("Harry Beck design contains an invalid origin stop")
			origin_positions[name] = [float(x_coordinate), float(y_coordinate)]

		segments_by_route = {}
		designed_stops_by_route = {}
		for route_id, segment_records in records.items():
			if route_id not in routes_by_id:
				raise ValueError("Harry Beck design contains an invalid route")
			if route_id in segments_by_route:
				raise ValueError(f"Harry Beck design repeats route {route_id}")
			if not isinstance(segment_records, list) or not segment_records:
				raise ValueError(f"Harry Beck route {route_id} has no segments")
			segments = []
			for index, segment_record in enumerate(segment_records):
				if not isinstance(segment_record, list) or len(segment_record) != 2:
					raise ValueError(
						f"Harry Beck route {route_id} segment {index} is invalid"
					)
				direction, stops = segment_record
				segments.append({"direction": direction, "stops": stops})

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
			designed_stops = []
			for segment in segments:
				for stop in segment["stops"]:
					if stop not in designed_stops:
						designed_stops.append(stop)
			segments_by_route[route_id] = segments
			designed_stops_by_route[route_id] = designed_stops

		if not segments_by_route:
			raise ValueError("Harry Beck design must contain at least one route")
		return origin_positions, segments_by_route, designed_stops_by_route

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

	@classmethod
	def _project_positions(
		cls,
		origin_positions: dict[str, list[float]],
		design_routes: list[dict[str, object]],
	) -> dict[str, list[float]]:
		pending_segments = []
		for route in design_routes:
			for segment in route["segments"]:
				direction_index = cls.DIRECTIONS.index(segment["direction"])
				x_delta, y_delta = cls.DIRECTION_VECTORS[direction_index]
				pending_segments.append((segment["stops"], x_delta, y_delta))

		projected = {
			name: point[:] for name, point in origin_positions.items()
		}
		while pending_segments:
			remaining_segments = []
			for stops, x_delta, y_delta in pending_segments:
				anchor_index = next(
					(index for index, stop in enumerate(stops) if stop in projected),
					None,
				)
				if anchor_index is None:
					remaining_segments.append((stops, x_delta, y_delta))
					continue

				anchor_x, anchor_y = projected[stops[anchor_index]]
				for index, stop in enumerate(stops):
					if stop not in projected:
						step_count = index - anchor_index
						projected[stop] = [
							anchor_x + step_count * x_delta,
							anchor_y + step_count * y_delta,
						]
			if len(remaining_segments) == len(pending_segments):
				missing_stops = sorted(
					{stop for stops, _, _ in remaining_segments for stop in stops}
				)
				break
			pending_segments = remaining_segments
		else:
			missing_stops = []

		if missing_stops:
			raise ValueError(
				"Harry Beck stops are not connected to an origin: "
				+ ", ".join(missing_stops)
			)
		return projected

	def _grid_svg_lines(self) -> list[str]:
		lines = ['<g class="coordinate-grid">']
		logical_width = round((self.width - self.padding * 2) / self.UNIT_SCALE)
		logical_height = round((self.height - self.padding * 2) / self.UNIT_SCALE)
		for index in range(logical_width + 1):
			x_coordinate = self.padding + index * self.UNIT_SCALE
			grid_class = "grid-major" if index % 10 == 0 else "grid-minor"
			lines.append(
				f'<line class="{grid_class}" x1="{x_coordinate}" y1="0" '
				f'x2="{x_coordinate}" y2="{self.height}"/>'
			)
		for index in range(logical_height + 1):
			y_coordinate = self.padding + index * self.UNIT_SCALE
			grid_class = "grid-major" if index % 10 == 0 else "grid-minor"
			lines.append(
				f'<line class="{grid_class}" x1="0" y1="{y_coordinate}" '
				f'x2="{self.width}" y2="{y_coordinate}"/>'
			)
		lines.append("</g>")
		return lines