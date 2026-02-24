import pytest
from unittest.mock import MagicMock

from src.kb_bc.article.application.commands.publish_article import (
    PublishArticleCommand,
    PublishArticleCommandHandler,
)
from src.kb_bc.article.domain.entities import Article
from src.kb_bc.article.domain.enums import ArticleStatus
from src.kb_bc.article.domain.exceptions import (
    ArticleNotFoundError,
    InvalidArticleStatusTransitionError,
)


class TestPublishArticleCommandHandler:
    def test_publishes_draft_article(self):
        repo = MagicMock()
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
            id="art1",
        )
        repo.find_by_id.return_value = article

        handler = PublishArticleCommandHandler(article_repo=repo)
        handler.handle(
            PublishArticleCommand(article_id="art1", company_id="comp1")
        )

        repo.save.assert_called_once()
        assert article.status == ArticleStatus.PUBLISHED

    def test_raises_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = PublishArticleCommandHandler(article_repo=repo)
        with pytest.raises(ArticleNotFoundError):
            handler.handle(
                PublishArticleCommand(article_id="art1", company_id="comp1")
            )

    def test_raises_invalid_transition(self):
        repo = MagicMock()
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
            id="art1",
        )
        article.publish()
        article.archive()
        repo.find_by_id.return_value = article

        handler = PublishArticleCommandHandler(article_repo=repo)
        with pytest.raises(InvalidArticleStatusTransitionError):
            handler.handle(
                PublishArticleCommand(article_id="art1", company_id="comp1")
            )
