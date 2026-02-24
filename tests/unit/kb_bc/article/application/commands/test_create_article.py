from unittest.mock import MagicMock

from src.kb_bc.article.application.commands.create_article import (
    CreateArticleCommand,
    CreateArticleCommandHandler,
)
from src.kb_bc.article.domain.enums import ArticleStatus


class TestCreateArticleCommandHandler:
    def test_creates_article_and_version(self):
        repo = MagicMock()
        handler = CreateArticleCommandHandler(article_repo=repo)

        handler.handle(
            CreateArticleCommand(
                article_id="art1",
                company_id="comp1",
                title="How to Reset Password",
                content="<p>Steps to reset...</p>",
                author_id="user1",
                excerpt="Password reset guide",
                category_id="cat1",
            )
        )

        repo.save.assert_called_once()
        saved_article = repo.save.call_args[0][0]
        assert saved_article.title == "How to Reset Password"
        assert saved_article.status == ArticleStatus.DRAFT
        assert saved_article.author_id == "user1"
        assert saved_article.category_id == "cat1"

        repo.save_version.assert_called_once()
        saved_version = repo.save_version.call_args[0][0]
        assert saved_version.version_number == 1
        assert saved_version.title == "How to Reset Password"
