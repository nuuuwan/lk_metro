from dataclasses import dataclass

from lk_metro.LatLng.LatLngCacheMixin import LatLngCacheMixin
from lk_metro.LatLng.LatLngCustomMixin import LatLngCustomMixin
from lk_metro.LatLng.LatLngFetchMixin import LatLngFetchMixin


@dataclass
class LatLng(LatLngCacheMixin, LatLngCustomMixin, LatLngFetchMixin):
    lat: float
    lng: float
