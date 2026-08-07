import math

from lk_metro.GD.Point import Point


class HBDSegmentIntersectionMixin:
    @staticmethod
    def _proper_segment_intersection(
        first_start: list[float],
        first_end: list[float],
        second_start: list[float],
        second_end: list[float],
    ) -> Point | None:
        first_delta = (
            first_end[0] - first_start[0],
            first_end[1] - first_start[1],
        )
        second_delta = (
            second_end[0] - second_start[0],
            second_end[1] - second_start[1],
        )
        denominator = (
            first_delta[0] * second_delta[1]
            - first_delta[1] * second_delta[0]
        )
        if math.isclose(denominator, 0.0):
            return None
        start_delta = (
            second_start[0] - first_start[0],
            second_start[1] - first_start[1],
        )
        first_fraction = (
            start_delta[0] * second_delta[1]
            - start_delta[1] * second_delta[0]
        ) / denominator
        second_fraction = (
            start_delta[0] * first_delta[1] - start_delta[1] * first_delta[0]
        ) / denominator
        if not 0.0 < first_fraction < 1.0 or not 0.0 < second_fraction < 1.0:
            return None
        return (
            first_start[0] + first_fraction * first_delta[0],
            first_start[1] + first_fraction * first_delta[1],
        )
