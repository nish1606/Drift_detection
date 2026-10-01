from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from backend.api.deps import model_service_dep
from backend.core.auth import get_current_active_user
from backend.database.models import User
from backend.explainability.grad_cam_service import build_grad_cam_attribution
from backend.explainability.lime_service import LimeService
from backend.explainability.shap_service import ShapService
from backend.schemas.explainability import (
    ExplainabilityRequest,
    ExplainabilityResponse,
    GradCAMRequest,
    GradCAMResponse,
)

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


@router.post("/shap", response_model=ExplainabilityResponse, operation_id="shap_explanation_post")
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


@router.get("/shap", response_model=ExplainabilityResponse, operation_id="shap_explanation_get")
def shap_explanation_query(
    features: str = Query(..., description="JSON object of transaction features"),
    model_name: str = Query(default="fraud_classifier"),
    model_version: str | None = Query(default=None),
    model_service=Depends(model_service_dep),
    user: User = Depends(get_current_active_user),
) -> ExplainabilityResponse:
    model = _loaded_model(model_service)
    if model is None:
        raise HTTPException(status_code=501, detail="SHAP explanation requires a trained model")
    parsed = _parse_features(features)
    try:
        values = ShapService().explain(model, [parsed])
    except ImportError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    return ExplainabilityResponse(method="shap", values=values)


@router.post("/lime", response_model=ExplainabilityResponse, operation_id="lime_explanation_post")
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


@router.get("/lime", response_model=ExplainabilityResponse, operation_id="lime_explanation_get")
def lime_explanation_query(
    features: str = Query(..., description="JSON object of transaction features"),
    model_name: str = Query(default="fraud_classifier"),
    model_version: str | None = Query(default=None),
    model_service=Depends(model_service_dep),
    user: User = Depends(get_current_active_user),
) -> ExplainabilityResponse:
    model = _loaded_model(model_service)
    if model is None:
        raise HTTPException(status_code=501, detail="LIME explanation requires a trained model")
    parsed = _parse_features(features)
    try:
        values = LimeService().explain(model, parsed)
    except ImportError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    return ExplainabilityResponse(method="lime", values=values)


def _parse_features(raw: str) -> dict[str, object]:
    try:
        return ExplainabilityRequest(features=raw).feature_dict()
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid 'features' query parameter: {error}") from error
