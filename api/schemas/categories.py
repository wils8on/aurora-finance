"""Schemas HTTP de categorias e subcategorias."""

from pydantic import BaseModel, ConfigDict

from models import CategoryType


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: CategoryType


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType
    is_active: bool


class SubcategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class SubcategoryResponse(BaseModel):
    id: int
    name: str
    is_active: bool
