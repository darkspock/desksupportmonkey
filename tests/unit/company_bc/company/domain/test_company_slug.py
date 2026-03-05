import pytest

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import AuthMode


class TestGenerateSlug:
    def test_simple_name(self):
        assert Company.generate_slug("Acme Corp") == "acme-corp"

    def test_name_with_special_chars(self):
        assert Company.generate_slug("Acme & Sons, Ltd.") == "acme-sons-ltd"

    def test_unicode_name(self):
        slug = Company.generate_slug("Ñoño & Friends S.A.")
        assert slug == "nono-friends-s-a"

    def test_name_with_accents(self):
        slug = Company.generate_slug("Café Résumé")
        assert slug == "cafe-resume"

    def test_short_name_gets_suffix(self):
        slug = Company.generate_slug("AB")
        assert slug == "ab-co"
        assert len(slug) >= 3

    def test_single_char_name(self):
        slug = Company.generate_slug("X")
        assert slug == "x-co"

    def test_long_name_truncated(self):
        slug = Company.generate_slug("a" * 100)
        assert len(slug) <= 50

    def test_numeric_name(self):
        assert Company.generate_slug("123 Corp") == "123-corp"

    def test_already_slug_format(self):
        assert Company.generate_slug("already-a-slug") == "already-a-slug"

    def test_whitespace_collapsed(self):
        assert Company.generate_slug("  Acme   Corp  ") == "acme-corp"

    def test_pure_unicode_gets_suffix(self):
        slug = Company.generate_slug("日本語")
        # All chars stripped → empty → "-co" suffix
        assert len(slug) >= 3


class TestValidateSlug:
    def test_valid_slug(self):
        Company.validate_slug("acme-corp")  # Should not raise

    def test_valid_slug_numeric(self):
        Company.validate_slug("company123")  # Should not raise

    def test_valid_slug_with_hyphens(self):
        Company.validate_slug("my-company-name")  # Should not raise

    def test_valid_slug_minimum_length(self):
        Company.validate_slug("abc")  # Should not raise

    def test_empty_slug_raises(self):
        with pytest.raises(ValueError, match="Slug is required"):
            Company.validate_slug("")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="between 3 and 50"):
            Company.validate_slug("ab")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="between 3 and 50"):
            Company.validate_slug("a" * 51)

    def test_uppercase_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("UPPER")

    def test_spaces_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("slug with spaces")

    def test_leading_hyphen_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("-leading")

    def test_trailing_hyphen_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("trailing-")

    def test_consecutive_hyphens_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("double--hyphen")

    def test_special_chars_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Company.validate_slug("slug_with_underscores")

    @pytest.mark.parametrize("reserved", [
        "admin", "api", "login", "register", "reseller", "app", "auth", "super-admin",
    ])
    def test_reserved_slugs_rejected(self, reserved):
        with pytest.raises(ValueError, match="reserved"):
            Company.validate_slug(reserved)


class TestUpdateSlug:
    def test_update_valid_slug(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        company.update_slug("new-slug")
        assert company.slug == "new-slug"

    def test_update_reserved_slug_raises(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        with pytest.raises(ValueError, match="reserved"):
            company.update_slug("admin")

    def test_update_invalid_slug_raises(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            company.update_slug("Invalid Slug!")


class TestCompanyAuthMode:
    def test_default_auth_mode_is_domain(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        assert company.auth_mode == AuthMode.DOMAIN

    def test_slug_field_defaults_to_none(self):
        company = Company.create(name="Acme Corp", email_domains=["acme.com"])
        assert company.slug is None

    def test_create_with_slug(self):
        company = Company.create(
            name="Acme Corp", email_domains=["acme.com"], slug="acme-corp"
        )
        assert company.slug == "acme-corp"

    def test_create_with_invalid_slug_raises(self):
        with pytest.raises(ValueError, match="reserved"):
            Company.create(
                name="Acme Corp", email_domains=["acme.com"], slug="admin"
            )
