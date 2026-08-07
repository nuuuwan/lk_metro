import math

from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import CandidatePayload, Tick


class PGDLabelPayloadMixin:
    @staticmethod
    def _outward_tick_payloads(
        base_candidates: list[Tick],
        position: Point,
        clearance: float,
    ) -> list[CandidatePayload]:
        payloads = []
        for extra in range(0, 25, 2):
            for candidate in base_candidates:
                outward = (
                    candidate[1][0] - position[0],
                    candidate[1][1] - position[1],
                )
                outward_length = math.hypot(*outward)
                distance = clearance + extra
                anchor = (
                    candidate[1][0] + outward[0] / outward_length * distance,
                    candidate[1][1] + outward[1] / outward_length * distance,
                )
                payloads.append((candidate, anchor, outward, extra))
        return payloads

    def _direction_payloads(
        self,
        base_candidates: list[Tick],
        position: Point,
        clearance: float,
    ) -> list[CandidatePayload]:
        payloads = []
        for extra in range(0, 25, 2):
            radius = self.ROUTE_STROKE_WIDTH / 2 + self.STATION_TICK_LENGTH
            radius += clearance + extra
            for direction in self.LABEL_DIRECTIONS:
                payloads.append(
                    self._direction_payload(
                        base_candidates,
                        position,
                        direction,
                        radius,
                        extra,
                    )
                )
        return payloads

    @staticmethod
    def _direction_payload(
        base_candidates: list[Tick],
        position: Point,
        direction: Point,
        radius: float,
        extra: float,
    ) -> CandidatePayload:
        length = math.hypot(*direction)
        x_direction = direction[0] / length
        y_direction = direction[1] / length
        candidate = max(
            base_candidates,
            key=lambda tick: (
                (tick[1][0] - position[0]) * x_direction
                + (tick[1][1] - position[1]) * y_direction
            ),
        )
        anchor = (
            position[0] + x_direction * radius,
            position[1] + y_direction * radius,
        )
        return candidate, anchor, (x_direction, y_direction), extra
