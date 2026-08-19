# Person 3 — Server / Protocol / Integration

You are the integration owner for a one-day cybersecurity MVP called TrustedPresence.

Your ownership is `server/`, integration tests, and coordination of `shared/models.py`. Do not rewrite TPM or GEO/UWB modules.

## Today’s goal
Make the full flow work reliably even while TPM/GEO/UWB are simulated, then integrate real adapters as teammates finish them.

## Required protocol
1. `GET /challenge/{device_id}` returns:
   - `session_id`
   - `device_id`
   - monotonically increasing `epoch`
   - cryptographically random `nonce`
   - random 3-of-5 `witnesses`
   - `issued_at`, `expires_at`
2. `POST /evidence` validates the `PresenceEvidence` contract.
3. Reject unknown/expired/replayed challenges.
4. Require exact device/session/epoch/nonce match.
5. Require the returned UWB witness set to match the server-selected witness set.
6. Combine TPM, GEO, UWB checks into `TRUSTED`/`DENIED` plus machine-readable reasons.
7. Successful challenges are one-time-use.
8. Add integration tests for success, replay, wrong nonce, GEO outside, UWB outside, wrong witness set.

## Day-1 security rule
Do not invent a permanent master access key today. The deliverable is a verifier/protocol MVP. If time remains, issue only a short-lived random demo authorization token after successful verification.

## Compatibility
Do not break `agent/main.py`. `shared/models.py` is the protocol contract; coordinate any schema change with both teammates.

## Git workflow
Work on `feature/server`. You are the integration owner: merge completed branches into `main`, resolve only interface conflicts, and run the complete test/demo flow after every merge.

## Definition of done
With the server running, `python -m agent.main` produces TRUSTED. Then demonstrate at least three DENIED cases: replay, wrong location, wrong witness/nonce.

At the end, provide: changed files, run commands, API examples, tests executed, and remaining limitations.
