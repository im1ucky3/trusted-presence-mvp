from __future__ import annotations

import json
import subprocess
from pathlib import Path

from shared.models import TPMEvidence
from agent.tpm.windows_status import get_windows_tpm_status


ROOT = Path(__file__).resolve().parents[2]

TPM_HELPER = (
    ROOT
    / "tools"
    / "tpm-helper"
    / "tpm-helper.csproj"
)


def _run_quote(nonce: str) -> dict:
    if len(nonce) != 64:
        raise ValueError(
            "TPM nonce must be 64 hexadecimal characters"
        )

    try:
        bytes.fromhex(nonce)
    except ValueError as exc:
        raise ValueError(
            "TPM nonce must be hexadecimal"
        ) from exc

    result = subprocess.run(
        [
            "dotnet",
            "run",
            "--project",
            str(TPM_HELPER),
            "--",
            "quote",
            nonce,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "TPM helper failed:\n"
            f"{result.stderr.strip()}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "TPM helper returned invalid JSON:\n"
            f"{result.stdout}"
        ) from exc


def collect_tpm_evidence(
    nonce: str,
) -> TPMEvidence:
    status = get_windows_tpm_status()

    if not status.present:
        raise RuntimeError("TPM is not present")

    if not status.ready:
        raise RuntimeError("TPM is not ready")

    quote = _run_quote(nonce)

    if quote.get("mode") != "real":
        raise RuntimeError(
            "TPM helper did not return real evidence"
        )

    if quote.get("nonce") != nonce.lower():
        raise RuntimeError(
            "TPM helper returned wrong nonce"
        )

    if not quote.get("verified_locally"):
        raise RuntimeError(
            "TPM quote failed local verification"
        )

    return TPMEvidence(
        mode="real",
        quote_b64=quote["quote_b64"],
        signature_b64=quote["signature_b64"],
        pcrs=quote["pcrs"],
        secure_boot=status.secure_boot,
        nonce=quote["nonce"],
    )


if __name__ == "__main__":
    import secrets

    nonce = secrets.token_hex(32)

    print(f"Nonce: {nonce}")

    evidence = collect_tpm_evidence(nonce)

    print(
        evidence.model_dump_json(indent=2)
    )