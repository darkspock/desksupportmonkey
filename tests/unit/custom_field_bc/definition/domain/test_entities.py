import pytest

from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.domain.exceptions import OptionsRequiredError


class TestSlugify:
    def test_create_generates_valid_slug(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Cost Center",
            field_type="text",
        )
        assert definition.field_key == "cost_center"

    def test_slugify_special_chars(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Building #3 (Main)",
            field_type="text",
        )
        assert definition.field_key == "building_3_main"

    def test_slugify_unicode(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Área de Trabajo",
            field_type="text",
        )
        assert definition.field_key == "rea_de_trabajo"

    def test_slugify_max_length(self):
        long_label = "a" * 60
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label=long_label,
            field_type="text",
        )
        assert len(definition.field_key) == 50

    def test_slugify_leading_trailing_spaces(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="  My Field  ",
            field_type="text",
        )
        assert definition.field_key == "my_field"

    def test_slugify_multiple_spaces(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="My   Field",
            field_type="text",
        )
        assert definition.field_key == "my_field"


class TestOptionsValidation:
    def test_create_select_requires_options(self):
        with pytest.raises(OptionsRequiredError):
            CustomFieldDefinition.create(
                company_id="01COMP",
                entity_type="asset",
                label="Status",
                field_type="select",
                options=None,
            )

    def test_create_select_with_options_succeeds(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Status",
            field_type="select",
            options=["A", "B"],
        )
        assert definition.options == ["A", "B"]

    def test_create_text_rejects_options(self):
        with pytest.raises(OptionsRequiredError):
            CustomFieldDefinition.create(
                company_id="01COMP",
                entity_type="asset",
                label="Notes",
                field_type="text",
                options=["A"],
            )

    def test_create_boolean_rejects_options(self):
        with pytest.raises(OptionsRequiredError):
            CustomFieldDefinition.create(
                company_id="01COMP",
                entity_type="asset",
                label="Active",
                field_type="boolean",
                options=["A"],
            )

    def test_create_multi_select_requires_options(self):
        with pytest.raises(OptionsRequiredError):
            CustomFieldDefinition.create(
                company_id="01COMP",
                entity_type="asset",
                label="Tags",
                field_type="multi_select",
                options=None,
            )

    def test_update_validates_options_consistency(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Status",
            field_type="select",
            options=["A", "B"],
        )
        with pytest.raises(OptionsRequiredError):
            definition.update(options=[])


class TestUpdate:
    def test_update_mutable_fields(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Old Label",
            field_type="text",
            description="Old description",
            required=False,
        )
        original_updated_at = definition.updated_at

        definition.update(
            label="New Label",
            description="New description",
            required=True,
        )

        assert definition.label == "New Label"
        assert definition.description == "New description"
        assert definition.required is True
        assert definition.updated_at != original_updated_at


class TestDeactivateActivate:
    def test_deactivate(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Cost Center",
            field_type="text",
        )
        assert definition.is_active is True
        definition.deactivate()
        assert definition.is_active is False

    def test_activate(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Cost Center",
            field_type="text",
        )
        definition.deactivate()
        assert definition.is_active is False
        definition.activate()
        assert definition.is_active is True


class TestCreateDefaults:
    def test_create_defaults(self):
        definition = CustomFieldDefinition.create(
            company_id="01COMP",
            entity_type="asset",
            label="Cost Center",
            field_type="text",
        )
        assert definition.required is False
        assert definition.is_active is True
        assert definition.visible_to_employees is True
        assert definition.id is not None
        assert definition.created_at is not None
        assert definition.updated_at is not None
