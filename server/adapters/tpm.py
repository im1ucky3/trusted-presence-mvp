from __future__ import annotations

import logging
import os
import secrets

from shared.models import Challenge, TPMEvidence
from server.tpm_verifier import verify_real_tpm_evidence


logger = logging.getLogger(__name__)


class IntegratedTPMVerifier:
    """
    Adapter between participant #1 TPM verifier and the server verifier interface.

    - real evidence -> participant #1 cryptographic verifier
    - simulated evidence -> allowed for MVP unless REQUIRE_REAL_TPM=1
    """

    def __init__(self, require_real: bool | None = None) -> None:
        if require_real is None:
            require_real = os.getenv("REQUIRE_REAL_TPM", "0") == "1"
        self._require_real = require_real

    def verify(self, evidence: TPMEvidence, challenge: Challenge) -> bool:
        if evidence.mode == "real":
            if not evidence.secure_boot:
                logger.warning(
                    "Real TPM evidence reports secure_boot=False for device %s",
                    challenge.device_id,
                )
                return False

            result = verify_real_tpm_evidence(
                device_id=challenge.device_id,
                expected_nonce=challenge.nonce,
                evidence=evidence,
            )

            if not result.valid:
                logger.warning(
                    "Real TPM verification failed for device %s: %s",
                    challenge.device_id,
                    result.reasons,
                )

            return result.valid

        if self._require_real:
            logger.warning(
                "Simulated TPM evidence rejected because REQUIRE_REAL_TPM=1"
            )
            return False

        try:
            nonce_matches = secrets.compare_digest(
                evidence.nonce,
                challenge.nonce,
            )
        except (TypeError, ValueError):
            nonce_matches = False

        return evidence.secure_boot and nonce_matches
