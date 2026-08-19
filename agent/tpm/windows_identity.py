from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from dataclasses import dataclass


@dataclass
class WindowsDeviceIdentity:
    device_id: str
    ek_public_b64: str

    certificate_subject: str | None
    certificate_issuer: str | None
    certificate_thumbprint: str | None


def _run_powershell(command: str) -> str:
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"PowerShell command failed:\n"
            f"{command}\n\n"
            f"stderr:\n{result.stderr}"
        )

    return result.stdout.strip()


def get_windows_device_identity() -> WindowsDeviceIdentity:
    command = r"""
    $ek = Get-TpmEndorsementKeyInfo

    if (-not $ek.IsPresent) {
        throw "TPM Endorsement Key is not present"
    }

    $certs = @($ek.ManufacturerCertificates) +
             @($ek.AdditionalCertificates)

    $cert = $certs | Select-Object -First 1

    $result = [PSCustomObject]@{
        ek_public_b64 = [Convert]::ToBase64String(
            $ek.PublicKey.RawData
        )

        certificate_subject = if ($cert) {
            $cert.Subject
        } else {
            $null
        }

        certificate_issuer = if ($cert) {
            $cert.Issuer
        } else {
            $null
        }

        certificate_thumbprint = if ($cert) {
            $cert.Thumbprint
        } else {
            $null
        }
    }

    $result | ConvertTo-Json -Compress
    """

    output = _run_powershell(command)
    data = json.loads(output)

    ek_public = base64.b64decode(
        data["ek_public_b64"]
    )

    fingerprint = hashlib.sha256(
        ek_public
    ).hexdigest()

    device_id = f"ek-sha256:{fingerprint}"

    return WindowsDeviceIdentity(
        device_id=device_id,
        ek_public_b64=data["ek_public_b64"],
        certificate_subject=data[
            "certificate_subject"
        ],
        certificate_issuer=data[
            "certificate_issuer"
        ],
        certificate_thumbprint=data[
            "certificate_thumbprint"
        ],
    )


if __name__ == "__main__":
    identity = get_windows_device_identity()

    print()
    print("TrustedPresence Device Identity")
    print("=" * 38)

    print(f"Device ID: {identity.device_id}")

    print(
        f"Certificate subject: "
        f"{identity.certificate_subject}"
    )

    print(
        f"Certificate issuer: "
        f"{identity.certificate_issuer}"
    )

    print(
        f"Certificate thumbprint: "
        f"{identity.certificate_thumbprint}"
    )