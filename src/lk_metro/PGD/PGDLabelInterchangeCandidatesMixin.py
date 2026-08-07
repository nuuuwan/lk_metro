import math

from lk_metro.GD.Point import Point
from lk_metro.PGD._PlacementContext import _PlacementContext
from lk_metro.PGD.PGDTypes import Bounds


class PGDLabelInterchangeCandidatesMixin:
    def _interchange_candidates(
        self,
        position: Point,
    ) -> list[tuple[float, float, str, Point]]:
        x_coordinate, y_coordinate = position
        base_offset = self.INTERCHANGE_RADIUS + self.LABEL_OFFSET
        candidates = []
        for extra in range(0, 25, 2):
            for x_direction, y_direction in self.LABEL_DIRECTIONS:
                length = math.hypot(x_direction, y_direction)
                x_direction /= length
                y_direction /= length
                text_direction = x_direction
                if math.isclose(x_direction, 0.0):
                    text_direction = (
                        -1.0 if x_coordinate > self.width / 2 else 1.0
                    )
                candidates.append(
                    (
                        x_coordinate + x_direction * (base_offset + extra),
                        y_coordinate + y_direction * (base_offset + extra),
                        "start" if text_direction > 0 else "end",
                        (text_direction, 0.0),
                    )
                )
        return candidates

    def _label_score(
        self,
        bounds: Bounds,
        context: _PlacementContext,
    ) -> tuple[float, float, float]:
        return (
            self._outside_area(bounds, context.canvas_bounds),
            sum(
                self._overlap_area(bounds, other)
                for other in context.occupied
            ),
            sum(
                self._overlap_area(bounds, route)
                for route in context.route_bounds
            ),
        )
