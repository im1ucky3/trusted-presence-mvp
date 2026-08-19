from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from shared.models import Challenge


class ChallengeState(str, Enum):
    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    SUPERSEDED = "SUPERSEDED"


class ReasonCode(str, Enum):
    UNKNOWN_SESSION = "UNKNOWN_SESSION"
    REPLAY = "REPLAY"
    CHALLENGE_SUPERSEDED = "CHALLENGE_SUPERSEDED"
    CHALLENGE_EXPIRED = "CHALLENGE_EXPIRED"
    MALFORMED_EVIDENCE = "MALFORMED_EVIDENCE"
    UNSUPPORTED_PROTOCOL = "UNSUPPORTED_PROTOCOL"
    DEVICE_MISMATCH = "DEVICE_MISMATCH"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    NONCE_MISMATCH = "NONCE_MISMATCH"
    WITNESS_SET_MISMATCH = "WITNESS_SET_MISMATCH"
    TPM_FAILED = "TPM_FAILED"
    GEO_FAILED = "GEO_FAILED"
    UWB_FAILED = "UWB_FAILED"


class ClaimStatus(str, Enum):
    OK = "OK"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"
    REPLAY = "REPLAY"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


@dataclass
class ChallengeRecord:
    challenge: Challenge
    state: ChallengeState = ChallengeState.ISSUED


@dataclass
class ClaimResult:
    status: ClaimStatus
    record: ChallengeRecord | None = None
