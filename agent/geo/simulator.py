import time
from shared.models import GeoEvidence
from .geofence import haversine_m

FACILITY = {"id": "FACILITY_A", "lat": 50.4500, "lon": 30.4600, "radius_m": 5000.0}


def collect_geo_evidence(lat: float = 50.4505, lon: float = 30.4610) -> GeoEvidence:
    now = int(time.time())
    distance = haversine_m(lat, lon, FACILITY["lat"], FACILITY["lon"])
    return GeoEvidence(
        mode="simulated",
        lat=lat,
        lon=lon,
        accuracy_m=5.0,
        timestamp=now,
        facility_id=FACILITY["id"],
        distance_m=round(distance, 2),
        inside=distance <= FACILITY["radius_m"],
        fresh=True,
    )
