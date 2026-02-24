from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Requests ---


class CreateArticleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    category_id: Optional[str] = None


class UpdateArticleRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    category_id: Optional[str] = None


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    sort_order: int = 0


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    sort_order: Optional[int] = None


# --- Responses ---


class ArticleListItemResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    status: str
    author_id: str
    author_name: Optional[str] = None
    view_count: int = 0
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ArticleDetailResponse(BaseModel):
    id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    status: str
    author_id: str
    author_name: Optional[str] = None
    view_count: int = 0
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    sort_order: int = 0
    article_count: int = 0


class ArticleVersionResponse(BaseModel):
    id: str
    version_number: int
    title: str
    content: str
    edited_by: str
    editor_name: Optional[str] = None
    created_at: Optional[datetime] = None
