from __future__ import annotations

from shared.models import GeoEvidence, PresenceEvidence, TPMEvidence, UWBEvidence


class EvidenceAccessor:
    """Single adaptation layer for the shared PresenceEvidence contract."""

    @staticmethod
    def session_id(evidence: PresenceEvidence) -> str:
        return evidence.session_id

    @staticmethod
    def protocol_version(evidence: PresenceEvidence) -> str:
        return evidence.protocol_version

    @staticmethod
    def device_id(evidence: PresenceEvidence) -> str:
        return evidence.device_id

    @staticmethod
    def epoch(evidence: PresenceEvidence) -> int:
        return evidence.epoch

    @staticmethod
    def nonce(evidence: PresenceEvidence) -> str:
        return evidence.nonce

    @staticmethod
    def witness_ids(evidence: PresenceEvidence) -> list[str]:
        return list(evidence.uwb.witnesses)

    @staticmethod
    def range_anchor_ids(evidence: PresenceEvidence) -> list[str]:
        return [item.anchor for item in evidence.uwb.ranges]

    @staticmethod
    def tpm(evidence: PresenceEvidence) -> TPMEvidence:
        return evidence.tpm

    @staticmethod
    def geo(evidence: PresenceEvidence) -> GeoEvidence:
        return evidence.geo

    @staticmethod
    def uwb(evidence: PresenceEvidence) -> UWBEvidence:
        return evidence.uwb
