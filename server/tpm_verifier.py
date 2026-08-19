from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from shared.models import TPMEvidence


ROOT = Path(__file__).resolve().parents[1]

TPM_HELPER = (
    ROOT
    / "tools"
    / "tpm-helper"
    / "tpm-helper.csproj"
)

ENROLLMENT_FILE = (
    ROOT
    / "state"
    / "tpm_enrollment.json"
)


@dataclass
class TPMVerificationResult:
    valid: bool
    reasons: list[str]


def _load_enrollment(
    device_id: str,
) -> dict | None:
    if not ENROLLMENT_FILE.exists():
        return None

    with ENROLLMENT_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        data = json.load(f)

    return data.get(device_id)


def verify_real_tpm_evidence(
    device_id: str,
    expected_nonce: str,
    evidence: TPMEvidence,
) -> TPMVerificationResult:
    reasons: list[str] = []

    if evidence.mode != "real":
        return TPMVerificationResult(
            valid=False,
            reasons=["tpm_not_real"],
        )

    if evidence.nonce.lower() != expected_nonce.lower():
        reasons.append("tpm_nonce_mismatch")

    required_pcrs = {"0", "2", "4", "7"}

    if not required_pcrs.issubset(evidence.pcrs):
        reasons.append("tpm_pcr_set_invalid")

    if reasons:
        return TPMVerificationResult(
            valid=False,
            reasons=reasons,
        )

    enrollment = _load_enrollment(device_id)

    if enrollment is None:
        return TPMVerificationResult(
            valid=False,
            reasons=["tpm_device_not_enrolled"],
        )

    command = [
        "dotnet",
        "run",
        "--no-build",
        "--project",
        str(TPM_HELPER),
        "--",
        "verify",
        enrollment["ak_public_b64"],
        evidence.quote_b64,
        evidence.signature_b64,
        expected_nonce,
        evidence.pcrs["0"],
        evidence.pcrs["2"],
        evidence.pcrs["4"],
        evidence.pcrs["7"],
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode not in (0, 3):
        return TPMVerificationResult(
            valid=False,
            reasons=[
                "tpm_verifier_error"
            ],
        )

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        return TPMVerificationResult(
            valid=False,
            reasons=[
                "tpm_verifier_invalid_output"
            ],
        )

    if not output.get("valid", False):
        return TPMVerificationResult(
            valid=False,
            reasons=["tpm_quote_invalid"],
        )

    return TPMVerificationResult(
        valid=True,
        reasons=[],
    )