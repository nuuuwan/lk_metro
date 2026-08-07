import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class LatLngFetchMixin:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "lk_metro/1.0 (https://github.com/nuuuwan/lk_metro)"

    @classmethod
    def _fetch_location(cls, query_name: str) -> "LatLng":
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
            return cls(
                lat=float(results[0]["lat"]), lng=float(results[0]["lon"])
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "Nominatim returned an invalid location"
            ) from error
