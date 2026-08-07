import json
from pathlib import Path


class StopReadMixin:
    @classmethod
    def read_all(cls) -> list["Stop"]:
        data_dir = Path(__file__).resolve().parents[3] / "data"
        stops_path = data_dir / cls.DATA_FILE
        xy_path = data_dir / cls.XY_DATA_FILE
        with stops_path.open(encoding="utf-8") as file:
            stop_records = json.load(file)
        with xy_path.open(encoding="utf-8") as file:
            xy_records = json.load(file)
        if not isinstance(stop_records, list):
            raise ValueError(f"Expected a JSON list in {stops_path}")
        if not isinstance(xy_records, list):
            raise ValueError(f"Expected a JSON list in {xy_path}")
        coordinates_by_name = cls._coordinates_by_name(xy_records, xy_path)
        stops = cls._stops_from_records(
            stop_records, coordinates_by_name, stops_path
        )
        if coordinates_by_name:
            unknown_names = ", ".join(sorted(coordinates_by_name))
            raise ValueError(
                f"Coordinates reference unknown stops: {unknown_names}"
            )
        return stops

    @staticmethod
    def _coordinates_by_name(
        xy_records: list[object],
        xy_path: Path,
    ) -> dict[str, list[float]]:
        coordinates_by_name: dict[str, list[float]] = {}
        for index, record in enumerate(xy_records):
            if not isinstance(record, dict) or set(record) != {"name", "xy"}:
                raise ValueError(
                    f"Invalid coordinate record at index {index} in {xy_path}"
                )
            name = record["name"]
            if not isinstance(name, str) or name in coordinates_by_name:
                raise ValueError(
                    "Invalid or duplicate stop name "
                    f"at index {index} in {xy_path}"
                )
            coordinates_by_name[name] = record["xy"]
        return coordinates_by_name

    @classmethod
    def _stops_from_records(
        cls,
        stop_records: list[object],
        coordinates_by_name: dict[str, list[float]],
        stops_path: Path,
    ) -> list["Stop"]:
        stops = []
        for index, record in enumerate(stop_records):
            if not isinstance(record, dict) or set(record) != {
                "name",
                "latlng",
            }:
                raise ValueError(
                    f"Invalid stop record at index {index} in {stops_path}"
                )
            name = record["name"]
            if name not in coordinates_by_name:
                raise ValueError(f"Missing coordinates for stop {name!r}")
            stops.append(cls(**record, xy=coordinates_by_name.pop(name)))
        return stops
