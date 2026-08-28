from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import model_service_dep
from backend.core.auth import get_current_active_user
from backend.database.models import User
from backend.explainability.grad_cam_service import build_grad_cam_attribution
from backend.schemas.explainability import GradCAMRequest, GradCAMResponse

router = APIRouter(prefix="/explainability", tags=["explainability"])


@router.post("/grad-cam", response_model=GradCAMResponse)
def grad_cam(
    request: GradCAMRequest,
    model_service=Depends(model_service_dep),
    user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    prediction = model_service.predict(
        model_name=request.model_name,
        model_version=request.model_version,
        features=request.features,
    )
    return build_grad_cam_attribution(prediction)
