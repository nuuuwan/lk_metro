from lk_metro.GeographicDiagram.Point import Point
from lk_metro.ParallelGeographicDiagram.ParallelGeographicDiagramTypes import (
    CandidatePayload, Tick)


class ParallelGeographicDiagramLabelStationCandidatesMixin:
    def _horizontal_candidate_payloads(
        self,
        tick: Tick,
        font_size: float,
        clearance: float,
    ) -> list[CandidatePayload]:
        first, second = tick
        left = min(first[0], second[0])
        right = max(first[0], second[0])
        payloads = []
        outwards = ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))
        for extra in (0.0, font_size * 1.1, font_size * 2.2):
            top = min(first[1], second[1]) - clearance - extra
            bottom = max(first[1], second[1]) + clearance
            bottom += font_size * self.LABEL_BASELINE_COMPENSATION + extra
            anchors = (
                (left, top),
                (right, top),
                (left, bottom),
                (right, bottom),
            )
            payloads.extend(
                (tick, anchor, outward, extra)
                for anchor, outward in zip(anchors, outwards)
            )
        return payloads

    def _rotated_candidate_payloads(
        self,
        tick: Tick,
        position: Point,
        clearance: float,
    ) -> list[CandidatePayload]:
        x_coordinate, y_coordinate = position
        first, second = tick
        mirrored = (
            (2 * x_coordinate - first[0], 2 * y_coordinate - first[1]),
            (2 * x_coordinate - second[0], 2 * y_coordinate - second[1]),
        )
        base_candidates = [tick, mirrored]
        outward = self._outward_tick_payloads(
            base_candidates, position, clearance
        )
        directed = self._direction_payloads(
            base_candidates, position, clearance
        )
        return outward + directed
