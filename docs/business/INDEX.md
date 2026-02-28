# Business Documentation Index

Quick reference for AI agents. Read this to identify which docs to load — don't read everything.

## Product (docs/product/)

| File | Contents | Read when |
|------|----------|-----------|
| `roadmap.md` | All epics, phases, status | Always — understand scope |
| `functional_requirements.md` | Full functional spec | New feature design |
| `technical_requirements.md` | NFRs, security, performance | Architecture decisions |
| `competitive-analysis.md` | Competitor comparison | Positioning questions |
| `market-sizing-eu-itam.md` | EU ITAM market data | Business case work |

## Epics (docs/epics/)

Each epic folder `e{N}-{name}/` contains:
- `requirements.md` — business requirements (read first)
- `slicing.md` — feature breakdown with status
- `features/f{N}-{name}/tasks.md` — implementation tasks with checkboxes

### Core Platform (E0-E9)
| Epic | Name | Status |
|------|------|--------|
| E0 | Foundation & Auth | Done |
| E1 | Company Management | Done |
| E2 | Asset Inventory | Done |
| E3 | Service Requests | Done |
| E4 | Realtime Notifications | Done |
| E5 | Admin Dashboard | Done |
| E6 | Report Generation | Done |
| E7 | Frontend | Done |
| E8 | Seed Data & Demo | Done |
| E9 | UX Polish | Done |

### Extended Features (E10-E19)
| Epic | Name | Status |
|------|------|--------|
| E10 | Asset Labels (QR/Barcode) | Done |
| E11 | Department Equipment Profiles | Done |
| E12 | Request Typification & Approval | Done |
| E13 | AI Request Classification | Done |
| E14 | Procurement & Budget | Done |
| E15 | Appointment Scheduling | Done |
| E16 | Shipping & Logistics | Done |
| E17 | Scheduled Maintenance | Done |
| E18 | Knowledge Base | Done |
| E19 | SLA Management | Done |

### Security, Compliance & Advanced (E24+)
| Epic | Name | Status |
|------|------|--------|
| E24 | Google/Microsoft Login | Done |
| E25 | Vendor Supply Chain Risk | Done |
| E29 | Audit Trail | Done |
| E30 | Custom Fields | Done |
| E31 | Workflow Templates | Done |
| E33 | Change Management | Done |
| E35 | MCP Server | Done |
| E36 | Security Incident Management | Done |
| E37 | Risk Register | Done |
| E38 | Asset Criticality & CMDB | Done |
| E39 | Compliance Dashboard | Done |
| E40 | Vulnerability Management | Done |
| E43 | Billing (Stripe) | Done |
| E44 | Super Admin Enhancements | Done |
| E45 | Asset Locations | Done |
| E46 | White Label | Done |
| E49 | Asset Checkout & Custody | Done |

### Pending Epics
| Epic | Name | Phase |
|------|------|-------|
| E20 | Email Templates & Branding | 10 |
| E21 | Mobile App (React Native) | 11 |
| E23 | Multi-Channel Intake | 11 |
| E28 | Remote Management Integration | 12 |
| E32 | Asset Discovery | 12 |
| E42 | Compliance Evidence Vault | 8 |
| E26 | Automated Compliance Reports | Backlog |
| E27 | Predictive Analytics | Backlog |
| E34 | Multi-Language Knowledge Base | Backlog |

## Startup (startup/)

| Folder | Contents | Read when |
|--------|----------|-----------|
| `competitive/` | Competitor analyses (InvGate, compliance) | Positioning, feature parity |
| `branding/` | Brand identity, landing page, messaging | UI/UX, marketing |
| `business-model/` | Pricing, plans, revenue model | Billing features |
| `compliance/` | DORA, NIS2, ISO 27001, CRA analyses | Compliance features |
| `financials/` | Revenue projections | Business planning |
| `go-to-market/` | GTM strategy | Growth features |
| `market/` | Market analysis (EU, USA) | Business context |
| `pitch/` | Investor pitch (EN/ES) | Messaging |
| `team/` | Team profiles (CEO, CTO, etc.) | AI agent personas |
