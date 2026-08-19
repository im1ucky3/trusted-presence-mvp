from __future__ import annotations

from threading import Lock

from shared.models import Challenge
from server.models import ChallengeRecord, ChallengeState, ClaimResult, ClaimStatus


class MemoryChallengeStore:
    """Thread-safe in-memory state store for the one-day MVP."""

    def __init__(self) -> None:
        self._challenges_by_session: dict[str, ChallengeRecord] = {}
        self._active_session_by_device: dict[str, str] = {}
        self._epochs_by_device: dict[str, int] = {}
        self._lock = Lock()

    def issue(
        self,
        *,
        device_id: str,
        session_id: str,
        nonce: str,
        witnesses: list[str],
        issued_at: int,
        expires_at: int,
    ) -> Challenge:
        """Atomically supersede the current active challenge and issue the next epoch."""
        with self._lock:
            old_session = self._active_session_by_device.get(device_id)
            if old_session is not None:
                old_record = self._challenges_by_session.get(old_session)
                if old_record is not None and old_record.state == ChallengeState.ISSUED:
                    if issued_at <= old_record.challenge.expires_at:
                        old_record.state = ChallengeState.SUPERSEDED
                self._active_session_by_device.pop(device_id, None)

            epoch = self._epochs_by_device.get(device_id, 0) + 1
            self._epochs_by_device[device_id] = epoch

            challenge = Challenge(
                session_id=session_id,
                device_id=device_id,
                epoch=epoch,
                nonce=nonce,
                witnesses=list(witnesses),
                issued_at=issued_at,
                expires_at=expires_at,
            )
            self._challenges_by_session[session_id] = ChallengeRecord(challenge=challenge)
            self._active_session_by_device[device_id] = session_id
            return challenge

    def claim(self, session_id: str, *, now: int) -> ClaimResult:
        """Atomically decide challenge status and consume an active valid challenge."""
        with self._lock:
            record = self._challenges_by_session.get(session_id)
            if record is None:
                return ClaimResult(status=ClaimStatus.UNKNOWN_SESSION)

            if record.state == ChallengeState.SUPERSEDED:
                return ClaimResult(status=ClaimStatus.SUPERSEDED, record=record)

            if record.state == ChallengeState.CONSUMED:
                return ClaimResult(status=ClaimStatus.REPLAY, record=record)

            if now > record.challenge.expires_at:
                if self._active_session_by_device.get(record.challenge.device_id) == session_id:
                    self._active_session_by_device.pop(record.challenge.device_id, None)
                return ClaimResult(status=ClaimStatus.EXPIRED, record=record)

            record.state = ChallengeState.CONSUMED
            if self._active_session_by_device.get(record.challenge.device_id) == session_id:
                self._active_session_by_device.pop(record.challenge.device_id, None)
            return ClaimResult(status=ClaimStatus.OK, record=record)

    def get_record(self, session_id: str) -> ChallengeRecord | None:
        with self._lock:
            return self._challenges_by_session.get(session_id)

    def active_session_for_device(self, device_id: str) -> str | None:
        with self._lock:
            return self._active_session_by_device.get(device_id)

    def clear(self) -> None:
        with self._lock:
            self._challenges_by_session.clear()
            self._active_session_by_device.clear()
            self._epochs_by_device.clear()
