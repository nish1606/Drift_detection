from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import model_service_dep
from backend.core.auth import get_current_active_user
from backend.database.models import User
from backend.explainability.grad_cam_service import build_grad_cam_attribution
from backend.explainability.lime_service import LimeService
from backend.explainability.shap_service import ShapService
from backend.schemas.explainability import ExplainabilityResponse, GradCAMRequest, GradCAMResponse

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


def _loaded_model(model_service):
    predictor = model_service.predictor
    if predictor is None:
        return None
    return predictor._ensure_loaded()


@router.api_route("/shap", methods=["GET", "POST"], response_model=ExplainabilityResponse)
def shap_explanation(
    request: GradCAMRequest,
    model_service=Depends(model_service_dep),
    user: User = Depends(get_current_active_user),
) -> ExplainabilityResponse:
    model = _loaded_model(model_service)
    if model is None:
        raise HTTPException(status_code=501, detail="SHAP explanation requires a trained model")
    try:
        values = ShapService().explain(model, [request.features])
    except ImportError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    return ExplainabilityResponse(method="shap", values=values)


@router.api_route("/lime", methods=["GET", "POST"], response_model=ExplainabilityResponse)
def lime_explanation(
    request: GradCAMRequest,
    model_service=Depends(model_service_dep),
    user: User = Depends(get_current_active_user),
) -> ExplainabilityResponse:
    model = _loaded_model(model_service)
    if model is None:
        raise HTTPException(status_code=501, detail="LIME explanation requires a trained model")
    try:
        values = LimeService().explain(model, request.features)
    except ImportError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    return ExplainabilityResponse(method="lime", values=values)
