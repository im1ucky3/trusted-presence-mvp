from abc import ABC, abstractmethod

from shared.models import UWBEvidence


class UwbAdapter(ABC):

    @abstractmethod
    def collect(
        self,
        witnesses: list[str],
    ) -> UWBEvidence:
        pass
