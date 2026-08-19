import asyncio
import os
import time

import httpx

from shared.models import Challenge, PresenceEvidence
from agent.geo.simulator import collect_geo_evidence
from agent.uwb.simulator import collect_uwb_evidence
from agent.tpm.simulator import collect_tpm_evidence as collect_simulated_tpm_evidence
from agent.tpm.real import collect_tpm_evidence as collect_real_tpm_evidence
from agent.tpm.windows_identity import get_windows_device_identity


SERVER = os.getenv("TRUSTED_PRESENCE_SERVER", "http://127.0.0.1:8000")
TPM_MODE = os.getenv("TPM_MODE", "simulated").lower()
SIMULATED_DEVICE_ID = os.getenv("DEVICE_ID", "ASUS-G16-DEMO")


def resolve_device_and_tpm():
    if TPM_MODE == "real":
        identity = get_windows_device_identity()
        return identity.device_id, collect_real_tpm_evidence

    if TPM_MODE == "simulated":
        return SIMULATED_DEVICE_ID, collect_simulated_tpm_evidence

    raise RuntimeError(
        f"Unsupported TPM_MODE={TPM_MODE!r}. "
        "Expected 'simulated' or 'real'."
    )


async def main():
    device_id, collect_tpm_evidence = resolve_device_and_tpm()

    print(f"TPM mode: {TPM_MODE}")
    print(f"Device ID: {device_id}")

    async with httpx.AsyncClient(timeout=15) as client:
        challenge_response = await client.get(
            f"{SERVER}/challenge/{device_id}"
        )
        challenge_response.raise_for_status()

        challenge = Challenge.model_validate(
            challenge_response.json()
        )

        print(f"Session: {challenge.session_id}")
        print(f"Epoch: {challenge.epoch}")
        print(f"Nonce: {challenge.nonce}")

        evidence = PresenceEvidence(
            device_id=device_id,
            session_id=challenge.session_id,
            epoch=challenge.epoch,
            nonce=challenge.nonce,
            timestamp=int(time.time()),
            tpm=collect_tpm_evidence(challenge.nonce),
            geo=collect_geo_evidence(),
            uwb=collect_uwb_evidence(challenge.witnesses),
        )

        response = await client.post(
            f"{SERVER}/evidence",
            json=evidence.model_dump(),
        )
        response.raise_for_status()

        print()
        print("Verification result:")
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
