from dataclasses import dataclass

from .LatLngCacheMixin import LatLngCacheMixin
from .LatLngCustomMixin import LatLngCustomMixin
from .LatLngFetchMixin import LatLngFetchMixin


@dataclass
class LatLng(LatLngCacheMixin, LatLngCustomMixin, LatLngFetchMixin):
    lat: float
    lng: float
