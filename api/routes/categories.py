"""Endpoints de categorias e subcategorias."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_session
from api.schemas import (
    CategoryCreate,
    CategoryResponse,
    SubcategoryCreate,
    SubcategoryResponse,
)
from models import User
from services import CategoryService, ReferenceQueryService

router = APIRouter(prefix="/categories", tags=["categories"])


def _category_response(item) -> CategoryResponse:
    category_type = (
        item.category_type if hasattr(item, "category_type") else item.type
    )
    return CategoryResponse(
        id=item.id,
        name=item.name,
        type=category_type,
        is_active=item.is_active,
    )


def _subcategory_response(item) -> SubcategoryResponse:
    return SubcategoryResponse(id=item.id, name=item.name, is_active=item.is_active)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CategoryResponse]:
    items = ReferenceQueryService(session).list_categories(current_user.id)
    return [_category_response(item) for item in items]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategoryResponse:
    category = CategoryService(session).create_category(
        user_id=current_user.id,
        name=payload.name,
        category_type=payload.type,
    )
    return _category_response(category)


@router.get(
    "/{category_id}/subcategories",
    response_model=list[SubcategoryResponse],
)
def list_subcategories(
    category_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SubcategoryResponse]:
    items = ReferenceQueryService(session).list_subcategories(
        current_user.id,
        category_id,
    )
    return [_subcategory_response(item) for item in items]


@router.post(
    "/{category_id}/subcategories",
    response_model=SubcategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subcategory(
    category_id: int,
    payload: SubcategoryCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubcategoryResponse:
    subcategory = CategoryService(session).create_subcategory(
        user_id=current_user.id,
        category_id=category_id,
        name=payload.name,
    )
    return _subcategory_response(subcategory)
