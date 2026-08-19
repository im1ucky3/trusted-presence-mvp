from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass
class WindowsTPMStatus:
    present: bool
    ready: bool
    enabled: bool
    activated: bool
    owned: bool

    manufacturer: str
    manufacturer_version: str

    secure_boot: bool

    ready_for_attestation: bool
    capable_for_attestation: bool

    restart_pending: bool


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


def _get_tpm() -> dict:
    command = """
    Get-Tpm |
    Select-Object `
        TpmPresent,
        TpmReady,
        TpmEnabled,
        TpmActivated,
        TpmOwned,
        RestartPending,
        ManufacturerIdTxt,
        ManufacturerVersion |
    ConvertTo-Json -Compress
    """

    output = _run_powershell(command)

    return json.loads(output)


def _get_secure_boot() -> bool:
    output = _run_powershell(
        "Confirm-SecureBootUEFI"
    )

    return output.strip().lower() == "true"


def _get_attestation_status() -> tuple[bool, bool]:
    output = _run_powershell(
        "tpmtool getdeviceinformation"
    )

    ready = (
        "-Ready For Attestation: True"
        in output
    )

    capable = (
        "-Is Capable For Attestation: True"
        in output
    )

    return ready, capable


def get_windows_tpm_status() -> WindowsTPMStatus:
    tpm = _get_tpm()

    ready_attestation, capable_attestation = (
        _get_attestation_status()
    )

    secure_boot = _get_secure_boot()

    return WindowsTPMStatus(
        present=bool(tpm["TpmPresent"]),
        ready=bool(tpm["TpmReady"]),
        enabled=bool(tpm["TpmEnabled"]),
        activated=bool(tpm["TpmActivated"]),
        owned=bool(tpm["TpmOwned"]),

        manufacturer=tpm[
            "ManufacturerIdTxt"
        ],

        manufacturer_version=str(
            tpm["ManufacturerVersion"]
        ),

        secure_boot=secure_boot,

        ready_for_attestation=ready_attestation,
        capable_for_attestation=capable_attestation,

        restart_pending=bool(
            tpm["RestartPending"]
        ),
    )

if __name__ == "__main__":
    status = get_windows_tpm_status()

    print()
    print("TrustedPresence TPM Status")
    print("=" * 35)

    print(
        f"TPM present:            "
        f"{status.present}"
    )

    print(
        f"TPM ready:              "
        f"{status.ready}"
    )

    print(
        f"TPM enabled:            "
        f"{status.enabled}"
    )

    print(
        f"TPM activated:          "
        f"{status.activated}"
    )

    print(
        f"TPM owned:              "
        f"{status.owned}"
    )

    print(
        f"Manufacturer:           "
        f"{status.manufacturer}"
    )

    print(
        f"Firmware:               "
        f"{status.manufacturer_version}"
    )

    print(
        f"Ready for attestation:  "
        f"{status.ready_for_attestation}"
    )

    print(
        f"Capable of attestation: "
        f"{status.capable_for_attestation}"
    )

    print(
        f"Secure Boot:            "
        f"{status.secure_boot}"
    )

    print(
        f"Restart pending:        "
        f"{status.restart_pending}"
    )