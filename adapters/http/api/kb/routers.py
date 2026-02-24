from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.kb.dependencies import get_article_repo, get_user_repo
from adapters.http.api.kb.schemas import (
    ArticleDetailResponse,
    ArticleListItemResponse,
    ArticleVersionResponse,
    CategoryResponse,
    CreateArticleRequest,
    CreateCategoryRequest,
    UpdateArticleRequest,
    UpdateCategoryRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.kb_bc.article.application.commands.archive_article import (
    ArchiveArticleCommand,
    ArchiveArticleCommandHandler,
)
from src.kb_bc.article.application.commands.create_article import (
    CreateArticleCommand,
    CreateArticleCommandHandler,
)
from src.kb_bc.article.application.commands.create_category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from src.kb_bc.article.application.commands.delete_article import (
    DeleteArticleCommand,
    DeleteArticleCommandHandler,
)
from src.kb_bc.article.application.commands.delete_category import (
    DeleteCategoryCommand,
    DeleteCategoryCommandHandler,
)
from src.kb_bc.article.application.commands.publish_article import (
    PublishArticleCommand,
    PublishArticleCommandHandler,
)
from src.kb_bc.article.application.commands.restore_article import (
    RestoreArticleCommand,
    RestoreArticleCommandHandler,
)
from src.kb_bc.article.application.commands.unpublish_article import (
    UnpublishArticleCommand,
    UnpublishArticleCommandHandler,
)
from src.kb_bc.article.application.commands.update_article import (
    UpdateArticleCommand,
    UpdateArticleCommandHandler,
)
from src.kb_bc.article.application.commands.update_category import (
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from src.kb_bc.article.application.queries.get_article_detail import (
    GetArticleDetailQuery,
    GetArticleDetailQueryHandler,
)
from src.kb_bc.article.application.queries.get_article_versions import (
    GetArticleVersionsQuery,
    GetArticleVersionsQueryHandler,
)
from src.kb_bc.article.application.queries.list_articles import (
    ListArticlesQuery,
    ListArticlesQueryHandler,
)
from src.kb_bc.article.application.queries.list_categories import (
    ListCategoriesQuery,
    ListCategoriesQueryHandler,
)
from src.kb_bc.article.domain.exceptions import (
    ArticleDraftOnlyDeleteError,
    ArticleNotFoundError,
    CategoryHasArticlesError,
    CategoryNotFoundError,
    InvalidArticleStatusTransitionError,
)
from src.kb_bc.article.infrastructure.repository import ArticleRepository

router = APIRouter(prefix="/api/v1/kb", tags=["knowledge-base"])


def _user_name_resolver_factory(user_repo: UserRepository):
    def resolver(user_ids: list[str]) -> dict[str, str]:
        users = user_repo.find_by_ids(user_ids)
        result: dict[str, str] = {}
        for uid, user in users.items():
            if user.name and user.name.strip():
                result[uid] = user.name.strip()
            else:
                local = (
                    user.email.split("@", 1)[0]
                    .replace(".", " ")
                    .replace("_", " ")
                    .replace("-", " ")
                    .strip()
                )
                result[uid] = " ".join(
                    part.capitalize() for part in local.split()
                ) or user.email
        return result

    return resolver


def _category_name_resolver_factory(article_repo: ArticleRepository):
    def resolver(category_ids: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for cid in category_ids:
            # We use a simplified approach — categories are per-company
            # but we only need the name for display
            from sqlalchemy import select
            from src.kb_bc.article.infrastructure.models import ArticleCategoryModel

            model = article_repo.session.execute(
                select(ArticleCategoryModel).where(
                    ArticleCategoryModel.id == cid
                )
            ).scalar_one_or_none()
            if model:
                result[cid] = model.name
        return result

    return resolver


# --- Search & suggest (must be before /{article_id}) ---


@router.get("/search")
def search_articles(
    q: str = QueryParam(min_length=1),
    limit: int = QueryParam(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    articles = article_repo.search(current_user.company_id, q, limit)
    name_resolver = _user_name_resolver_factory(user_repo)
    user_ids = list({a.author_id for a in articles})
    name_map = name_resolver(user_ids) if user_ids else {}

    return {
        "data": [
            ArticleListItemResponse(
                id=a.id,
                title=a.title,
                slug=a.slug,
                excerpt=a.excerpt,
                status=a.status.value,
                author_id=a.author_id,
                author_name=name_map.get(a.author_id),
                view_count=a.view_count,
                published_at=a.published_at,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in articles
        ]
    }


@router.get("/suggest")
def suggest_articles(
    text: str = QueryParam(min_length=3),
    limit: int = QueryParam(5, ge=1, le=10),
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    articles = article_repo.suggest(current_user.company_id, text, limit)
    return {
        "data": [
            ArticleListItemResponse(
                id=a.id,
                title=a.title,
                slug=a.slug,
                excerpt=a.excerpt,
                status=a.status.value,
                author_id=a.author_id,
                view_count=a.view_count,
                published_at=a.published_at,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in articles
        ]
    }


@router.get("/public")
def list_public_articles(
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(20, ge=1, le=100),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    filters = {
        "page": page,
        "page_size": page_size,
        "category_id": category_id,
        "search": search,
    }
    articles, total = article_repo.find_published(
        current_user.company_id, filters
    )
    name_resolver = _user_name_resolver_factory(user_repo)
    user_ids = list({a.author_id for a in articles})
    name_map = name_resolver(user_ids) if user_ids else {}

    return {
        "data": [
            ArticleListItemResponse(
                id=a.id,
                title=a.title,
                slug=a.slug,
                excerpt=a.excerpt,
                category_id=a.category_id,
                status=a.status.value,
                author_id=a.author_id,
                author_name=name_map.get(a.author_id),
                view_count=a.view_count,
                published_at=a.published_at,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in articles
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


# --- Categories ---


@router.get("/categories")
def list_categories(
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = ListCategoriesQueryHandler(article_repo=article_repo)
    categories = handler.handle(
        ListCategoriesQuery(company_id=current_user.company_id)
    )
    return {
        "data": [
            CategoryResponse.model_validate(c.__dict__).model_dump()
            for c in categories
        ]
    }


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    body: CreateCategoryRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    category_id = str(ulid.new())
    handler = CreateCategoryCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            CreateCategoryCommand(
                category_id=category_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
                sort_order=body.sort_order,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    cat = article_repo.find_category_by_id(
        category_id, current_user.company_id
    )
    return {
        "data": CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            sort_order=cat.sort_order,
            article_count=0,
        ).model_dump()
    }


@router.put("/categories/{category_id}")
def update_category(
    category_id: str,
    body: UpdateCategoryRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = UpdateCategoryCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            UpdateCategoryCommand(
                category_id=category_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
                sort_order=body.sort_order,
            )
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return {"message": "Category updated"}


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = DeleteCategoryCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            DeleteCategoryCommand(
                category_id=category_id,
                company_id=current_user.company_id,
            )
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    except CategoryHasArticlesError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category has articles and cannot be deleted",
        )


# --- Article CRUD ---


@router.post("/articles", status_code=status.HTTP_201_CREATED)
def create_article(
    body: CreateArticleRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    article_id = str(ulid.new())
    handler = CreateArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            CreateArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
                title=body.title,
                content=body.content,
                author_id=current_user.id,
                excerpt=body.excerpt,
                category_id=body.category_id,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetArticleDetailQueryHandler(
        article_repo=article_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        category_name_resolver=_category_name_resolver_factory(article_repo),
    )
    detail = detail_handler.handle(
        GetArticleDetailQuery(
            article_id=article_id, company_id=current_user.company_id
        )
    )
    return {
        "data": ArticleDetailResponse.model_validate(
            detail.__dict__
        ).model_dump(mode="json")
    }


@router.get("/articles")
def list_articles(
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(20, ge=1, le=100),
    status_filter: Optional[str] = QueryParam(None, alias="status"),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = ListArticlesQueryHandler(
        article_repo=article_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        category_name_resolver=_category_name_resolver_factory(article_repo),
    )
    dtos, total = handler.handle(
        ListArticlesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=status_filter,
            category_id=category_id,
            search=search,
        )
    )
    return {
        "data": [
            ArticleListItemResponse.model_validate(d.__dict__).model_dump(
                mode="json"
            )
            for d in dtos
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    detail_handler = GetArticleDetailQueryHandler(
        article_repo=article_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        category_name_resolver=_category_name_resolver_factory(article_repo),
    )
    try:
        detail = detail_handler.handle(
            GetArticleDetailQuery(
                article_id=article_id,
                company_id=current_user.company_id,
                increment_view=True,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return {
        "data": ArticleDetailResponse.model_validate(
            detail.__dict__
        ).model_dump(mode="json")
    }


@router.put("/articles/{article_id}")
def update_article(
    article_id: str,
    body: UpdateArticleRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = UpdateArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            UpdateArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
                edited_by=current_user.id,
                title=body.title,
                content=body.content,
                excerpt=body.excerpt,
                category_id=body.category_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetArticleDetailQueryHandler(
        article_repo=article_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        category_name_resolver=_category_name_resolver_factory(article_repo),
    )
    detail = detail_handler.handle(
        GetArticleDetailQuery(
            article_id=article_id, company_id=current_user.company_id
        )
    )
    return {
        "data": ArticleDetailResponse.model_validate(
            detail.__dict__
        ).model_dump(mode="json")
    }


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = DeleteArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            DeleteArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except ArticleDraftOnlyDeleteError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft articles can be deleted",
        )


# --- Article Status Actions ---


@router.post("/articles/{article_id}/publish")
def publish_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = PublishArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            PublishArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except InvalidArticleStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Article published"}


@router.post("/articles/{article_id}/unpublish")
def unpublish_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = UnpublishArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            UnpublishArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except InvalidArticleStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Article unpublished"}


@router.post("/articles/{article_id}/archive")
def archive_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = ArchiveArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            ArchiveArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except InvalidArticleStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Article archived"}


@router.post("/articles/{article_id}/restore")
def restore_article(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
):
    handler = RestoreArticleCommandHandler(article_repo=article_repo)
    try:
        handler.handle(
            RestoreArticleCommand(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    except InvalidArticleStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Article restored"}


# --- Article Versions ---


@router.get("/articles/{article_id}/versions")
def get_article_versions(
    article_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    article_repo: ArticleRepository = Depends(get_article_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = GetArticleVersionsQueryHandler(
        article_repo=article_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    try:
        versions = handler.handle(
            GetArticleVersionsQuery(
                article_id=article_id,
                company_id=current_user.company_id,
            )
        )
    except ArticleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return {
        "data": [
            ArticleVersionResponse.model_validate(v.__dict__).model_dump(
                mode="json"
            )
            for v in versions
        ]
    }
