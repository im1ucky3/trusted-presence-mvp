from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

PROTOCOL_VERSION = "0.1"

class Challenge(BaseModel):
    protocol_version: str = PROTOCOL_VERSION
    session_id: str
    device_id: str
    epoch: int
    nonce: str
    witnesses: list[str]
    issued_at: int
    expires_at: int

class TPMEvidence(BaseModel):
    mode: Literal["simulated", "real"]
    quote_b64: str
    signature_b64: str
    pcrs: dict[str, str]
    secure_boot: bool
    nonce: str

class GeoEvidence(BaseModel):
    mode: Literal["simulated", "phone", "gnss"]
    lat: float
    lon: float
    accuracy_m: float
    timestamp: int
    facility_id: str
    distance_m: float
    inside: bool
    fresh: bool

class UWBRange(BaseModel):
    anchor: str
    distance_m: float = Field(ge=0)
    quality: float = Field(ge=0, le=1)

class UWBEvidence(BaseModel):
    mode: Literal["simulated", "serial"]
    witnesses: list[str]
    ranges: list[UWBRange]
    position_x: float | None = None
    position_y: float | None = None
    inside: bool
    timestamp: int

class PresenceEvidence(BaseModel):
    protocol_version: str = PROTOCOL_VERSION
    device_id: str
    session_id: str
    epoch: int
    nonce: str
    timestamp: int
    tpm: TPMEvidence
    geo: GeoEvidence
    uwb: UWBEvidence

class VerificationResult(BaseModel):
    trusted: bool
    reasons: list[str]
    session_id: str
    epoch: int
