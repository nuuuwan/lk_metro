import json
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar


class StopXYMixin:
	DATA_FILE: ClassVar[str]
	XY_DATA_FILE: ClassVar[str] = "stops.xy.json"
	OVERLAPS_DATA_FILE: ClassVar[str] = "overlaps.json"
	XY_WIDTH: ClassVar[int] = 100
	XY_HEIGHT: ClassVar[int] = 100
	XY_PADDING: ClassVar[int] = 12

	@classmethod
	def generate_xy(cls) -> None:
		data_dir = Path(__file__).resolve().parents[2] / "data"
		stops_path = data_dir / cls.DATA_FILE
		xy_path = data_dir / cls.XY_DATA_FILE
		overlaps_path = data_dir / cls.OVERLAPS_DATA_FILE
		with stops_path.open(encoding="utf-8") as file:
			records = json.load(file)

		longitude_ranks = cls._dense_ranks(
			record["latlng"][1] for record in records
		)
		latitude_ranks = cls._dense_ranks(
			record["latlng"][0] for record in records
		)

		xy_records = [
			{
				"name": record["name"],
				"xy": [
					cls._rank_to_coordinate(
						longitude_ranks[record["latlng"][1]],
						len(longitude_ranks),
						cls.XY_WIDTH,
					),
					cls._rank_to_coordinate(
						len(latitude_ranks) - 1
						- latitude_ranks[record["latlng"][0]],
						len(latitude_ranks),
						cls.XY_HEIGHT,
					),
				],
			}
			for record in records
		]
		xy_path.write_text(
			json.dumps(xy_records, indent=2) + "\n",
			encoding="utf-8",
		)

		stops_by_xy: dict[tuple[int, int], list[str]] = {}
		for record in xy_records:
			coordinate = tuple(record["xy"])
			stops_by_xy.setdefault(coordinate, []).append(record["name"])
		overlaps = [
			{"xy": list(coordinate), "stops": stop_names}
			for coordinate, stop_names in stops_by_xy.items()
			if len(stop_names) > 1
		]
		overlaps_path.write_text(
			json.dumps(overlaps, indent=2) + "\n",
			encoding="utf-8",
		)

	@staticmethod
	def _dense_ranks(values: Iterable[float]) -> dict[float, int]:
		return {
			value: rank
			for rank, value in enumerate(sorted(set(values)))
		}

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