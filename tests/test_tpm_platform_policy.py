from agent.tpm.platform_policy import verify_platform_status
from agent.tpm.windows_status import WindowsTPMStatus


def make_status(
    secure_boot: bool = True,
) -> WindowsTPMStatus:
    return WindowsTPMStatus(
        present=True,
        ready=True,
        enabled=True,
        activated=True,
        owned=True,
        manufacturer="AMD",
        manufacturer_version="6.32.0.6",
        secure_boot=secure_boot,
        ready_for_attestation=True,
        capable_for_attestation=True,
        restart_pending=False,
    )


def test_trusted_platform():
    result = verify_platform_status(
        make_status(secure_boot=True)
    )

    assert result.trusted is True
    assert result.reasons == []


def test_secure_boot_disabled():
    result = verify_platform_status(
        make_status(secure_boot=False)
    )

    assert result.trusted is False
    assert "secure_boot_disabled" in result.reasons
