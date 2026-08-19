import time

from fastapi.testclient import TestClient

from agent.geo.simulator import collect_geo_evidence
from agent.tpm.simulator import collect_tpm_evidence
from agent.uwb.simulator import collect_uwb_evidence
from server.main import create_app
from server.models import ReasonCode
from shared.models import Challenge, PresenceEvidence

DEVICE = "ASUS-G16-TEST"


def build_evidence(challenge: Challenge) -> PresenceEvidence:
    return PresenceEvidence(
        device_id=challenge.device_id,
        session_id=challenge.session_id,
        epoch=challenge.epoch,
        nonce=challenge.nonce,
        timestamp=int(time.time()),
        tpm=collect_tpm_evidence(challenge.nonce),
        geo=collect_geo_evidence(),
        uwb=collect_uwb_evidence(challenge.witnesses),
    )


def fresh_client() -> TestClient:
    return TestClient(create_app())


def test_valid_flow_and_replay_rejected():
    client = fresh_client()
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    evidence = build_evidence(challenge)

    first = client.post("/evidence", json=evidence.model_dump())
    replay = client.post("/evidence", json=evidence.model_dump())

    assert first.status_code == 200
    assert first.json()["trusted"] is True
    assert first.json()["reasons"] == []
    assert replay.status_code == 200
    assert replay.json()["trusted"] is False
    assert replay.json()["reasons"] == [ReasonCode.REPLAY.value]


def test_422_does_not_consume_challenge():
    client = fresh_client()
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())

    malformed = {
        "device_id": challenge.device_id,
        "session_id": challenge.session_id,
        "epoch": challenge.epoch,
        "nonce": challenge.nonce,
    }
    invalid = client.post("/evidence", json=malformed)
    valid = client.post("/evidence", json=build_evidence(challenge).model_dump())

    assert invalid.status_code == 422
    assert valid.status_code == 200
    assert valid.json()["trusted"] is True


def test_second_get_supersedes_first():
    client = fresh_client()
    first = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    second = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())

    old_result = client.post("/evidence", json=build_evidence(first).model_dump())
    new_result = client.post("/evidence", json=build_evidence(second).model_dump())

    assert second.epoch == first.epoch + 1
    assert old_result.status_code == 200
    assert old_result.json()["reasons"] == [ReasonCode.CHALLENGE_SUPERSEDED.value]
    assert new_result.json()["trusted"] is True


def test_wrong_geo_is_denied():
    client = fresh_client()
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    evidence = build_evidence(challenge)
    evidence.geo = evidence.geo.model_copy(update={"inside": False})

    response = client.post("/evidence", json=evidence.model_dump())
    assert response.json()["trusted"] is False
    assert response.json()["reasons"] == [ReasonCode.GEO_FAILED.value]


def test_wrong_uwb_room_is_denied():
    client = fresh_client()
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    evidence = build_evidence(challenge)
    evidence.uwb = evidence.uwb.model_copy(update={"inside": False})

    response = client.post("/evidence", json=evidence.model_dump())
    assert response.json()["trusted"] is False
    assert response.json()["reasons"] == [ReasonCode.UWB_FAILED.value]


def test_tpm_failure_is_denied():
    client = fresh_client()
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    evidence = build_evidence(challenge)
    evidence.tpm = evidence.tpm.model_copy(update={"secure_boot": False})

    response = client.post("/evidence", json=evidence.model_dump())
    assert response.json()["trusted"] is False
    assert response.json()["reasons"] == [ReasonCode.TPM_FAILED.value]
