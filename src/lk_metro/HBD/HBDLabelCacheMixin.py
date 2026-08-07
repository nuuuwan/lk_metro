import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

from lk_metro.Render.Types import Bounds

LabelPlacement = tuple[float, float, str]
LabelState = tuple[dict[str, LabelPlacement], dict[str, Bounds]]


class HBDLabelCacheMixin:
    LABEL_CACHE_VERSION = 2
    LABEL_CACHE_DIR = Path(tempfile.gettempdir()) / "lk_metro"

    def _label_cache_path(self) -> Path:
        digest = hashlib.sha256(self.design_path.read_bytes()).hexdigest()
        return self.LABEL_CACHE_DIR / f"hbd_labels_{digest}.json"

    def _load_cached_stop_labels(self) -> bool:
        try:
            with self._label_cache_path().open(encoding="utf-8") as file:
                payload = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False
        state = self._parse_label_cache(payload)
        if state is None:
            return False
        self._stop_label_placements, self._stop_label_bounds_by_name = state
        self._stop_label_bounds = list(
            self._stop_label_bounds_by_name.values()
        )
        return True

    def _parse_label_cache(self, payload: object) -> LabelState | None:
        if not isinstance(payload, dict) or (
            payload.get("version") != self.LABEL_CACHE_VERSION
        ):
            return None
        placements = self._parse_cached_placements(payload.get("placements"))
        bounds = self._parse_cached_bounds(payload.get("bounds"))
        expected = {stop.name for stop in self.stops}
        if (
            placements is None
            or bounds is None
            or set(placements) != expected
            or set(bounds) != expected
        ):
            return None
        return placements, bounds

    @classmethod
    def _parse_cached_placements(
        cls, records: object
    ) -> dict[str, LabelPlacement] | None:
        if not isinstance(records, dict):
            return None
        parsed = {}
        for name, record in records.items():
            if not (
                isinstance(name, str)
                and cls._valid_record(record, 3)
                and record[2] in ("start", "middle", "end")
            ):
                return None
            parsed[name] = (float(record[0]), float(record[1]), record[2])
        return parsed

    @classmethod
    def _parse_cached_bounds(cls, records: object) -> dict[str, Bounds] | None:
        if not isinstance(records, dict):
            return None
        parsed = {}
        for name, record in records.items():
            if not isinstance(name, str) or not cls._valid_record(record, 4):
                return None
            parsed[name] = tuple(map(float, record))
        return parsed

    @staticmethod
    def _valid_record(record: object, length: int) -> bool:
        if not isinstance(record, list) or len(record) != length:
            return False
        values = record if length == 4 else record[:2]
        return all(
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            for value in values
        )

    def _write_cached_stop_labels(self) -> None:
        path = self._label_cache_path()
        payload = {
            "version": self.LABEL_CACHE_VERSION,
            "placements": self._stop_label_placements,
            "bounds": self._stop_label_bounds_by_name,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}."
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2, sort_keys=True)
                file.write("\n")
            os.replace(temporary_name, path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
