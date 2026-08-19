import secrets
import time
from fastapi import FastAPI, HTTPException
from shared.models import Challenge, PresenceEvidence, VerificationResult

app = FastAPI(title="TrustedPresence MVP", version="0.1")
CHALLENGES: dict[str, Challenge] = {}
EPOCHS: dict[str, int] = {}
ANCHORS = ["A", "B", "C", "D", "E"]

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/challenge/{device_id}", response_model=Challenge)
def make_challenge(device_id: str):
    now = int(time.time())
    epoch = EPOCHS.get(device_id, 0) + 1
    EPOCHS[device_id] = epoch
    witnesses = secrets.SystemRandom().sample(ANCHORS, 3)
    challenge = Challenge(
        session_id=secrets.token_hex(8),
        device_id=device_id,
        epoch=epoch,
        nonce=secrets.token_hex(32),
        witnesses=witnesses,
        issued_at=now,
        expires_at=now + 30,
    )
    CHALLENGES[challenge.session_id] = challenge
    return challenge

@app.post("/evidence", response_model=VerificationResult)
def verify_evidence(e: PresenceEvidence):
    c = CHALLENGES.get(e.session_id)
    if c is None:
        raise HTTPException(404, "unknown session")

    reasons: list[str] = []
    now = int(time.time())
    if now > c.expires_at:
        reasons.append("challenge_expired")
    if e.device_id != c.device_id:
        reasons.append("device_mismatch")
    if e.epoch != c.epoch:
        reasons.append("epoch_mismatch")
    if e.nonce != c.nonce or e.tpm.nonce != c.nonce:
        reasons.append("nonce_mismatch")
    if sorted(e.uwb.witnesses) != sorted(c.witnesses):
        reasons.append("witness_set_mismatch")
    if not e.tpm.secure_boot:
        reasons.append("secure_boot_failed")
    if not e.geo.inside or not e.geo.fresh:
        reasons.append("macro_location_failed")
    if not e.uwb.inside:
        reasons.append("room_presence_failed")

    # Day-1 MVP: cryptographic TPM verification is implemented by TPM owner.
    trusted = not reasons
    if trusted:
        CHALLENGES.pop(e.session_id, None)  # one-time challenge, blocks replay

    return VerificationResult(
        trusted=trusted,
        reasons=reasons or ["all_checks_passed"],
        session_id=e.session_id,
        epoch=e.epoch,
    )
