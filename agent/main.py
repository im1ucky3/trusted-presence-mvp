import asyncio
import time

import httpx

from shared.models import Challenge, PresenceEvidence
from agent.tpm.real import collect_tpm_evidence
from agent.tpm.windows_identity import get_windows_device_identity
from agent.geo.simulator import collect_geo_evidence
from agent.uwb.simulator import collect_uwb_evidence


SERVER = "http://127.0.0.1:8000"


async def main():
    device_id = get_windows_device_identity().device_id

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
            tpm=collect_tpm_evidence(
                challenge.nonce
            ),
            geo=collect_geo_evidence(),
            uwb=collect_uwb_evidence(
                challenge.witnesses
            ),
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