from typing import Protocol

from shared.models import Challenge, GeoEvidence, TPMEvidence, UWBEvidence


class TPMVerifier(Protocol):
    def verify(self, evidence: TPMEvidence, challenge: Challenge) -> bool: ...


class GEOVerifier(Protocol):
    def verify(self, evidence: GeoEvidence, challenge: Challenge) -> bool: ...


class UWBVerifier(Protocol):
    def verify(self, evidence: UWBEvidence, challenge: Challenge) -> bool: ...
