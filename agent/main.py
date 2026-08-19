import asyncio
import time
import httpx
from shared.models import Challenge, PresenceEvidence
from agent.tpm.simulator import collect_tpm_evidence
from agent.geo.simulator import collect_geo_evidence
from agent.uwb.simulator import collect_uwb_evidence

SERVER = "http://127.0.0.1:8000"
DEVICE_ID = "ASUS-G16-DEMO"

async def main():
    async with httpx.AsyncClient(timeout=5) as client:
        challenge_json = (await client.get(f"{SERVER}/challenge/{DEVICE_ID}")).json()
        challenge = Challenge.model_validate(challenge_json)

        evidence = PresenceEvidence(
            device_id=DEVICE_ID,
            session_id=challenge.session_id,
            epoch=challenge.epoch,
            nonce=challenge.nonce,
            timestamp=int(time.time()),
            tpm=collect_tpm_evidence(challenge.nonce),
            geo=collect_geo_evidence(),
            uwb=collect_uwb_evidence(challenge.witnesses),
        )

        response = await client.post(f"{SERVER}/evidence", json=evidence.model_dump())
        response.raise_for_status()
        print(response.json())

if __name__ == "__main__":
    asyncio.run(main())
