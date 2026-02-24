class ArticleNotFoundError(Exception):
    def __init__(self, article_id: str):
        super().__init__(f"Article '{article_id}' not found")
        self.article_id = article_id


class InvalidArticleStatusTransitionError(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Cannot transition from '{current}' to '{target}'")
        self.current = current
        self.target = target


class ArticleDraftOnlyDeleteError(Exception):
    def __init__(self) -> None:
        super().__init__("Only draft articles can be deleted")


class CategoryNotFoundError(Exception):
    def __init__(self, category_id: str):
        super().__init__(f"Category '{category_id}' not found")
        self.category_id = category_id


class CategoryHasArticlesError(Exception):
    def __init__(self, category_id: str):
        super().__init__(f"Category '{category_id}' has articles and cannot be deleted")
        self.category_id = category_id


class DuplicateSlugError(Exception):
    def __init__(self, slug: str):
        super().__init__(f"An article with slug '{slug}' already exists")
        self.slug = slug
