import time
from fastapi.testclient import TestClient
from server.main import app
from shared.models import Challenge, PresenceEvidence
from agent.tpm.simulator import collect_tpm_evidence
from agent.geo.simulator import collect_geo_evidence
from agent.uwb.simulator import collect_uwb_evidence

client = TestClient(app)
DEVICE = "ASUS-G16-TEST"


def build_evidence(challenge: Challenge) -> PresenceEvidence:
    return PresenceEvidence(
        device_id=DEVICE,
        session_id=challenge.session_id,
        epoch=challenge.epoch,
        nonce=challenge.nonce,
        timestamp=int(time.time()),
        tpm=collect_tpm_evidence(challenge.nonce),
        geo=collect_geo_evidence(),
        uwb=collect_uwb_evidence(challenge.witnesses),
    )


def test_valid_flow_and_replay_rejected():
    challenge = Challenge.model_validate(client.get(f"/challenge/{DEVICE}").json())
    evidence = build_evidence(challenge)

    first = client.post("/evidence", json=evidence.model_dump())
    assert first.status_code == 200
    assert first.json()["trusted"] is True

    replay = client.post("/evidence", json=evidence.model_dump())
    assert replay.status_code == 404
