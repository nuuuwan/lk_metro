import json
import math
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

		projected = {
			record["name"]: (
				math.radians(record["latlng"][1]),
				math.log(
					math.tan(
						math.pi / 4 + math.radians(record["latlng"][0]) / 2
					)
				),
			)
			for record in records
		}
		min_x = min(point[0] for point in projected.values())
		max_x = max(point[0] for point in projected.values())
		min_y = min(point[1] for point in projected.values())
		max_y = max(point[1] for point in projected.values())
		x_range = max_x - min_x
		y_range = max_y - min_y
		scale = min(
			(cls.XY_WIDTH - cls.XY_PADDING * 2) / x_range,
			(cls.XY_HEIGHT - cls.XY_PADDING * 2) / y_range,
		)
		content_width = x_range * scale
		content_height = y_range * scale
		x_offset = (cls.XY_WIDTH - content_width) / 2
		y_offset = (cls.XY_HEIGHT - content_height) / 2

		xy_records = [
			{
				"name": name,
				"xy": [
					int(round(x_offset + (point[0] - min_x) * scale, 0)),
					int(round(y_offset + (max_y - point[1]) * scale, 0)),
				],
			}
			for name, point in projected.items()
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