import json
import math

from utils_future import Log

log = Log("HBD")


class HBDDesignReadMixin:
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
            log.warning("[design][] must contain origin stops")
            origin_records = {}
        if not isinstance(records, dict):
            log.warning("[design][] must contain routes")
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
            log.warning(f"[design][] could not read design: {error}")
            return {}

    @staticmethod
    def _read_origin_positions(
        origin_records: dict[object, object],
    ) -> dict[str, list[float]]:
        origin_positions = {}
        for name, coordinates in origin_records.items():
            if not isinstance(coordinates, list) or len(coordinates) != 2:
                log.warning(f"[origin stop][{name}] has invalid coordinates")
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
                log.warning(f"[origin stop][{name}] is invalid")
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
        self._circle_routes: dict[str, tuple[float, float, float, bool]] = {}
        route_records = {
            str(route_id): record for route_id, record in records.items()
        }
        fitted_records = {
            route_id: self._parse_fitted_shape(str(route_id), sequence)
            for route_id, sequence in route_records.items()
        }
        self._fitted_circle_routes = {
            route_id: radii
            for route_id, (_, radii, is_fitted) in fitted_records.items()
            if is_fitted
        }
        for route_id, sequence in route_records.items():
            if route_id not in routes_by_id:
                log.warning(
                    f"[design route][] route {route_id!r} does not exist"
                )
                continue
            designed_stops = routes_by_id[route_id].stops
            sequence = fitted_records[route_id][0]
            segments_by_route[route_id] = self._read_route_segments(
                route_id, sequence, designed_stops
            )
            designed_stops_by_route[route_id] = designed_stops
        return segments_by_route, designed_stops_by_route

    def _read_route_segments(
        self,
        route_id: str,
        sequence: object,
        designed_stops: list[str],
    ) -> list[dict[str, object]]:
        circle = self._parse_circle(route_id, sequence)
        if circle is not None:
            if designed_stops[0] != designed_stops[-1]:
                raise ValueError(
                    f"Harry Beck route {route_id} circle must be closed"
                )
            self._circle_routes[route_id] = circle
            return self._segments_from_circle(designed_stops)
        if (
            route_id in self._fitted_circle_routes
            and designed_stops[0] != designed_stops[-1]
        ):
            raise ValueError(
                f"Harry Beck route {route_id} fitted shape must be closed"
            )
        directions = self._parse_directions(
            route_id, sequence, len(designed_stops) - 1
        )
        return self._segments_from_directions(
            route_id, designed_stops, directions
        )
