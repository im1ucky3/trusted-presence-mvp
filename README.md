# TrustedPresence MVP

One-day team MVP for continuous trusted presence verification.

## Goal for today
A working end-to-end demo where a server issues a fresh challenge with a random 3-of-5 witness set, the agent returns TPM/GEO/UWB evidence, and the server returns `TRUSTED` or `DENIED`.

Hardware is **not required** for the first milestone. TPM, GEO and UWB have simulation adapters. Real adapters can replace them without changing the shared protocol.

## Team ownership
- Person 1: `agent/tpm/` + TPM verification logic
- Person 2: `agent/geo/`, `agent/uwb/`
- Person 3: `server/`, integration, shared protocol

Do not change `shared/models.py` without team agreement.

## Run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn server.main:app --reload
```
In another terminal:
```bash
python -m agent.main
```
Expected result:
```text
{'trusted': True, 'reasons': ['all_checks_passed'], ...}
```

## Branches
- `feature/tpm`
- `feature/location`
- `feature/server`

## Integration contract
The server sends `Challenge`; the agent sends `PresenceEvidence`. Schemas are in `shared/models.py`.

## Day-1 definition of done
1. End-to-end simulated flow works.
2. Real TPM presence/Secure Boot check works on the ASUS where possible.
3. GEO geofence accepts inside and rejects outside/stale coordinates.
4. UWB simulator supports 5 anchors and server-selected random 3-of-5 witnesses.
5. Replay of an already accepted challenge is rejected.
6. One final demo command shows TRUSTED/DENIED.
