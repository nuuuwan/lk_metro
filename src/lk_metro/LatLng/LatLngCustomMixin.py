from typing import Self


class LatLngCustomMixin:
    CUSTOM_LATLNG = {
        "Anderson Flats": (6.890321583694404, 79.8730423696894),
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
        "Maharagama Cargills": (6.8497, 79.9261),
        "Malabe Bus Stand": (6.9036, 79.9547),
        "Near Lalanka Head Office": (6.8833, 79.8750),
        "Panadura Hospital": (6.7139, 79.9078),
        "Peliyagoda (New Kelani Bridge)": (6.9589, 79.8794),
        "Piliyandala Bus Stand Stop": (6.8017, 79.9228),
        "Rathmalana Tec": (6.8206, 79.8833),
        "Royal Institute Bus Stop": (6.8839, 79.8661),
        "Singer Mega - Colombo 8": (6.9133, 79.8775),
        "Thalahena Junction": (6.9083, 79.9389),
        "Thalawathugoda": (6.8778, 79.9306),
        "Town Hall - Vision Care": (6.9158, 79.8625),
        "VTA": (6.8856, 79.8731),
        "Wellawaththa": (6.8738, 79.8610),
    }

    @classmethod
    def from_name(cls, name: str) -> Self:
        name = name.strip()
        if not name:
            raise ValueError("name must not be empty")
        if name in cls.CUSTOM_LATLNG:
            lat, lng = cls.CUSTOM_LATLNG[name]
            return cls(lat=lat, lng=lng)
        cache_key = " ".join(name.casefold().split())
        cache = cls._read_cache()
        cached_location = cls._location_from_cache(cache, cache_key)
        if cached_location is not None:
            return cached_location
        query_name = f"{name}, Sri Lanka"
        location = cls._fetch_location(query_name)
        cache[cache_key] = {"lat": location.lat, "lng": location.lng}
        cls._write_cache(cache)
        return location
