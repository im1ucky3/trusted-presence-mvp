import time

from shared.models import GeoEvidence

from .simulator import (
    collect_geo_evidence,
    MAX_COORDINATE_AGE_S,
    MAX_ACCURACY_M,
)


class PhoneGeoAdapter:
    """
    Real location input from a phone.

    The coordinates are real phone-provided coordinates,
    but they are not treated as cryptographically trusted GNSS.

    Therefore GeoEvidence.mode is always "phone".
    """

    def __init__(
        self,
        *,
        max_age_s: int = MAX_COORDINATE_AGE_S,
        max_accuracy_m: float = MAX_ACCURACY_M,
    ):
        self.max_age_s = max_age_s
        self.max_accuracy_m = max_accuracy_m

    def collect(
        self,
        *,
        lat: float,
        lon: float,
        accuracy_m: float,
        timestamp: int | None = None,
        now: int | None = None,
    ) -> GeoEvidence:

        current_time = int(time.time()) if now is None else int(now)

        sample_time = current_time if timestamp is None else int(timestamp)

        return collect_geo_evidence(
            lat=lat,
            lon=lon,
            timestamp=sample_time,
            accuracy_m=accuracy_m,
            mode="phone",
            max_age_s=self.max_age_s,
            max_accuracy_m=self.max_accuracy_m,
            now=current_time,
        )
