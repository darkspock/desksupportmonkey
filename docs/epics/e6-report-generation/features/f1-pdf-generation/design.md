# Design: F1 - PDF Generation + Celery Task

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-16

---

## Celery Task Architecture

```python
@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_id: str):
    session = SessionLocal()
    try:
        # 1. Load report record
        repo = ReportRepository(session)
        report = repo.find_by_id_any_company(report_id)

        # 2. Update status to processing
        repo.update_status(report_id, ReportStatus.PROCESSING)
        session.commit()

        # 3. Collect data based on report type
        data = collect_data(report.type, report.company_id, report.parameters, session)

        # 4. Render HTML template
        html = render_template(report.type, data)

        # 5. Convert to PDF
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()

        # 6. Upload to S3
        storage_key = f"reports/{report.company_id}/{report.id}.pdf"
        storage = S3StorageService()
        storage.upload(storage_key, pdf_bytes)

        # 7. Update report record
        repo.update_status(report_id, ReportStatus.COMPLETED, storage_key=storage_key)
        session.commit()

    except Exception as exc:
        session.rollback()
        repo.update_status(report_id, ReportStatus.FAILED, error_message=str(exc))
        session.commit()
        raise self.retry(exc=exc)
    finally:
        session.close()
```

---

## Data Collectors

Each report type has a data collector function that queries repositories:

### asset_inventory
```python
def collect_asset_inventory(company_id, params, session):
    asset_repo = AssetRepository(session)
    company_repo = CompanyRepository(session)
    return {
        "company": company_repo.find_by_id(company_id),
        "by_status": asset_repo.count_by_status(company_id),
        "by_type": asset_repo.count_by_type(company_id),
        "assets": asset_repo.find_all_by_company(company_id),  # new method, unpaginated
        "expiring_warranties": asset_repo.find_expiring_warranties(company_id, 90),
    }
```

### request_summary
```python
def collect_request_summary(company_id, params, session):
    request_repo = RequestRepository(session)
    from_date = params.get("from_date") if params else None
    to_date = params.get("to_date") if params else None
    return {
        "company": ...,
        "by_status": request_repo.count_by_status(company_id),
        "by_type": request_repo.count_by_type(company_id),
        "by_priority": request_repo.count_by_priority(company_id),
        "avg_resolution_time": request_repo.avg_resolution_time(company_id, from_date, to_date),
        "sla_breaches": request_repo.find_open_requests_with_age(company_id),
    }
```

### technician_performance
```python
def collect_technician_performance(company_id, params, session):
    request_repo = RequestRepository(session)
    from_date = params.get("from_date") if params else None
    to_date = params.get("to_date") if params else None
    return {
        "company": ...,
        "by_technician": request_repo.avg_resolution_time_by_technician(company_id, from_date, to_date),
    }
```

---

## HTML Templates

### Base Template (`templates/reports/base.html`)
- Company name header
- Report title, generation date
- CSS for professional layout (tables, colors, spacing)
- Footer with page info

### Report-Specific Templates
Each extends base.html and adds:
- Summary cards (counts)
- Data tables
- Alert sections (warranty, SLA)

---

## New Repository Method

### AssetRepository.find_all_by_company(company_id) -> list[Asset]
Returns all assets for a company without pagination. For report generation only.

---

## Shared SLA Constants

Extract SLA thresholds from dashboard router to a shared location:
```python
# src/request_bc/request/domain/constants.py
SLA_THRESHOLDS_HOURS = {
    "urgent": 4, "high": 24, "medium": 72, "low": 168,
}
```
Update dashboard router to import from this location.
