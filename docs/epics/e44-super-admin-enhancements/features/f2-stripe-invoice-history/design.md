# Solution Design: F2 — Stripe Invoice History

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `company_bc`

---

## Summary

Extend `StripeClient` with `list_invoices()`, add a new query handler, new endpoint, and an Invoices tab in the frontend billing modal. No DB schema changes — data fetched live from Stripe.

---

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `StripeClient` | `core/stripe_client.py` | Yes | Add `list_invoices()` |
| `StripeUnavailableError` | `core/stripe_client.py` | Yes | Reuse as-is |
| Company billing router | `adapters/http/api/companies/routers.py` | Yes | Add new endpoint |
| `CompanyBillingModal.tsx` | `web/app/src/pages/superadmin/CompanyBillingModal.tsx` | Yes | Add Invoices tab |

---

## Implementation Plan

### 1. Domain / Application Layer

#### New: `InvoiceDto`

```python
# src/company_bc/company/application/queries/billing/get_company_invoices.py

@dataclass
class InvoiceDto:
    invoice_id: str
    date: datetime
    period_start: datetime
    period_end: datetime
    amount_cents: int
    currency: str
    status: str           # paid | open | uncollectible | void
    invoice_url: Optional[str]
    pdf_url: Optional[str]

@dataclass
class GetCompanyInvoicesQuery(Query):
    company_id: str
    limit: int = 20

class GetCompanyInvoicesQueryHandler(QueryHandler[GetCompanyInvoicesQuery, list[InvoiceDto]]):
    def __init__(self, company_repo: CompanyRepository, stripe_client: StripeClient) -> None:
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, query: GetCompanyInvoicesQuery) -> list[InvoiceDto]:
        company = self.company_repo.find_by_id(query.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        if not company.stripe_customer_id:
            return []
        raw = self.stripe_client.list_invoices(
            stripe_customer_id=company.stripe_customer_id,
            limit=min(query.limit, 100),
        )
        return [
            InvoiceDto(
                invoice_id=inv["id"],
                date=datetime.fromtimestamp(inv["created"], tz=timezone.utc),
                period_start=datetime.fromtimestamp(inv["period_start"], tz=timezone.utc),
                period_end=datetime.fromtimestamp(inv["period_end"], tz=timezone.utc),
                amount_cents=inv["amount_paid"] if inv["status"] == "paid" else inv["amount_due"],
                currency=inv["currency"],
                status=inv["status"],
                invoice_url=inv.get("hosted_invoice_url"),
                pdf_url=inv.get("invoice_pdf"),
            )
            for inv in raw
        ]
```

---

### 2. Infrastructure Layer

#### `core/stripe_client.py` — Add `list_invoices()`

```python
def list_invoices(self, stripe_customer_id: str, limit: int = 20) -> list[dict]:
    if self._open_source_mode:
        return []
    try:
        response = stripe.Invoice.list(customer=stripe_customer_id, limit=limit)
        return response.get("data", [])
    except stripe.error.StripeError as e:
        raise StripeUnavailableError(str(e)) from e
```

---

### 3. HTTP Layer

#### `adapters/http/api/companies/schemas.py` — New schema

```python
class InvoiceResponse(BaseModel):
    invoice_id: str
    date: datetime
    period_start: datetime
    period_end: datetime
    amount_cents: int
    currency: str
    status: str
    invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None
```

#### `adapters/http/api/companies/routers.py` — New endpoint

```python
@router.get("/{company_id}/invoices")
def get_company_invoices(
    company_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
) -> dict:
    handler = GetCompanyInvoicesQueryHandler(
        company_repo=company_repo,
        stripe_client=stripe_client,
    )
    try:
        invoices = handler.handle(GetCompanyInvoicesQuery(company_id=company_id, limit=limit))
    except CompanyNotFoundError:
        raise HTTPException(status_code=404, detail="Company not found")
    except StripeUnavailableError:
        raise HTTPException(status_code=503, detail="Stripe unavailable")
    return {"data": [InvoiceResponse(**dataclasses.asdict(inv)).model_dump(mode="json") for inv in invoices]}
```

---

### 4. Frontend

#### `CompanyBillingModal.tsx` — Add Invoices tab

**State additions:**
```tsx
const [activeTab, setActiveTab] = useState<'billing' | 'invoices'>('billing');

const { data: invoices, isLoading: invoicesLoading } = useQuery({
  queryKey: ['company-invoices', companyId],
  queryFn: async () => {
    const { data } = await api.get(`/companies/${companyId}/invoices`);
    return data.data as Invoice[];
  },
  enabled: activeTab === 'invoices',
});
```

**Invoice interface:**
```tsx
interface Invoice {
  invoice_id: string;
  date: string;
  period_start: string;
  period_end: string;
  amount_cents: number;
  currency: string;
  status: 'paid' | 'open' | 'uncollectible' | 'void';
  invoice_url: string | null;
  pdf_url: string | null;
}
```

**Status badge colors:**
- `paid` → green
- `open` → yellow
- `uncollectible` / `void` → red

**Invoice table columns:** Date | Period | Amount | Status | Actions (View / PDF)

---

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `core/stripe_client.py` | Additive | New `list_invoices()` method |
| `src/company_bc/.../get_company_invoices.py` | New | Query + handler + DTO |
| `adapters/http/api/companies/schemas.py` | Additive | `InvoiceResponse` |
| `adapters/http/api/companies/routers.py` | Additive | New GET endpoint |
| `web/app/src/pages/superadmin/CompanyBillingModal.tsx` | Extend | Invoices tab |
| `web/app/src/locales/en.ts` + `es.ts` | Additive | Invoice i18n keys |

**Breaking changes:** None.

---

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | `GetCompanyInvoicesQueryHandler` — empty for no stripe_customer_id; maps Stripe response; propagates `StripeUnavailableError` | High |
| Unit | `StripeClient.list_invoices()` — returns empty in open_source_mode; raises on Stripe error | High |
| Integration | `GET /companies/{id}/invoices` — mocked Stripe returns list; 404 for unknown; 503 on Stripe error; 403 for non-super-admin | High |

---

## Implementation Order

1. `core/stripe_client.py` — add `list_invoices()`
2. `get_company_invoices.py` — query, handler, DTO
3. `schemas.py` — `InvoiceResponse`
4. `routers.py` — new endpoint
5. Unit tests
6. Integration tests
7. Frontend: `CompanyBillingModal.tsx` — invoices tab + i18n
