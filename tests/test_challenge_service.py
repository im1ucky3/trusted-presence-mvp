from server.config import AVAILABLE_WITNESSES, CHALLENGE_TTL_SECONDS, WITNESS_QUORUM_SIZE


def test_issue_generates_expected_challenge_shape(challenge_service):
    challenge = challenge_service.issue("device-A")

    assert challenge.device_id == "device-A"
    assert challenge.epoch == 1
    assert len(challenge.session_id) >= 32
    assert len(challenge.nonce) >= 64
    assert len(challenge.witnesses) == WITNESS_QUORUM_SIZE
    assert len(set(challenge.witnesses)) == WITNESS_QUORUM_SIZE
    assert set(challenge.witnesses).issubset(set(AVAILABLE_WITNESSES))
    assert challenge.expires_at - challenge.issued_at == CHALLENGE_TTL_SECONDS


def test_issue_increments_epoch_and_rotates_security_values(challenge_service):
    first = challenge_service.issue("device-A")
    second = challenge_service.issue("device-A")

    assert second.epoch == first.epoch + 1
    assert second.session_id != first.session_id
    assert second.nonce != first.nonce
