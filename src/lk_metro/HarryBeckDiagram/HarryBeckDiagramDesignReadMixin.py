import json
import math

from utils_future import Log

log = Log("HarryBeckDiagram")


class HarryBeckDiagramDesignReadMixin:
    def _read_design(
        self,
    ) -> tuple[
        dict[str, list[float]],
        dict[str, list[dict[str, object]]],
        dict[str, list[str]],
    ]:
        design = self._load_design()
        origin_records = (
            design.get("origin_stops") if isinstance(design, dict) else None
        )
        records = design.get("routes") if isinstance(design, dict) else None
        if not isinstance(origin_records, dict) or not origin_records:
            log.warn("Harry Beck design must contain origin stops")
            origin_records = {}
        if not isinstance(records, dict):
            log.warn("Harry Beck design must contain routes")
            records = {}
        origin_positions = self._read_origin_positions(origin_records)
        segments, designed_stops = self._read_design_routes(records)
        return self._with_design_fallbacks(
            origin_positions, segments, designed_stops
        )

    def _load_design(self) -> object:
        try:
            with self.design_path.open(encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            log.warn(f"Could not read Harry Beck design: {error}")
            return {}

    @staticmethod
    def _read_origin_positions(
        origin_records: dict[object, object],
    ) -> dict[str, list[float]]:
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
            origin_positions[name] = [
                float(x_coordinate),
                float(y_coordinate),
            ]
        return origin_positions

    def _read_design_routes(
        self,
        records: dict[object, object],
    ) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[str]]]:
        routes_by_id = {route.id: route for route in self.routes}
        segments_by_route = {}
        designed_stops_by_route = {}
        for route_id, sequence in records.items():
            if route_id not in routes_by_id:
                log.warn(f"Harry Beck route {route_id!r} does not exist")
                continue
            designed_stops = routes_by_id[route_id].stops
            directions = self._parse_directions(
                route_id, sequence, len(designed_stops) - 1
            )
            segments_by_route[route_id] = self._segments_from_directions(
                route_id, designed_stops, directions
            )
            designed_stops_by_route[route_id] = designed_stops
        return segments_by_route, designed_stops_by_route
