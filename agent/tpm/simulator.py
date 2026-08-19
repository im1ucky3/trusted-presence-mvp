import base64
import hashlib
import hmac
from shared.models import TPMEvidence

_SIM_KEY = b"trusted-presence-day1-demo-key"


def collect_tpm_evidence(nonce: str) -> TPMEvidence:
    pcrs = {
        "0": hashlib.sha256(b"firmware-demo").hexdigest(),
        "2": hashlib.sha256(b"option-rom-demo").hexdigest(),
        "4": hashlib.sha256(b"bootloader-demo").hexdigest(),
        "7": hashlib.sha256(b"secure-boot-demo").hexdigest(),
    }
    quote = f"nonce={nonce};pcr7={pcrs['7']}".encode()
    signature = hmac.new(_SIM_KEY, quote, hashlib.sha256).digest()
    return TPMEvidence(
        mode="simulated",
        quote_b64=base64.b64encode(quote).decode(),
        signature_b64=base64.b64encode(signature).decode(),
        pcrs=pcrs,
        secure_boot=True,
        nonce=nonce,
    )
