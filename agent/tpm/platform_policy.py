from __future__ import annotations

from dataclasses import dataclass

from agent.tpm.windows_status import (
    WindowsTPMStatus,
    get_windows_tpm_status,
)


@dataclass
class PlatformPolicyResult:
    trusted: bool
    reasons: list[str]


def verify_platform_status(
    status: WindowsTPMStatus,
) -> PlatformPolicyResult:

    reasons: list[str] = []

    if not status.present:
        reasons.append("tpm_not_present")

    if not status.ready:
        reasons.append("tpm_not_ready")

    if not status.enabled:
        reasons.append("tpm_not_enabled")

    if not status.activated:
        reasons.append("tpm_not_activated")

    if not status.ready_for_attestation:
        reasons.append("tpm_not_ready_for_attestation")

    if not status.capable_for_attestation:
        reasons.append("tpm_not_attestation_capable")

    if not status.secure_boot:
        reasons.append("secure_boot_disabled")

    return PlatformPolicyResult(
        trusted=len(reasons) == 0,
        reasons=reasons,
    )


if __name__ == "__main__":
    status = get_windows_tpm_status()
    result = verify_platform_status(status)

    print()
    print("TrustedPresence Platform Policy")
    print("=" * 38)

    if result.trusted:
        print("RESULT: TRUSTED")
    else:
        print("RESULT: DENIED")
        print("Reasons:")

        for reason in result.reasons:
            print(f"  - {reason}")
