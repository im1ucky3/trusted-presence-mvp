import math
import random
import time
from collections.abc import Mapping

from shared.models import UWBEvidence, UWBRange

from .base import UwbAdapter

ANCHORS = {
    "A": (0.0, 0.0),
    "B": (6.0, 0.0),
    "C": (0.0, 5.0),
    "D": (6.0, 5.0),
    "E": (3.0, 5.0),
}

ROOM = (0.0, 0.0, 6.0, 5.0)

WITNESS_COUNT = 3
MIN_QUALITY = 0.50
MAX_MEASUREMENT_AGE_S = 5


class UwbSimulator(UwbAdapter):

    def __init__(
        self,
        *,
        tag: tuple[float, float] = (2.7, 3.1),
        noise_m: float = 0.03,
        quality: float | Mapping[str, float] = 0.95,
        timestamp: int | None = None,
        min_quality: float = MIN_QUALITY,
        max_age_s: int = MAX_MEASUREMENT_AGE_S,
        now: int | None = None,
    ):
        self.tag = tag
        self.noise_m = noise_m
        self.quality = quality
        self.timestamp = timestamp
        self.min_quality = min_quality
        self.max_age_s = max_age_s
        self.now = now

    def _quality_for(
        self,
        anchor: str,
    ) -> float:

        if isinstance(self.quality, Mapping):
            if anchor not in self.quality:
                raise ValueError(f"missing quality for anchor {anchor}")

            value = float(self.quality[anchor])

        else:
            value = float(self.quality)

        if not 0 <= value <= 1:
            raise ValueError("quality must be between 0 and 1")

        return value

    @staticmethod
    def _validate_witnesses(
        witnesses: list[str],
    ):

        if len(witnesses) != WITNESS_COUNT:
            raise ValueError("exactly 3 witnesses are required")

        if len(set(witnesses)) != WITNESS_COUNT:
            raise ValueError("witnesses must be unique")

        for anchor in witnesses:
            if anchor not in ANCHORS:
                raise ValueError(f"unknown UWB witness: {anchor}")

    def collect(
        self,
        witnesses: list[str],
    ) -> UWBEvidence:

        self._validate_witnesses(witnesses)

        current_time = int(time.time()) if self.now is None else int(self.now)

        sample_time = current_time if self.timestamp is None else int(self.timestamp)

        age_s = current_time - sample_time

        fresh = 0 <= age_s <= self.max_age_s

        ranges: list[UWBRange] = []

        all_quality_ok = True

        for anchor in witnesses:

            ax, ay = ANCHORS[anchor]

            exact_distance = math.hypot(
                self.tag[0] - ax,
                self.tag[1] - ay,
            )

            noise = random.uniform(
                -self.noise_m,
                self.noise_m,
            )

            measured_distance = max(
                0.0,
                exact_distance + noise,
            )

            quality = self._quality_for(anchor)

            if quality < self.min_quality:
                all_quality_ok = False

            ranges.append(
                UWBRange(
                    anchor=anchor,
                    distance_m=round(
                        measured_distance,
                        3,
                    ),
                    quality=quality,
                )
            )

        x1, y1, x2, y2 = ROOM

        geometrically_inside = x1 <= self.tag[0] <= x2 and y1 <= self.tag[1] <= y2

        inside = geometrically_inside and fresh and all_quality_ok

        return UWBEvidence(
            mode="simulated",
            witnesses=list(witnesses),
            ranges=ranges,
            # MVP:
            # position is taken from the known
            # simulated tag position.
            # Real hardware can later replace this
            # with trilateration.
            position_x=self.tag[0],
            position_y=self.tag[1],
            inside=inside,
            timestamp=sample_time,
        )


def collect_uwb_evidence(
    witnesses: list[str],
    *,
    adapter: UwbAdapter | None = None,
    tag: tuple[float, float] = (2.7, 3.1),
    noise_m: float = 0.03,
    quality: float | Mapping[str, float] = 0.95,
    timestamp: int | None = None,
    min_quality: float = MIN_QUALITY,
    max_age_s: int = MAX_MEASUREMENT_AGE_S,
    now: int | None = None,
) -> UWBEvidence:

    if adapter is None:
        adapter = UwbSimulator(
            tag=tag,
            noise_m=noise_m,
            quality=quality,
            timestamp=timestamp,
            min_quality=min_quality,
            max_age_s=max_age_s,
            now=now,
        )

    return adapter.collect(witnesses)
