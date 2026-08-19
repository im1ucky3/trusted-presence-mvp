from agent.geo.geofence import haversine_m
from agent.geo.simulator import collect_geo_evidence


def test_same_point_is_zero():
    assert haversine_m(50.45, 30.46, 50.45, 30.46) == 0


def test_coordinate_inside_5km():
    evidence = collect_geo_evidence(
        lat=50.49,
        lon=30.46,
    )

    assert evidence.distance_m < 5000
    assert evidence.inside is True
    assert evidence.fresh is True


def test_coordinate_outside_5km():
    evidence = collect_geo_evidence(
        lat=50.50,
        lon=30.46,
    )

    assert evidence.distance_m > 5000
    assert evidence.inside is False


def test_stale_coordinate_is_not_fresh():
    evidence = collect_geo_evidence(
        lat=50.45,
        lon=30.46,
        timestamp=900,
        now=1000,
        max_age_s=30,
    )

    assert evidence.fresh is False


def test_bad_accuracy_is_rejected():
    evidence = collect_geo_evidence(
        lat=50.45,
        lon=30.46,
        accuracy_m=200.0,
        max_accuracy_m=50.0,
    )

    assert evidence.inside is False
