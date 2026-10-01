from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import db_dep
from backend.core.auth import get_current_active_user
from backend.database.models import User
from backend.response.freeze import ModelResponseService
from backend.schemas.response import ResponseStateRequest, ResponseStateResponse

router = APIRouter(prefix="/models", tags=["response"])


def _service(db, user: User) -> ModelResponseService:
    return ModelResponseService(db, actor=user.username)


@router.get("/{model_name}/response-state", response_model=ResponseStateResponse)
def get_response_state(
    model_name: str,
    db=Depends(db_dep),
    user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    return _service(db, user).state(model_name)


@router.post("/{model_name}/freeze", response_model=ResponseStateResponse)
def freeze_model(
    model_name: str,
    request: ResponseStateRequest,
    db=Depends(db_dep),
    user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    return _service(db, user).freeze(model_name, request.reason)


@router.post("/{model_name}/unfreeze", response_model=ResponseStateResponse)
def unfreeze_model(
    model_name: str,
    request: ResponseStateRequest,
    db=Depends(db_dep),
    user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    return _service(db, user).unfreeze(model_name, request.reason)


@router.post("/{model_name}/rollback", response_model=ResponseStateResponse)
def rollback_model(
    model_name: str,
    request: ResponseStateRequest,
    db=Depends(db_dep),
    user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    return _service(db, user).rollback(model_name, request.reason)