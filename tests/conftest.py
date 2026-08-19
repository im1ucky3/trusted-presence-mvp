from __future__ import annotations

import time

import pytest

from agent.geo.simulator import collect_geo_evidence
from agent.tpm.simulator import collect_tpm_evidence
from agent.uwb.simulator import collect_uwb_evidence
from server.adapters.fake import FakeGEO, FakeTPM, FakeUWB
from server.challenge_service import ChallengeService
from server.challenge_store import MemoryChallengeStore
from server.evidence_access import EvidenceAccessor
from server.verifier import PresenceVerifier
from shared.models import Challenge, PresenceEvidence


class MutableClock:
    def __init__(self, value: int = 1_700_000_000) -> None:
        self.value = value

    def __call__(self) -> float:
        return float(self.value)

    def advance(self, seconds: int) -> None:
        self.value += seconds


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def store() -> MemoryChallengeStore:
    return MemoryChallengeStore()


@pytest.fixture
def challenge_service(store, clock) -> ChallengeService:
    return ChallengeService(store, clock=clock)


@pytest.fixture
def fake_tpm() -> FakeTPM:
    return FakeTPM()


@pytest.fixture
def fake_geo() -> FakeGEO:
    return FakeGEO()


@pytest.fixture
def fake_uwb() -> FakeUWB:
    return FakeUWB()


@pytest.fixture
def verifier(store, fake_tpm, fake_geo, fake_uwb, clock) -> PresenceVerifier:
    return PresenceVerifier(
        store=store,
        tpm_verifier=fake_tpm,
        geo_verifier=fake_geo,
        uwb_verifier=fake_uwb,
        accessor=EvidenceAccessor(),
        clock=clock,
    )


def make_evidence(challenge: Challenge, *, device_id: str | None = None) -> PresenceEvidence:
    return PresenceEvidence(
        device_id=device_id or challenge.device_id,
        session_id=challenge.session_id,
        epoch=challenge.epoch,
        nonce=challenge.nonce,
        timestamp=int(time.time()),
        tpm=collect_tpm_evidence(challenge.nonce),
        geo=collect_geo_evidence(),
        uwb=collect_uwb_evidence(challenge.witnesses),
    )


@pytest.fixture
def evidence_factory():
    return make_evidence
