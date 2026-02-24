from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.kb_bc.article.domain.entities import (
    Article,
    ArticleCategory,
    ArticleVersion,
)
from src.kb_bc.article.domain.enums import ArticleStatus
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface
from src.kb_bc.article.infrastructure.models import (
    ArticleCategoryModel,
    ArticleModel,
    ArticleVersionModel,
)


class ArticleRepository(ArticleRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    # --- Articles ---

    def save(self, article: Article) -> None:
        existing = self.session.execute(
            select(ArticleModel).where(ArticleModel.id == article.id)
        ).scalar_one_or_none()

        if existing:
            existing.company_id = article.company_id
            existing.title = article.title
            existing.slug = article.slug
            existing.content = article.content
            existing.excerpt = article.excerpt
            existing.category_id = article.category_id
            existing.status = article.status.value
            existing.author_id = article.author_id
            existing.view_count = article.view_count
            existing.published_at = article.published_at
        else:
            # Handle slug collision
            article.slug = self._resolve_slug(article.slug, article.company_id)
            model = ArticleModel(
                id=article.id,
                company_id=article.company_id,
                title=article.title,
                slug=article.slug,
                content=article.content,
                excerpt=article.excerpt,
                category_id=article.category_id,
                status=article.status.value,
                author_id=article.author_id,
                view_count=article.view_count,
                published_at=article.published_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_by_id(
        self, article_id: str, company_id: str
    ) -> Optional[Article]:
        model = self.session.execute(
            select(ArticleModel).where(
                ArticleModel.id == article_id,
                ArticleModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_by_slug(
        self, slug: str, company_id: str
    ) -> Optional[Article]:
        model = self.session.execute(
            select(ArticleModel).where(
                ArticleModel.slug == slug,
                ArticleModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[Article], int]:
        query = select(ArticleModel).where(
            ArticleModel.company_id == company_id
        )

        if filters.get("status"):
            query = query.where(ArticleModel.status == filters["status"])
        if filters.get("category_id"):
            query = query.where(
                ArticleModel.category_id == filters["category_id"]
            )
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.where(
                ArticleModel.title.ilike(search_term)
                | ArticleModel.content.ilike(search_term)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(ArticleModel.created_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def find_published(
        self, company_id: str, filters: dict
    ) -> tuple[list[Article], int]:
        query = select(ArticleModel).where(
            ArticleModel.company_id == company_id,
            ArticleModel.status == ArticleStatus.PUBLISHED.value,
        )

        if filters.get("category_id"):
            query = query.where(
                ArticleModel.category_id == filters["category_id"]
            )
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.where(
                ArticleModel.title.ilike(search_term)
                | ArticleModel.content.ilike(search_term)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(count_query).scalar() or 0

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        offset = (page - 1) * page_size
        query = query.order_by(ArticleModel.published_at.desc())
        query = query.offset(offset).limit(page_size)

        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    def delete(self, article_id: str, company_id: str) -> None:
        self.session.execute(
            delete(ArticleVersionModel).where(
                ArticleVersionModel.article_id == article_id
            )
        )
        self.session.execute(
            delete(ArticleModel).where(
                ArticleModel.id == article_id,
                ArticleModel.company_id == company_id,
            )
        )
        self.session.flush()

    def search(
        self, company_id: str, query: str, limit: int = 20
    ) -> list[Article]:
        search_term = f"%{query}%"
        stmt = (
            select(ArticleModel)
            .where(
                ArticleModel.company_id == company_id,
                ArticleModel.status == ArticleStatus.PUBLISHED.value,
                ArticleModel.title.ilike(search_term)
                | ArticleModel.content.ilike(search_term),
            )
            .order_by(ArticleModel.view_count.desc())
            .limit(limit)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def suggest(
        self, company_id: str, text: str, limit: int = 5
    ) -> list[Article]:
        # Use word-level matching for better suggestions
        words = [w.strip() for w in text.split() if len(w.strip()) > 2]
        if not words:
            return []

        stmt = select(ArticleModel).where(
            ArticleModel.company_id == company_id,
            ArticleModel.status == ArticleStatus.PUBLISHED.value,
        )

        # Match any word in title or content
        from sqlalchemy import or_

        conditions = []
        for word in words[:10]:  # Limit to first 10 words
            pattern = f"%{word}%"
            conditions.append(ArticleModel.title.ilike(pattern))
            conditions.append(ArticleModel.content.ilike(pattern))
        stmt = stmt.where(or_(*conditions))
        stmt = stmt.order_by(ArticleModel.view_count.desc()).limit(limit)

        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    # --- Versions ---

    def save_version(self, version: ArticleVersion) -> None:
        model = ArticleVersionModel(
            id=version.id,
            article_id=version.article_id,
            version_number=version.version_number,
            title=version.title,
            content=version.content,
            edited_by=version.edited_by,
        )
        self.session.add(model)
        self.session.flush()

    def get_versions(self, article_id: str) -> list[ArticleVersion]:
        models = (
            self.session.execute(
                select(ArticleVersionModel)
                .where(ArticleVersionModel.article_id == article_id)
                .order_by(ArticleVersionModel.version_number.desc())
            )
            .scalars()
            .all()
        )
        return [
            ArticleVersion(
                id=m.id,
                article_id=m.article_id,
                version_number=m.version_number,
                title=m.title,
                content=m.content,
                edited_by=m.edited_by,
                created_at=m.created_at,
            )
            for m in models
        ]

    def get_latest_version_number(self, article_id: str) -> int:
        result = self.session.execute(
            select(func.max(ArticleVersionModel.version_number)).where(
                ArticleVersionModel.article_id == article_id
            )
        ).scalar()
        return result or 0

    # --- Categories ---

    def save_category(self, category: ArticleCategory) -> None:
        existing = self.session.execute(
            select(ArticleCategoryModel).where(
                ArticleCategoryModel.id == category.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.name = category.name
            existing.slug = category.slug
            existing.description = category.description
            existing.sort_order = category.sort_order
        else:
            model = ArticleCategoryModel(
                id=category.id,
                company_id=category.company_id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                sort_order=category.sort_order,
            )
            self.session.add(model)
        self.session.flush()

    def find_category_by_id(
        self, category_id: str, company_id: str
    ) -> Optional[ArticleCategory]:
        model = self.session.execute(
            select(ArticleCategoryModel).where(
                ArticleCategoryModel.id == category_id,
                ArticleCategoryModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_category(model)

    def find_all_categories(
        self, company_id: str
    ) -> list[ArticleCategory]:
        models = (
            self.session.execute(
                select(ArticleCategoryModel)
                .where(ArticleCategoryModel.company_id == company_id)
                .order_by(ArticleCategoryModel.sort_order.asc())
            )
            .scalars()
            .all()
        )
        return [self._to_category(m) for m in models]

    def delete_category(
        self, category_id: str, company_id: str
    ) -> None:
        self.session.execute(
            delete(ArticleCategoryModel).where(
                ArticleCategoryModel.id == category_id,
                ArticleCategoryModel.company_id == company_id,
            )
        )
        self.session.flush()

    def count_articles_in_category(self, category_id: str) -> int:
        result = self.session.execute(
            select(func.count()).where(
                ArticleModel.category_id == category_id
            )
        ).scalar()
        return result or 0

    # --- Helpers ---

    def _resolve_slug(self, slug: str, company_id: str) -> str:
        base_slug = slug
        counter = 1
        while True:
            existing = self.session.execute(
                select(ArticleModel.id).where(
                    ArticleModel.slug == slug,
                    ArticleModel.company_id == company_id,
                )
            ).scalar_one_or_none()
            if not existing:
                return slug
            counter += 1
            slug = f"{base_slug}-{counter}"

    def _to_entity(self, model: ArticleModel) -> Article:
        return Article(
            id=model.id,
            company_id=model.company_id,
            title=model.title,
            slug=model.slug,
            content=model.content,
            status=ArticleStatus(model.status),
            author_id=model.author_id,
            view_count=model.view_count,
            excerpt=model.excerpt,
            category_id=model.category_id,
            published_at=model.published_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_category(self, model: ArticleCategoryModel) -> ArticleCategory:
        return ArticleCategory(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            slug=model.slug,
            sort_order=model.sort_order,
            description=model.description,
            created_at=model.created_at,
        )
