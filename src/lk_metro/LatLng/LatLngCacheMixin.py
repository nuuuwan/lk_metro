import json
import os
import tempfile
from pathlib import Path


class LatLngCacheMixin:
    CACHE_FILE = (
        Path(tempfile.gettempdir()) / "lk_metro" / "latlng_cache.json"
    )

    @classmethod
    def _location_from_cache(
        cls,
        cache: dict[str, dict[str, float]],
        cache_key: str,
    ) -> "LatLng | None":
        cached_location = cache.get(cache_key)
        if cached_location is None:
            return None
        try:
            return cls(
                lat=float(cached_location["lat"]),
                lng=float(cached_location["lng"]),
            )
        except (KeyError, TypeError, ValueError):
            del cache[cache_key]
            return None

    @classmethod
    def _read_cache(cls) -> dict[str, dict[str, float]]:
        try:
            with cls.CACHE_FILE.open(encoding="utf-8") as file:
                cache = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        return cache if isinstance(cache, dict) else {}

    @classmethod
    def _write_cache(cls, cache: dict[str, dict[str, float]]) -> None:
        cls.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=cls.CACHE_FILE.parent,
            prefix=f".{cls.CACHE_FILE.name}.",
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=2, sort_keys=True)
                file.write("\n")
            os.replace(temporary_name, cls.CACHE_FILE)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
