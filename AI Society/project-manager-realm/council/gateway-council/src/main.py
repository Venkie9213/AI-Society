from fastapi import FastAPI, Request
from src.config.settings import settings
from src.middleware.correlation import CorrelationMiddleware
from src.middleware.signature import SignatureVerificationMiddleware
from src.middleware.tenant import TenantResolutionMiddleware
from src.api.router import proxy_router
from src.api.endpoints.discovery import router as discovery_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# Register Middleware
app.add_middleware(CorrelationMiddleware)
app.add_middleware(SignatureVerificationMiddleware)
app.add_middleware(TenantResolutionMiddleware)

# Register Routers
app.include_router(proxy_router)
app.include_router(discovery_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
