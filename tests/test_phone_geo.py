from agent.geo.phone_adapter import PhoneGeoAdapter


def test_phone_location_is_marked_as_phone():

    adapter = PhoneGeoAdapter()

    evidence = adapter.collect(
        lat=50.45,
        lon=30.46,
        accuracy_m=5.0,
        timestamp=1000,
        now=1000,
    )

    assert evidence.mode == "phone"
    assert evidence.fresh is True
    assert evidence.inside is True


def test_phone_bad_accuracy_is_rejected():

    adapter = PhoneGeoAdapter()

    evidence = adapter.collect(
        lat=50.45,
        lon=30.46,
        accuracy_m=200.0,
        timestamp=1000,
        now=1000,
    )

    assert evidence.mode == "phone"
    assert evidence.inside is False
