from agent.geo.geofence import haversine_m


def test_same_point_is_zero():
    assert haversine_m(50.45, 30.46, 50.45, 30.46) == 0
