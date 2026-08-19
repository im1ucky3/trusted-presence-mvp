import os
import time
from typing import Literal

from shared.models import GeoEvidence
from .geofence import haversine_m

# Default facility.
# Can be overridden through environment variables.
FACILITY = {
    "id": "FACILITY_A",
    "lat": 50.4500,
    "lon": 30.4600,
    "radius_m": 5000.0,
}

MAX_COORDINATE_AGE_S = 30
MAX_ACCURACY_M = 50.0


def get_facility() -> dict:
    """
    Return current facility configuration.

    Environment variables can override the default location:

    TP_FACILITY_ID
    TP_FACILITY_LAT
    TP_FACILITY_LON
    TP_FACILITY_RADIUS_M
    """

    return {
        "id": os.getenv(
            "TP_FACILITY_ID",
            FACILITY["id"],
        ),
        "lat": float(
            os.getenv(
                "TP_FACILITY_LAT",
                str(FACILITY["lat"]),
            )
        ),
        "lon": float(
            os.getenv(
                "TP_FACILITY_LON",
                str(FACILITY["lon"]),
            )
        ),
        "radius_m": float(
            os.getenv(
                "TP_FACILITY_RADIUS_M",
                str(FACILITY["radius_m"]),
            )
        ),
    }


def collect_geo_evidence(
    lat: float = 50.4505,
    lon: float = 30.4610,
    *,
    timestamp: int | None = None,
    accuracy_m: float = 5.0,
    mode: Literal["simulated", "phone", "gnss"] = "simulated",
    max_age_s: int = MAX_COORDINATE_AGE_S,
    max_accuracy_m: float = MAX_ACCURACY_M,
    now: int | None = None,
) -> GeoEvidence:

    if accuracy_m < 0:
        raise ValueError("accuracy_m must be non-negative")

    current_time = int(time.time()) if now is None else int(now)

    sample_time = current_time if timestamp is None else int(timestamp)

    age_s = current_time - sample_time

    fresh = 0 <= age_s <= max_age_s

    facility = get_facility()

    distance = haversine_m(
        lat,
        lon,
        facility["lat"],
        facility["lon"],
    )

    within_radius = distance <= facility["radius_m"]

    accuracy_ok = accuracy_m <= max_accuracy_m

    inside = within_radius and accuracy_ok

    return GeoEvidence(
        mode=mode,
        lat=lat,
        lon=lon,
        accuracy_m=accuracy_m,
        timestamp=sample_time,
        facility_id=facility["id"],
        distance_m=round(distance, 2),
        inside=inside,
        fresh=fresh,
    )
