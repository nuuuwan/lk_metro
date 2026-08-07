import math

from ..Route import Route
from ..Stop import Stop


class GeographicDiagramValidationMixin:
    def _validate_data(self) -> None:
        self._validate_collection_data()
        self._validate_route_stops()
        for stop in self.stops:
            self._validate_stop_coordinates(stop)

    def _validate_collection_data(self) -> None:
        if not self.routes:
            raise ValueError("At least one route is required")
        if not self.stops:
            raise ValueError("At least one stop is required")
        if len(self._stops_by_name) != len(self.stops):
            raise ValueError("Stop names must be unique")

    def _validate_route_stops(self) -> None:
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

    @staticmethod
    def _validate_stop_coordinates(stop: Stop) -> None:
        if len(stop.latlng) != 2 or any(
            not math.isfinite(coordinate) for coordinate in stop.latlng
        ):
            raise ValueError(
                f"Stop {stop.name!r} must have finite latitude and longitude"
            )
        latitude, longitude = stop.latlng
        if not -85.0 < latitude < 85.0 or not -180.0 <= longitude <= 180.0:
            raise ValueError(
                f"Stop {stop.name!r} has invalid latitude or longitude"
            )
        if len(stop.xy) != 2 or any(
            type(coordinate) not in (int, float)
            or not math.isfinite(coordinate)
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
