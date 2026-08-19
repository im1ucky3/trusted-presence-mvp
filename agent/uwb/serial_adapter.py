from shared.models import UWBEvidence

from .base import UwbAdapter


class UwbSerialAdapter(UwbAdapter):
    """
    Placeholder for future real UWB hardware.

    Expected future flow:

    serial device
        ->
    anchor ranging
        ->
    distance / quality
        ->
    position estimation
        ->
    UWBEvidence

    The public interface intentionally matches
    UwbSimulator.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
    ):
        self.port = port
        self.baudrate = baudrate

    def collect(
        self,
        witnesses: list[str],
    ) -> UWBEvidence:

        raise NotImplementedError(
            "Real UWB serial hardware " "is not connected in the MVP"
        )
