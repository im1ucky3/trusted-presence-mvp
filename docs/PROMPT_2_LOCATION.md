# Person 2 — GEO + UWB Location

You are implementing the location/presence module of a one-day cybersecurity MVP called TrustedPresence.

Repository contract: your ownership is `agent/geo/` and `agent/uwb/`. Do not redesign the server. `shared/models.py` is the fixed data contract.

## Today’s goal
Deliver working macro-location and indoor-presence logic with simulation first, designed so real hardware can replace the simulator later without changing the API.

## GEO tasks
1. Keep/finish Haversine geofence calculation.
2. Check radius, timestamp freshness, and accuracy threshold.
3. Implement test cases: inside 5 km, outside 5 km, stale timestamp, unacceptable accuracy.
4. Optional zero-cost real input: accept coordinates from a phone/manual JSON source. Do not pretend phone coordinates are cryptographically trusted GNSS.

## UWB tasks
1. Keep 5 simulated anchors A–E with configured `(x,y)` positions.
2. Support server-selected random witness set, usually 3 of 5.
3. Return `anchor`, `distance_m`, `quality`, timestamp.
4. Add realistic configurable noise.
5. Implement simple position/inside-room decision. If time permits, implement least-squares trilateration; otherwise preserve the known simulated tag position for the demo and clearly label it.
6. Create an adapter interface so later `UwbSerialAdapter` can replace `UwbSimulator`.
7. Tests: valid room presence, tag outside room, missing witness, bad/low-quality range.

## Interfaces to preserve
`collect_geo_evidence(...) -> GeoEvidence`
`collect_uwb_evidence(witnesses: list[str], ...) -> UWBEvidence`

## Priority order
A. Stable simulator and tests.
B. Correct geofence/freshness logic.
C. Random 3-of-5 witness compatibility.
D. Trilateration only if A–C are finished.

## Git workflow
Work only on branch `feature/location`. Do not edit TPM/server code unless an agreed interface bug requires it.

At the end, provide: changed files, exact run commands, demo inputs for INSIDE/OUTSIDE, and known limitations.
