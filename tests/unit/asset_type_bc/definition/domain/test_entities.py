from src.asset_type_bc.definition.domain.entities import (
    AssetTypeDefinition,
    _UNSET,
)


class TestAssetTypeDefinition:
    def test_create_basic(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop"
        )
        assert d.company_id == "comp1"
        assert d.name == "Laptop"
        assert d.code == "laptop"
        assert d.is_active is True
        assert d.sort_order == 0
        assert d.icon is None
        assert len(d.id) == 26

    def test_create_with_icon(self):
        d = AssetTypeDefinition.create(
            company_id="comp1",
            name="Monitor",
            icon="monitor",
            sort_order=5,
        )
        assert d.icon == "monitor"
        assert d.sort_order == 5

    def test_create_strips_whitespace(self):
        d = AssetTypeDefinition.create(
            company_id="comp1",
            name="  Docking Station  ",
            icon="  dock  ",
        )
        assert d.name == "Docking Station"
        assert d.code == "docking_station"
        assert d.icon == "dock"

    def test_slugify_special_chars(self):
        d = AssetTypeDefinition.create(
            company_id="comp1",
            name="USB-C Hub (v2)",
        )
        assert d.code == "usbc_hub_v2"

    def test_slugify_long_name_truncated(self):
        long_name = "A" * 100
        d = AssetTypeDefinition.create(
            company_id="comp1", name=long_name
        )
        assert len(d.code) <= 50

    def test_update_name(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop"
        )
        d.update(name="Desktop")
        assert d.name == "Desktop"
        assert d.code == "desktop"

    def test_update_icon_to_value(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop"
        )
        d.update(icon="laptop_icon")
        assert d.icon == "laptop_icon"

    def test_update_icon_to_none(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop", icon="old"
        )
        d.update(icon=None)
        assert d.icon is None

    def test_update_icon_not_provided(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop", icon="original"
        )
        old_icon = d.icon
        d.update(icon=_UNSET)
        assert d.icon == old_icon

    def test_update_is_active(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop"
        )
        assert d.is_active is True
        d.update(is_active=False)
        assert d.is_active is False

    def test_update_updates_timestamp(self):
        d = AssetTypeDefinition.create(
            company_id="comp1", name="Laptop"
        )
        old_ts = d.updated_at
        d.update(name="Desktop")
        assert d.updated_at >= old_ts  # type: ignore[operator]
