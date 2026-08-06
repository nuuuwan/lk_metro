import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from utils_future import Log


log = Log("LatLng")


CUSTOM_LATLNG = {
    "Anderson Flat": (6.890321583694404, 79.8730423696894),
    "Army Hospital Borella": (6.9022, 79.8789),
    "Athurugiriya Hospital": (6.8922, 79.9428),
    "Borella 02 - YMBA": (6.9142, 79.8778),
    "BRC Junction": (6.8937, 79.8631),
    "Bus Stop Infront of Colombo": (6.9344, 79.8428),
    "Cancer Hospital Bus Stop 01": (6.8488, 79.9271),
    "German Tec Angulana": (6.8122, 79.8864),
    "Hekitta Junction": (6.9839, 79.8730),
    "Kalubowila Hospital Stop": (6.8601, 79.8797),
    "Katubedda Junction": (6.7972, 79.8884),
    "Kelaniya Campus": (6.9739, 79.9153),
    "Koralawella": (6.7644, 79.8978),
    "Lake House Bus Stop": (6.9329, 79.8472),
    "Lanka Fiber Fabrica": (6.8833, 79.9167),
    "Mahara Junction": (7.0101, 79.9213),
    "Maharagama Cargills Food City": (6.8497, 79.9261),
    "Malabe Bus Stand": (6.9036, 79.9547),
    "Near Lalanka Head Office": (6.8833, 79.8750),
    "Panadura Base Hospital": (6.7139, 79.9078),
    "Peliyagoda (New Kelani Bridge)": (6.9589, 79.8794),
    "Piliyandala Bus Stand Stop": (6.8017, 79.9228),
    "Rathmalana Tec": (6.8206, 79.8833),
    "Royal Institute Bus Stop": (6.8839, 79.8661),
    "Singer Mega - Colombo 8": (6.9133, 79.8775),
    "Thalahena Junction": (6.9083, 79.9389),
    "Thalawathugoda": (6.8778, 79.9306),
    "Town Hall - Vision Care": (6.9158, 79.8625),
    "VTA / AAT": (6.8856, 79.8731),
    "Wellawaththa": (6.8738, 79.8610),
}


@dataclass
class LatLng:
    lat: float
    lng: float

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "lk_metro/1.0 (https://github.com/nuuuwan/lk_metro)"
    CACHE_FILE = Path(tempfile.gettempdir()) / "lk_metro" / "latlng_cache.json"


    

    @classmethod
    def from_name(cls, name: str) -> "LatLng":
        name = name.strip()
        if not name:
            raise ValueError("name must not be empty")

        if name in CUSTOM_LATLNG:
            lat, lng = CUSTOM_LATLNG[name]
            return cls(lat=lat, lng=lng)

        cache_key = " ".join(name.casefold().split())
        cache = cls._read_cache()
        cached_location = cache.get(cache_key)
        if cached_location is not None:
            try:
                return cls(
                    lat=float(cached_location["lat"]),
                    lng=float(cached_location["lng"]),
                )
            except (KeyError, TypeError, ValueError):
                del cache[cache_key]

        query_name = f"{name}, Sri Lanka"

        query = urlencode({"q": query_name, "format": "jsonv2", "limit": 1})
        request = Request(
            f"{cls.NOMINATIM_URL}?{query}",
            headers={"User-Agent": cls.USER_AGENT},
        )
        with urlopen(request, timeout=15) as response:
            results = json.load(response)

        if not isinstance(results, list) or not results:
            raise ValueError(f"No location found for {query_name!r}")

        try:
            location = cls(
                lat=float(results[0]["lat"]),
                lng=float(results[0]["lon"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Nominatim returned an invalid location") from error

        cache[cache_key] = {"lat": location.lat, "lng": location.lng}
        cls._write_cache(cache)
        return location

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



if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else input("Enter a location name: ")
    latlng = LatLng.from_name(name)
    log.info(f"Location: {name}")
    log.info(f"Latitude: {latlng}")
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={latlng.lat},{latlng.lng}"
    log.info(f"Google Maps URL: {google_maps_url}")
    os.system(f"open -a firefox '{google_maps_url}'") 