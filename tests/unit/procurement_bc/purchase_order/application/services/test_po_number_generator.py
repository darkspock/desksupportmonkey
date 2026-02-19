from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.services.po_number_generator import (  # noqa: E501
    PONumberGenerator,
)


class TestPONumberGenerator:
    def setup_method(self):
        self.repo = MagicMock()
        self.generator = PONumberGenerator(self.repo)

    def test_first_po_of_year(self):
        self.repo.get_next_number.return_value = 1
        result = self.generator.generate(
            "comp1", "PO", 2026,
        )
        assert result == "PO-2026-001"
        self.repo.get_next_number.assert_called_once_with(
            "comp1", 2026,
        )

    def test_sequential_increment(self):
        self.repo.get_next_number.return_value = 42
        result = self.generator.generate(
            "comp1", "OC", 2026,
        )
        assert result == "OC-2026-042"
