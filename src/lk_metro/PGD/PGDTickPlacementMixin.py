import math

from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Tick
from lk_metro.Route import Route


class PGDTickPlacementMixin:
    def station_ticks(
        self,
        positions: dict[str, Point] | None = None,
        segments: dict[str, list[list[Point]]] | None = None,
        memberships: dict[str, set[str]] | None = None,
    ) -> dict[str, Tick]:
        positions = positions or self.layout()
        segments = segments or self.route_segments(positions)
        memberships = memberships or self._route_memberships()
        routes_by_id = {route.id: route for route in self.routes}
        ticks = {}
        for stop in self.stops:
            if len(memberships[stop.name]) != 1:
                continue
            ticks[stop.name] = self._station_tick_for_stop(
                stop.name,
                positions,
                segments,
                memberships,
                routes_by_id,
            )
        return ticks

    def _station_tick_for_stop(
        self,
        stop_name: str,
        positions: dict[str, Point],
        segments: dict[str, list[list[Point]]],
        memberships: dict[str, set[str]],
        routes_by_id: dict[str, Route],
    ) -> Tick:
        route_id = next(iter(memberships[stop_name]))
        route = routes_by_id[route_id]
        stop_index = route.stops.index(stop_name)
        candidates = self._tick_candidate_segments(
            segments[route_id], stop_index
        )
        first, second = next(
            (
                pair
                for pair in candidates
                if not math.isclose(math.dist(*pair), 0.0)
            ),
            (None, None),
        )
        if first is None or second is None:
            raise ValueError(f"Cannot orient station tick for {stop_name!r}")
        is_terminus = stop_index in (0, len(route.stops) - 1)
        return self._tick_endpoints(
            first, second, positions[stop_name], is_terminus
        )
