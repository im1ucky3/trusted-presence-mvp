from __future__ import annotations

import logging
import secrets
import time
from collections.abc import Callable
from typing import Any

from shared.models import PresenceEvidence, VerificationResult
from server.challenge_store import MemoryChallengeStore
from server.config import SUPPORTED_PROTOCOL_VERSION, WITNESS_QUORUM_SIZE
from server.evidence_access import EvidenceAccessor
from server.models import ClaimStatus, ReasonCode

logger = logging.getLogger(__name__)


class PresenceVerifier:
    def __init__(
        self,
        *,
        store: MemoryChallengeStore,
        tpm_verifier: Any,
        geo_verifier: Any,
        uwb_verifier: Any,
        accessor: EvidenceAccessor | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._store = store
        self._tpm = tpm_verifier
        self._geo = geo_verifier
        self._uwb = uwb_verifier
        self._accessor = accessor or EvidenceAccessor()
        self._clock = clock

    def verify_evidence(self, evidence: PresenceEvidence) -> VerificationResult:
        session_id = self._safe_session_id(evidence)
        if session_id is None:
            return VerificationResult(
                trusted=False,
                reasons=[ReasonCode.MALFORMED_EVIDENCE.value],
                session_id="",
                epoch=0,
            )

        now = int(self._clock())
        claim = self._store.claim(session_id, now=now)

        if claim.status != ClaimStatus.OK:
            return self._claim_failure_result(evidence, session_id, claim.status, claim.record)

        assert claim.record is not None
        challenge = claim.record.challenge

        try:
            protocol_version = self._accessor.protocol_version(evidence)
            device_id = self._accessor.device_id(evidence)
            epoch = self._accessor.epoch(evidence)
            nonce = self._accessor.nonce(evidence)
            witness_ids = self._accessor.witness_ids(evidence)
            range_anchor_ids = self._accessor.range_anchor_ids(evidence)
            tpm_evidence = self._accessor.tpm(evidence)
            geo_evidence = self._accessor.geo(evidence)
            uwb_evidence = self._accessor.uwb(evidence)
        except Exception:
            logger.exception("Failed to extract well-formed PresenceEvidence fields")
            return VerificationResult(
                trusted=False,
                reasons=[ReasonCode.MALFORMED_EVIDENCE.value],
                session_id=challenge.session_id,
                epoch=challenge.epoch,
            )

        reasons: list[str] = []

        # Phase 1: bind evidence to the server-issued challenge.
        if protocol_version != SUPPORTED_PROTOCOL_VERSION:
            reasons.append(ReasonCode.UNSUPPORTED_PROTOCOL.value)

        if device_id != challenge.device_id:
            reasons.append(ReasonCode.DEVICE_MISMATCH.value)

        if epoch != challenge.epoch:
            reasons.append(ReasonCode.EPOCH_MISMATCH.value)

        try:
            nonce_matches = secrets.compare_digest(nonce, challenge.nonce)
        except (TypeError, ValueError):
            nonce_matches = False
        if not nonce_matches:
            reasons.append(ReasonCode.NONCE_MISMATCH.value)

        if now > challenge.expires_at:
            reasons.append(ReasonCode.CHALLENGE_EXPIRED.value)

        if not self._valid_witness_quorum(
            challenge.witnesses,
            witness_ids,
            range_anchor_ids,
        ):
            reasons.append(ReasonCode.WITNESS_SET_MISMATCH.value)

        if reasons:
            return VerificationResult(
                trusted=False,
                reasons=reasons,
                session_id=challenge.session_id,
                epoch=challenge.epoch,
            )

        # Phase 2: run all presence verifiers and aggregate failures.
        if not self._safe_adapter_check("TPM", self._tpm.verify, tpm_evidence, challenge):
            reasons.append(ReasonCode.TPM_FAILED.value)

        if not self._safe_adapter_check("GEO", self._geo.verify, geo_evidence, challenge):
            reasons.append(ReasonCode.GEO_FAILED.value)

        if not self._safe_adapter_check("UWB", self._uwb.verify, uwb_evidence, challenge):
            reasons.append(ReasonCode.UWB_FAILED.value)

        return VerificationResult(
            trusted=not reasons,
            reasons=reasons,
            session_id=challenge.session_id,
            epoch=challenge.epoch,
        )

    def _safe_session_id(self, evidence: PresenceEvidence) -> str | None:
        try:
            session_id = self._accessor.session_id(evidence)
            if not isinstance(session_id, str) or not session_id:
                return None
            return session_id
        except Exception:
            logger.exception("Failed to extract session_id from PresenceEvidence")
            return None

    def _claim_failure_result(self, evidence, session_id, status, record) -> VerificationResult:
        reason_by_status = {
            ClaimStatus.UNKNOWN_SESSION: ReasonCode.UNKNOWN_SESSION,
            ClaimStatus.REPLAY: ReasonCode.REPLAY,
            ClaimStatus.SUPERSEDED: ReasonCode.CHALLENGE_SUPERSEDED,
            ClaimStatus.EXPIRED: ReasonCode.CHALLENGE_EXPIRED,
        }
        reason = reason_by_status[status].value

        if record is not None:
            epoch = record.challenge.epoch
            result_session_id = record.challenge.session_id
        else:
            result_session_id = session_id
            try:
                epoch = self._accessor.epoch(evidence)
            except Exception:
                epoch = 0

        return VerificationResult(
            trusted=False,
            reasons=[reason],
            session_id=result_session_id,
            epoch=epoch,
        )

    @staticmethod
    def _valid_witness_quorum(
        expected: list[str],
        received_witnesses: list[str],
        received_range_anchors: list[str],
    ) -> bool:
        if len(expected) != WITNESS_QUORUM_SIZE:
            return False
        if len(received_witnesses) != WITNESS_QUORUM_SIZE:
            return False
        if len(received_range_anchors) != WITNESS_QUORUM_SIZE:
            return False
        if len(set(received_witnesses)) != WITNESS_QUORUM_SIZE:
            return False
        if len(set(received_range_anchors)) != WITNESS_QUORUM_SIZE:
            return False

        expected_set = set(expected)
        return set(received_witnesses) == expected_set and set(received_range_anchors) == expected_set

    @staticmethod
    def _safe_adapter_check(name: str, func, *args) -> bool:
        try:
            return bool(func(*args))
        except Exception:
            logger.exception("%s verifier raised an exception", name)
            return False
