import pytest

from agent.uwb.base import UwbAdapter
from agent.uwb.simulator import (
    UwbSimulator,
    collect_uwb_evidence,
)

WITNESSES = ["B", "D", "E"]


def test_tag_inside_room():

    evidence = collect_uwb_evidence(
        WITNESSES,
        tag=(2.7, 3.1),
        noise_m=0,
    )

    assert evidence.witnesses == WITNESSES

    assert [r.anchor for r in evidence.ranges] == WITNESSES

    assert evidence.inside is True


def test_tag_outside_room():

    evidence = collect_uwb_evidence(
        WITNESSES,
        tag=(8.0, 3.0),
        noise_m=0,
    )

    assert evidence.inside is False


def test_wrong_witness_is_rejected():

    with pytest.raises(
        ValueError,
        match="unknown UWB witness",
    ):

        collect_uwb_evidence(["B", "D", "X"])


def test_missing_witness_is_rejected():

    with pytest.raises(
        ValueError,
        match="exactly 3 witnesses",
    ):

        collect_uwb_evidence(["B", "D"])


def test_low_quality_measurement_is_rejected():

    evidence = collect_uwb_evidence(
        WITNESSES,
        quality={
            "B": 0.95,
            "D": 0.20,
            "E": 0.95,
        },
        noise_m=0,
    )

    assert evidence.inside is False


def test_stale_measurement_is_rejected():

    evidence = collect_uwb_evidence(
        WITNESSES,
        timestamp=990,
        now=1000,
        max_age_s=5,
        noise_m=0,
    )

    assert evidence.inside is False


def test_simulator_implements_uwb_adapter():

    simulator = UwbSimulator()

    assert isinstance(
        simulator,
        UwbAdapter,
    )
