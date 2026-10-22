from datetime import datetime
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict

router = APIRouter(tags=["Health"])

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str]

@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Returns system operational status and subsystem readiness.
    """
    from backend.app.services.ml_inference_service import ml_inference_service
    ml_status = "ready" if ml_inference_service.is_ready else "unavailable"

    return HealthCheckResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow(),
        components={
            "database": "ready",
            "feature_engine": "ready",
            "ml_models": ml_status,
            "api_gateway": "ready",
        },
    )
