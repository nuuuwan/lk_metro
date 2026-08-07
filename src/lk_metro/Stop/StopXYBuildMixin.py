from collections.abc import Iterable


class StopXYBuildMixin:
    @classmethod
    def _xy_records(
        cls,
        records: list[dict[str, object]],
        longitude_ranks: dict[float, int],
        latitude_ranks: dict[float, int],
    ) -> list[dict[str, object]]:
        return [
            {
                "name": record["name"],
                "xy": [
                    cls._rank_to_coordinate(
                        longitude_ranks[record["latlng"][1]],
                        len(longitude_ranks),
                        cls.XY_WIDTH,
                    ),
                    cls._rank_to_coordinate(
                        len(latitude_ranks)
                        - 1
                        - latitude_ranks[record["latlng"][0]],
                        len(latitude_ranks),
                        cls.XY_HEIGHT,
                    ),
                ],
            }
            for record in records
        ]

    @staticmethod
    def _overlap_records(
        xy_records: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        stops_by_xy: dict[tuple[int, int], list[str]] = {}
        for record in xy_records:
            coordinate = tuple(record["xy"])
            stops_by_xy.setdefault(coordinate, []).append(record["name"])
        return [
            {"xy": list(coordinate), "stops": stop_names}
            for coordinate, stop_names in stops_by_xy.items()
            if len(stop_names) > 1
        ]

    @staticmethod
    def _dense_ranks(values: Iterable[float]) -> dict[float, int]:
        return {value: rank for rank, value in enumerate(sorted(set(values)))}

    @classmethod
    def _rank_to_coordinate(
        cls,
        rank: int,
        rank_count: int,
        dimension: int,
    ) -> int:
        if rank_count == 1:
            return dimension // 2
        usable_size = dimension - cls.XY_PADDING * 2
        return round(cls.XY_PADDING + rank * usable_size / (rank_count - 1))
