from concurrent.futures import ThreadPoolExecutor

from server.adapters.fake import FakeGEO, FakeTPM, FakeUWB
from server.evidence_access import EvidenceAccessor
from server.models import ReasonCode
from server.verifier import PresenceVerifier
from shared.models import UWBRange


def test_valid_evidence_is_trusted(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    result = verifier.verify_evidence(evidence_factory(challenge))

    assert result.trusted is True
    assert result.reasons == []


def test_replay_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)

    assert verifier.verify_evidence(evidence).trusted is True
    replay = verifier.verify_evidence(evidence)

    assert replay.trusted is False
    assert replay.reasons == [ReasonCode.REPLAY.value]


def test_wrong_nonce_denied_and_consumes_challenge(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    bad = evidence_factory(challenge).model_copy(update={"nonce": "wrong"})

    first = verifier.verify_evidence(bad)
    second = verifier.verify_evidence(evidence_factory(challenge))

    assert first.reasons == [ReasonCode.NONCE_MISMATCH.value]
    assert second.reasons == [ReasonCode.REPLAY.value]


def test_wrong_epoch_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    bad = evidence_factory(challenge).model_copy(update={"epoch": challenge.epoch + 1})

    result = verifier.verify_evidence(bad)
    assert result.reasons == [ReasonCode.EPOCH_MISMATCH.value]


def test_wrong_device_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    bad = evidence_factory(challenge).model_copy(update={"device_id": "device-B"})

    result = verifier.verify_evidence(bad)
    assert result.reasons == [ReasonCode.DEVICE_MISMATCH.value]


def test_wrong_protocol_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    bad = evidence_factory(challenge).model_copy(update={"protocol_version": "999"})

    result = verifier.verify_evidence(bad)
    assert result.reasons == [ReasonCode.UNSUPPORTED_PROTOCOL.value]


def test_expired_challenge_is_denied(challenge_service, verifier, clock, evidence_factory):
    challenge = challenge_service.issue("device-A")
    clock.advance(31)

    result = verifier.verify_evidence(evidence_factory(challenge))
    assert result.reasons == [ReasonCode.CHALLENGE_EXPIRED.value]


def test_superseded_challenge_is_denied(challenge_service, verifier, evidence_factory):
    old = challenge_service.issue("device-A")
    latest = challenge_service.issue("device-A")

    old_result = verifier.verify_evidence(evidence_factory(old))
    latest_result = verifier.verify_evidence(evidence_factory(latest))

    assert old_result.reasons == [ReasonCode.CHALLENGE_SUPERSEDED.value]
    assert latest_result.trusted is True


def test_witness_order_does_not_matter(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)
    reversed_witnesses = list(reversed(evidence.uwb.witnesses))
    reversed_ranges = list(reversed(evidence.uwb.ranges))
    evidence.uwb = evidence.uwb.model_copy(
        update={"witnesses": reversed_witnesses, "ranges": reversed_ranges}
    )

    assert verifier.verify_evidence(evidence).trusted is True



def test_wrong_witness_set_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)
    replacement = next(a for a in ["A", "B", "C", "D", "E"] if a not in challenge.witnesses)
    witnesses = list(evidence.uwb.witnesses)
    witnesses[0] = replacement
    evidence.uwb = evidence.uwb.model_copy(update={"witnesses": witnesses})

    result = verifier.verify_evidence(evidence)
    assert result.reasons == [ReasonCode.WITNESS_SET_MISMATCH.value]

def test_duplicate_witness_is_denied(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)
    duplicate = [challenge.witnesses[0], challenge.witnesses[0], challenge.witnesses[2]]
    evidence.uwb = evidence.uwb.model_copy(update={"witnesses": duplicate})

    result = verifier.verify_evidence(evidence)
    assert result.reasons == [ReasonCode.WITNESS_SET_MISMATCH.value]


def test_range_anchor_set_must_match_requested_witnesses(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)
    wrong_anchor = next(a for a in ["A", "B", "C", "D", "E"] if a not in challenge.witnesses)
    ranges = list(evidence.uwb.ranges)
    ranges[0] = UWBRange(anchor=wrong_anchor, distance_m=ranges[0].distance_m, quality=ranges[0].quality)
    evidence.uwb = evidence.uwb.model_copy(update={"ranges": ranges})

    result = verifier.verify_evidence(evidence)
    assert result.reasons == [ReasonCode.WITNESS_SET_MISMATCH.value]


class ControlledTPM(FakeTPM):
    def __init__(self, result=True):
        self.result = result
        self.calls = 0

    def verify(self, evidence, challenge):
        self.calls += 1
        return self.result


class ControlledGEO(FakeGEO):
    def __init__(self, result=True):
        self.result = result
        self.calls = 0

    def verify(self, evidence, challenge):
        self.calls += 1
        return self.result


class ControlledUWB(FakeUWB):
    def __init__(self, result=True):
        self.result = result
        self.calls = 0

    def verify(self, evidence, challenge):
        self.calls += 1
        return self.result


def test_phase2_aggregates_failures(store, challenge_service, clock, evidence_factory):
    tpm = ControlledTPM(True)
    geo = ControlledGEO(False)
    uwb = ControlledUWB(False)
    verifier = PresenceVerifier(
        store=store,
        tpm_verifier=tpm,
        geo_verifier=geo,
        uwb_verifier=uwb,
        accessor=EvidenceAccessor(),
        clock=clock,
    )
    challenge = challenge_service.issue("device-A")

    result = verifier.verify_evidence(evidence_factory(challenge))

    assert result.reasons == [ReasonCode.GEO_FAILED.value, ReasonCode.UWB_FAILED.value]
    assert tpm.calls == geo.calls == uwb.calls == 1


def test_phase1_failure_does_not_call_adapters(store, challenge_service, clock, evidence_factory):
    tpm = ControlledTPM(True)
    geo = ControlledGEO(True)
    uwb = ControlledUWB(True)
    verifier = PresenceVerifier(
        store=store,
        tpm_verifier=tpm,
        geo_verifier=geo,
        uwb_verifier=uwb,
        accessor=EvidenceAccessor(),
        clock=clock,
    )
    challenge = challenge_service.issue("device-A")
    bad = evidence_factory(challenge).model_copy(update={"nonce": "wrong"})

    result = verifier.verify_evidence(bad)

    assert result.reasons == [ReasonCode.NONCE_MISMATCH.value]
    assert tpm.calls == geo.calls == uwb.calls == 0


class RaisingVerifier:
    def verify(self, evidence, challenge):
        raise RuntimeError("adapter exploded")


def test_adapter_exception_fails_closed(store, challenge_service, clock, evidence_factory):
    verifier = PresenceVerifier(
        store=store,
        tpm_verifier=RaisingVerifier(),
        geo_verifier=FakeGEO(),
        uwb_verifier=FakeUWB(),
        accessor=EvidenceAccessor(),
        clock=clock,
    )
    challenge = challenge_service.issue("device-A")

    result = verifier.verify_evidence(evidence_factory(challenge))
    assert result.trusted is False
    assert result.reasons == [ReasonCode.TPM_FAILED.value]


class BrokenAccessor(EvidenceAccessor):
    def protocol_version(self, evidence):
        raise AttributeError("broken mapping")


def test_accessor_failure_is_malformed_and_consumed(store, challenge_service, clock, evidence_factory):
    challenge = challenge_service.issue("device-A")
    broken = PresenceVerifier(
        store=store,
        tpm_verifier=FakeTPM(),
        geo_verifier=FakeGEO(),
        uwb_verifier=FakeUWB(),
        accessor=BrokenAccessor(),
        clock=clock,
    )

    first = broken.verify_evidence(evidence_factory(challenge))
    normal = PresenceVerifier(
        store=store,
        tpm_verifier=FakeTPM(),
        geo_verifier=FakeGEO(),
        uwb_verifier=FakeUWB(),
        accessor=EvidenceAccessor(),
        clock=clock,
    )
    second = normal.verify_evidence(evidence_factory(challenge))

    assert first.reasons == [ReasonCode.MALFORMED_EVIDENCE.value]
    assert second.reasons == [ReasonCode.REPLAY.value]


def test_concurrent_verification_allows_at_most_one_trusted(challenge_service, verifier, evidence_factory):
    challenge = challenge_service.issue("device-A")
    evidence = evidence_factory(challenge)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: verifier.verify_evidence(evidence), range(2)))

    assert sum(result.trusted for result in results) == 1
    assert sorted(reason for result in results for reason in result.reasons) == [ReasonCode.REPLAY.value]
