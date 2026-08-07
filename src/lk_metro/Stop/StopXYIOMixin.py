import json
from pathlib import Path


class StopXYIOMixin:
    @classmethod
    def generate_xy(cls) -> None:
        data_dir = Path(__file__).resolve().parents[3] / "data"
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
        xy_records = cls._xy_records(records, longitude_ranks, latitude_ranks)
        xy_path.write_text(
            json.dumps(xy_records, indent=2) + "\n", encoding="utf-8"
        )
        overlaps_path.write_text(
            json.dumps(cls._overlap_records(xy_records), indent=2) + "\n",
            encoding="utf-8",
        )
