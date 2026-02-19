import csv
import io
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetType
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


REQUIRED_HEADERS = {"type", "brand", "model", "serial_number"}
OPTIONAL_HEADERS = {"purchase_date", "warranty_expiration", "notes"}
ALL_HEADERS = REQUIRED_HEADERS | OPTIONAL_HEADERS

VALID_TYPES = {t.value for t in AssetType}


class InvalidCSVError(Exception):
    pass


@dataclass
class ImportRowError:
    row: int
    error: str


@dataclass
class ImportResult:
    total: int
    successful: int
    failed: list[ImportRowError] = field(default_factory=list)


@dataclass
class ImportAssetsRequest:
    company_id: str
    performed_by: str
    csv_content: str


# Application service: returns ImportResult, not a CQRS command handler
class ImportAssetsService:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: ImportAssetsRequest) -> ImportResult:
        reader = csv.DictReader(io.StringIO(command.csv_content))

        if not reader.fieldnames:
            raise InvalidCSVError("CSV file is empty or has no headers")

        headers = {h.strip().lower() for h in reader.fieldnames}
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise InvalidCSVError(f"Missing required columns: {', '.join(sorted(missing))}")

        rows = list(reader)
        total = len(rows)
        failed: list[ImportRowError] = []
        seen_serials: set[str] = set()
        assets_to_save: list[tuple[Asset, AssetEvent]] = []

        for idx, row in enumerate(rows, start=2):  # row 1 = header
            row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

            error = self._validate_row(row, seen_serials, command.company_id)
            if error:
                failed.append(ImportRowError(row=idx, error=error))
                continue

            serial = row["serial_number"].strip()
            seen_serials.add(serial.lower())

            purchase_date = self._parse_date(row.get("purchase_date"))
            warranty_expiration = self._parse_date(row.get("warranty_expiration"))

            asset = Asset.create(
                company_id=command.company_id,
                type=AssetType(row["type"].strip().lower()),
                brand=row["brand"].strip(),
                model=row["model"].strip(),
                serial_number=serial,
                purchase_date=purchase_date,
                warranty_expiration=warranty_expiration,
                notes=row.get("notes", "").strip() or None,
            )
            event = AssetEvent.create(
                asset_id=asset.id,
                event_type="created",
                data={"source": "csv_import"},
                performed_by=command.performed_by,
            )
            assets_to_save.append((asset, event))

        for asset, event in assets_to_save:
            self.asset_repo.save(asset)
            self.asset_repo.save_event(event)

        return ImportResult(
            total=total,
            successful=total - len(failed),
            failed=failed,
        )

    def _validate_row(
        self, row: dict, seen_serials: set[str], company_id: str
    ) -> Optional[str]:
        # Required fields
        for field_name in ("brand", "model", "serial_number", "type"):
            if not row.get(field_name, "").strip():
                return f"{field_name} is required"

        # Type enum
        type_val = row["type"].strip().lower()
        if type_val not in VALID_TYPES:
            return f"Invalid type '{row['type'].strip()}'. Valid: {', '.join(sorted(VALID_TYPES))}"

        # Serial number uniqueness (intra-CSV)
        serial = row["serial_number"].strip().lower()
        if serial in seen_serials:
            return f"Duplicate serial number '{row['serial_number'].strip()}' in CSV"

        # Serial number uniqueness (DB)
        existing = self.asset_repo.find_by_serial_number(
            row["serial_number"].strip(), company_id
        )
        if existing:
            return f"Serial number '{row['serial_number'].strip()}' already exists"

        # Date validation
        for date_field in ("purchase_date", "warranty_expiration"):
            val = row.get(date_field, "").strip()
            if val:
                try:
                    date.fromisoformat(val)
                except ValueError:
                    return f"Invalid date format for {date_field}: '{val}'. Use YYYY-MM-DD"

        return None

    @staticmethod
    def _parse_date(val: Optional[str]) -> Optional[date]:
        if not val or not val.strip():
            return None
        return date.fromisoformat(val.strip())
