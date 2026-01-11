from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from src.middleware.signature.registry import registry

class SignatureVerificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        verifier = registry.get_verifier(request.url.path)
        if verifier:
            await verifier.verify(request)
            
        return await call_next(request)
