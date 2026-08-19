# One-day execution plan

## 09:00–09:30 — Everyone
- Clone repo, create venv, run baseline demo.
- Read `shared/models.py`.
- Confirm branch ownership.
- No schema changes after this checkpoint without team agreement.

## 09:30–13:00 — Parallel work
- Person 1: TPM/Secure Boot + verifier.
- Person 2: GEO/UWB + tests.
- Person 3: challenge/evidence server + replay/integration tests.

## 13:00 — Integration checkpoint
- Each person commits a runnable state.
- Integration owner merges or cherry-picks only working code.
- Baseline command must still return TRUSTED.

## 13:30–16:30 — Realism + negative cases
- TPM real checks where practical.
- GEO inside/outside/stale cases.
- UWB 3-of-5 simulator, outside-room case.
- Server replay and mismatch rejection.

## 16:30–18:00 — Final integration
- Freeze schema.
- Run tests.
- Prepare demo sequence and screenshots/logs.

## Final demo
1. Valid challenge -> TRUSTED.
2. Replay same evidence -> DENIED.
3. GEO outside -> DENIED.
4. UWB outside/wrong witnesses -> DENIED.
5. TPM/Secure Boot failure simulation or real mismatch -> DENIED.
