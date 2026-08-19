from __future__ import annotations

import secrets
import time
from collections.abc import Callable

from shared.models import Challenge
from server.challenge_store import MemoryChallengeStore
from server.config import (
    AVAILABLE_WITNESSES,
    CHALLENGE_TTL_SECONDS,
    NONCE_BYTES,
    SESSION_ID_BYTES,
    WITNESS_QUORUM_SIZE,
)


class ChallengeService:
    def __init__(
        self,
        store: MemoryChallengeStore,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._store = store
        self._clock = clock
        self._rng = secrets.SystemRandom()

    def issue(self, device_id: str) -> Challenge:
        now = int(self._clock())
        session_id = secrets.token_hex(SESSION_ID_BYTES)
        nonce = secrets.token_hex(NONCE_BYTES)
        witnesses = self._rng.sample(list(AVAILABLE_WITNESSES), WITNESS_QUORUM_SIZE)

        return self._store.issue(
            device_id=device_id,
            session_id=session_id,
            nonce=nonce,
            witnesses=witnesses,
            issued_at=now,
            expires_at=now + CHALLENGE_TTL_SECONDS,
        )
