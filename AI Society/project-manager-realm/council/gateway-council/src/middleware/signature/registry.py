from typing import Dict, Optional
from src.middleware.signature.base import SignatureVerifier
from src.middleware.signature.slack import SlackSignatureVerifier

class SignatureVerifierRegistry:
    def __init__(self):
        self._verifiers: Dict[str, SignatureVerifier] = {
            "/webhooks/slack": SlackSignatureVerifier()
        }

    def get_verifier(self, path: str) -> Optional[SignatureVerifier]:
        for prefix, verifier in self._verifiers.items():
            if path.startswith(prefix):
                return verifier
        return None

registry = SignatureVerifierRegistry()
