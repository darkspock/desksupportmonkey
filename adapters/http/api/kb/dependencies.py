from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.kb_bc.article.infrastructure.repository import ArticleRepository


def get_article_repo(
    db: Session = Depends(get_db),
) -> ArticleRepository:
    return ArticleRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)
