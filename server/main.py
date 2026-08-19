import os
import secrets
import time

from fastapi import FastAPI, HTTPException

from shared.models import (
    Challenge,
    PresenceEvidence,
    VerificationResult,
)
from server.tpm_verifier import verify_real_tpm_evidence


app = FastAPI(
    title="TrustedPresence MVP",
    version="0.1",
)

CHALLENGES: dict[str, Challenge] = {}
EPOCHS: dict[str, int] = {}
CONSUMED_SESSIONS: set[str] = set()

ANCHORS = ["A", "B", "C", "D", "E"]

REQUIRE_REAL_TPM = (
    os.getenv("REQUIRE_REAL_TPM", "0") == "1"
)


@app.get("/health")
def health():
    return {"ok": True}


@app.get(
    "/challenge/{device_id}",
    response_model=Challenge,
)
def make_challenge(device_id: str):
    now = int(time.time())

    epoch = EPOCHS.get(device_id, 0) + 1
    EPOCHS[device_id] = epoch

    witnesses = secrets.SystemRandom().sample(
        ANCHORS,
        3,
    )

    challenge = Challenge(
        session_id=secrets.token_hex(8),
        device_id=device_id,
        epoch=epoch,
        nonce=secrets.token_hex(32),
        witnesses=witnesses,
        issued_at=now,
        expires_at=now + 30,
    )

    CHALLENGES[
        challenge.session_id
    ] = challenge

    return challenge


@app.post(
    "/evidence",
    response_model=VerificationResult,
)
def verify_evidence(
    e: PresenceEvidence,
):
    if e.session_id in CONSUMED_SESSIONS:
        return VerificationResult(
            trusted=False,
            reasons=["challenge_replayed"],
            session_id=e.session_id,
            epoch=e.epoch,
        )

    c = CHALLENGES.pop(
        e.session_id,
        None,
    )

    if c is None:
        raise HTTPException(
            status_code=404,
            detail="unknown session",
        )

    CONSUMED_SESSIONS.add(
        e.session_id
    )

    reasons: list[str] = []
    now = int(time.time())

    if now > c.expires_at:
        reasons.append(
            "challenge_expired"
        )

    if e.device_id != c.device_id:
        reasons.append(
            "device_mismatch"
        )

    if e.epoch != c.epoch:
        reasons.append(
            "epoch_mismatch"
        )

    if (
        e.nonce != c.nonce
        or e.tpm.nonce != c.nonce
    ):
        reasons.append(
            "nonce_mismatch"
        )

    if (
        sorted(e.uwb.witnesses)
        != sorted(c.witnesses)
    ):
        reasons.append(
            "witness_set_mismatch"
        )

    if e.tpm.mode == "real":
        tpm_result = verify_real_tpm_evidence(
            device_id=c.device_id,
            expected_nonce=c.nonce,
            evidence=e.tpm,
        )

        reasons.extend(
            tpm_result.reasons
        )

    elif REQUIRE_REAL_TPM:
        reasons.append(
            "tpm_not_real"
        )

    if not e.tpm.secure_boot:
        reasons.append(
            "secure_boot_failed"
        )

    if (
        not e.geo.inside
        or not e.geo.fresh
    ):
        reasons.append(
            "macro_location_failed"
        )

    if not e.uwb.inside:
        reasons.append(
            "room_presence_failed"
        )

    trusted = len(reasons) == 0

    return VerificationResult(
        trusted=trusted,
        reasons=(
            reasons
            or ["all_checks_passed"]
        ),
        session_id=e.session_id,
        epoch=e.epoch,
    )