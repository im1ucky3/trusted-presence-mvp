from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import FastAPI

from shared.models import Challenge, PresenceEvidence, VerificationResult
from server.adapters.fake import FakeGEO, FakeTPM, FakeUWB
from server.challenge_service import ChallengeService
from server.challenge_store import MemoryChallengeStore
from server.evidence_access import EvidenceAccessor
from server.verifier import PresenceVerifier


def create_app(
    *,
    store: MemoryChallengeStore | None = None,
    tpm_verifier=None,
    geo_verifier=None,
    uwb_verifier=None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    store = store if store is not None else MemoryChallengeStore()
    tpm_verifier = tpm_verifier if tpm_verifier is not None else FakeTPM()
    geo_verifier = geo_verifier if geo_verifier is not None else FakeGEO()
    uwb_verifier = uwb_verifier if uwb_verifier is not None else FakeUWB()

    challenge_service = ChallengeService(store, clock=clock)
    verifier = PresenceVerifier(
        store=store,
        tpm_verifier=tpm_verifier,
        geo_verifier=geo_verifier,
        uwb_verifier=uwb_verifier,
        accessor=EvidenceAccessor(),
        clock=clock,
    )

    app = FastAPI(title="TrustedPresence MVP", version="0.1")
    app.state.challenge_store = store
    app.state.challenge_service = challenge_service
    app.state.presence_verifier = verifier

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/challenge/{device_id}", response_model=Challenge)
    def make_challenge(device_id: str):
        return challenge_service.issue(device_id)

    @app.post("/evidence", response_model=VerificationResult)
    def verify_evidence(evidence: PresenceEvidence):
        return verifier.verify_evidence(evidence)

    return app


app = create_app()
