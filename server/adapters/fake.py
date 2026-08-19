import secrets

from shared.models import Challenge, GeoEvidence, TPMEvidence, UWBEvidence


class FakeTPM:
    """Day-1 verifier until participant #1 real TPM verifier is connected."""

    def verify(self, evidence: TPMEvidence, challenge: Challenge) -> bool:
        return evidence.secure_boot and secrets.compare_digest(evidence.nonce, challenge.nonce)


class FakeGEO:
    """Day-1 verifier until participant #2 real GEO verifier is connected."""

    def verify(self, evidence: GeoEvidence, challenge: Challenge) -> bool:
        del challenge
        return evidence.inside and evidence.fresh


class FakeUWB:
    """Day-1 verifier until participant #2 real UWB verifier is connected."""

    def verify(self, evidence: UWBEvidence, challenge: Challenge) -> bool:
        del challenge
        return evidence.inside
