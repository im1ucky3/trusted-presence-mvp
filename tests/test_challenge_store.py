from concurrent.futures import ThreadPoolExecutor

from server.models import ChallengeState, ClaimStatus


def _issue(store, device: str, idx: int, now: int = 100):
    return store.issue(
        device_id=device,
        session_id=f"session-{idx}",
        nonce=f"nonce-{idx}",
        witnesses=["A", "B", "C"],
        issued_at=now,
        expires_at=now + 30,
    )


def test_second_issue_supersedes_first_for_same_device(store):
    first = _issue(store, "device-A", 1)
    second = _issue(store, "device-A", 2)

    assert first.epoch == 1
    assert second.epoch == 2
    assert store.get_record(first.session_id).state == ChallengeState.SUPERSEDED
    assert store.get_record(second.session_id).state == ChallengeState.ISSUED
    assert store.active_session_for_device("device-A") == second.session_id


def test_different_devices_do_not_supersede_each_other(store):
    a = _issue(store, "device-A", 1)
    b = _issue(store, "device-B", 2)

    assert store.get_record(a.session_id).state == ChallengeState.ISSUED
    assert store.get_record(b.session_id).state == ChallengeState.ISSUED
    assert a.epoch == 1
    assert b.epoch == 1


def test_claim_consumes_once_and_replay_is_rejected(store):
    challenge = _issue(store, "device-A", 1)

    first = store.claim(challenge.session_id, now=100)
    second = store.claim(challenge.session_id, now=100)

    assert first.status == ClaimStatus.OK
    assert second.status == ClaimStatus.REPLAY


def test_superseded_claim_is_distinct_from_unknown(store):
    first = _issue(store, "device-A", 1)
    _issue(store, "device-A", 2)

    assert store.claim(first.session_id, now=100).status == ClaimStatus.SUPERSEDED
    assert store.claim("missing", now=100).status == ClaimStatus.UNKNOWN_SESSION


def test_expired_challenge_is_not_claimed(store):
    challenge = _issue(store, "device-A", 1, now=100)

    result = store.claim(challenge.session_id, now=131)

    assert result.status == ClaimStatus.EXPIRED
    assert store.active_session_for_device("device-A") is None


def test_concurrent_claim_allows_only_one_success(store):
    challenge = _issue(store, "device-A", 1)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: store.claim(challenge.session_id, now=100).status, range(8)))

    assert results.count(ClaimStatus.OK) == 1
    assert results.count(ClaimStatus.REPLAY) == 7


def test_concurrent_issue_leaves_one_active_challenge(store):
    def issue_one(i: int):
        return _issue(store, "device-A", i)

    with ThreadPoolExecutor(max_workers=8) as pool:
        challenges = list(pool.map(issue_one, range(1, 9)))

    epochs = sorted(c.epoch for c in challenges)
    assert epochs == list(range(1, 9))

    active_session = store.active_session_for_device("device-A")
    assert active_session is not None
    issued_records = [
        store.get_record(c.session_id)
        for c in challenges
        if store.get_record(c.session_id).state == ChallengeState.ISSUED
    ]
    assert len(issued_records) == 1
    assert issued_records[0].challenge.session_id == active_session
