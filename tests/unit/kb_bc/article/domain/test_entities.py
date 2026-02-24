import pytest

from src.kb_bc.article.domain.entities import (
    Article,
    ArticleCategory,
    ArticleVersion,
    generate_slug,
)
from src.kb_bc.article.domain.enums import ArticleStatus
from src.kb_bc.article.domain.exceptions import (
    ArticleDraftOnlyDeleteError,
    InvalidArticleStatusTransitionError,
)


class TestGenerateSlug:
    def test_basic_slug(self):
        assert generate_slug("Hello World") == "hello-world"

    def test_special_characters(self):
        assert generate_slug("What's New? (2024)") == "what-s-new-2024"

    def test_long_title_truncated(self):
        title = "a" * 200
        slug = generate_slug(title)
        assert len(slug) <= 120


class TestArticle:
    def test_create_article(self):
        article = Article.create(
            company_id="comp1",
            title="How to Reset Password",
            content="<p>Steps to reset your password...</p>",
            author_id="user1",
        )
        assert article.title == "How to Reset Password"
        assert article.slug == "how-to-reset-password"
        assert article.status == ArticleStatus.DRAFT
        assert article.view_count == 0
        assert article.id is not None

    def test_create_article_with_excerpt(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
            excerpt="A short summary",
        )
        assert article.excerpt == "A short summary"

    def test_create_article_title_required(self):
        with pytest.raises(ValueError, match="Title is required"):
            Article.create(
                company_id="comp1",
                title="",
                content="<p>Content</p>",
                author_id="user1",
            )

    def test_create_article_content_required(self):
        with pytest.raises(ValueError, match="Content is required"):
            Article.create(
                company_id="comp1",
                title="Test",
                content="",
                author_id="user1",
            )

    def test_publish_from_draft(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        assert article.status == ArticleStatus.PUBLISHED
        assert article.published_at is not None

    def test_unpublish_from_published(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        article.unpublish()
        assert article.status == ArticleStatus.DRAFT

    def test_archive_from_published(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        article.archive()
        assert article.status == ArticleStatus.ARCHIVED

    def test_restore_from_archived(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        article.archive()
        article.restore()
        assert article.status == ArticleStatus.DRAFT

    def test_invalid_transition_draft_to_archived(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        with pytest.raises(InvalidArticleStatusTransitionError):
            article.archive()

    def test_invalid_transition_archived_to_published(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        article.archive()
        with pytest.raises(InvalidArticleStatusTransitionError):
            article.publish()

    def test_update_content(self):
        article = Article.create(
            company_id="comp1",
            title="Old Title",
            content="<p>Old</p>",
            author_id="user1",
        )
        article.update_content(
            title="New Title",
            content="<p>New</p>",
            excerpt="Updated summary",
        )
        assert article.title == "New Title"
        assert article.slug == "new-title"
        assert article.content == "<p>New</p>"
        assert article.excerpt == "Updated summary"

    def test_update_content_empty_title_fails(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        with pytest.raises(ValueError, match="Title cannot be empty"):
            article.update_content(title="  ")

    def test_increment_view_count(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        assert article.view_count == 0
        article.increment_view_count()
        assert article.view_count == 1
        article.increment_view_count()
        assert article.view_count == 2

    def test_validate_can_delete_draft(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.validate_can_delete()  # Should not raise

    def test_validate_can_delete_published_fails(self):
        article = Article.create(
            company_id="comp1",
            title="Test",
            content="<p>Content</p>",
            author_id="user1",
        )
        article.publish()
        with pytest.raises(ArticleDraftOnlyDeleteError):
            article.validate_can_delete()


class TestArticleCategory:
    def test_create_category(self):
        cat = ArticleCategory.create(
            company_id="comp1",
            name="Troubleshooting",
            sort_order=1,
            description="How to fix common issues",
        )
        assert cat.name == "Troubleshooting"
        assert cat.slug == "troubleshooting"
        assert cat.sort_order == 1
        assert cat.description == "How to fix common issues"

    def test_create_category_name_required(self):
        with pytest.raises(ValueError, match="Category name is required"):
            ArticleCategory.create(
                company_id="comp1",
                name="",
            )

    def test_update_category(self):
        cat = ArticleCategory.create(
            company_id="comp1",
            name="Old Name",
        )
        cat.update(name="New Name", sort_order=5)
        assert cat.name == "New Name"
        assert cat.slug == "new-name"
        assert cat.sort_order == 5


class TestArticleVersion:
    def test_create_version(self):
        version = ArticleVersion.create(
            article_id="art1",
            version_number=1,
            title="Test Article",
            content="<p>Content</p>",
            edited_by="user1",
        )
        assert version.version_number == 1
        assert version.title == "Test Article"
        assert version.id is not None
