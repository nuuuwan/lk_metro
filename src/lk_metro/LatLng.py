import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class LatLng:
    lat: float
    lng: float

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "lk_metro/1.0 (https://github.com/nuuuwan/lk_metro)"

    @classmethod
    def from_name(cls, name: str) -> "LatLng":
        name = name.strip()
        if not name:
            raise ValueError("name must not be empty")

        name = f'{name}, Sri Lanka'

        query = urlencode({"q": name, "format": "jsonv2", "limit": 1})
        request = Request(
            f"{cls.NOMINATIM_URL}?{query}",
            headers={"User-Agent": cls.USER_AGENT},
        )
        with urlopen(request, timeout=15) as response:
            results = json.load(response)

        if not isinstance(results, list) or not results:
            raise ValueError(f"No location found for {name!r}")

        try:
            return cls(lat=float(results[0]["lat"]), lng=float(results[0]["lon"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Nominatim returned an invalid location") from error



if __name__ == "__main__":
    import sys
    import os
    name = sys.argv[1] if len(sys.argv) > 1 else input("Enter a location name: ")
    latlng = LatLng.from_name(name)
    print(f"Location: {name}")
    print(f"Latitude: {latlng}")
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={latlng.lat},{latlng.lng}"
    print(f"Google Maps URL: {google_maps_url}")
    os.system(f"open '{google_maps_url}'") 