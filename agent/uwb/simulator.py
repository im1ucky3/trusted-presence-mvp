import math
import random
import time
from shared.models import UWBEvidence, UWBRange

ANCHORS = {
    "A": (0.0, 0.0),
    "B": (6.0, 0.0),
    "C": (0.0, 5.0),
    "D": (6.0, 5.0),
    "E": (3.0, 5.0),
}
ROOM = (0.0, 0.0, 6.0, 5.0)


def collect_uwb_evidence(witnesses: list[str], tag=(2.7, 3.1), noise_m: float = 0.03) -> UWBEvidence:
    ranges: list[UWBRange] = []
    for anchor in witnesses:
        ax, ay = ANCHORS[anchor]
        exact = math.hypot(tag[0] - ax, tag[1] - ay)
        measured = max(0.0, exact + random.uniform(-noise_m, noise_m))
        ranges.append(UWBRange(anchor=anchor, distance_m=round(measured, 3), quality=0.95))
    x1, y1, x2, y2 = ROOM
    inside = x1 <= tag[0] <= x2 and y1 <= tag[1] <= y2
    return UWBEvidence(
        mode="simulated",
        witnesses=witnesses,
        ranges=ranges,
        position_x=tag[0],
        position_y=tag[1],
        inside=inside,
        timestamp=int(time.time()),
    )
