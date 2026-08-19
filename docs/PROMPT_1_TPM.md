# Person 1 — TPM / Device Trust

You are implementing the TPM/device-trust module of a one-day cybersecurity MVP called TrustedPresence.

Repository contract: do not redesign the whole system. Your ownership is `agent/tpm/` and TPM verification support on the server. `shared/models.py` is the contract and should only be changed if absolutely necessary.

## Today’s goal
Replace the simulated TPM path with the strongest real implementation that can be completed today on an ASUS ROG Strix G16, while keeping the simulator as fallback.

## Required outputs
1. Detect TPM 2.0 and Secure Boot on Windows.
2. Document commands `Get-Tpm`, `Confirm-SecureBootUEFI`, and safe checks only. Do NOT clear/reset TPM.
3. If direct real TPM Quote is practical in the available environment, implement it using standard TPM tooling/APIs. If not, implement a clean adapter interface and keep quote simulation but use real TPM/Secure Boot status.
4. Implement enrollment metadata: `device_id`, AK public material when available, approved PCR policy/baseline format.
5. Implement server-side verification function returning valid/invalid with reasons.
6. Ensure the challenge nonce is bound to the evidence and replay is rejected.
7. Add tests for: valid proof, wrong nonce, Secure Boot false, modified PCR/baseline mismatch.

## Interface to preserve
`collect_tpm_evidence(nonce: str) -> TPMEvidence`

TPMEvidence fields are defined in `shared/models.py`.

## Priority order
A. End-to-end compatibility first.
B. Real TPM/Secure Boot detection second.
C. Real Quote/PCR if feasible today.
D. Do not spend the day fighting hardware APIs; preserve a simulator fallback.

## Git workflow
Work only on branch `feature/tpm`. Commit small changes. Do not edit GEO/UWB/server code except the TPM verifier integration point.

At the end, provide: changed files, exact run commands, what is real vs simulated, and known limitations.
