# Operations

**Date:** 2026-02-22
**Philosophy:** Minimal tooling. Every tool must earn its place. If GitHub can do it, we don't add another tool.
**Team model:** 1 human (Director de Orquesta) + AI agents. No employees. Advisors when needed.

---

## Toolstack

| Category | Tool | Cost | Notes |
|---|---|---|---|
| Code & version control | GitHub | Free | Source of truth for everything — code, issues, docs, startup folder |
| AI development | Claude Code | €100/month | Core of the engineering workflow — specs → implementation → review |
| Infrastructure | AWS (EC2 + RDS + S3) | ~€100/month | Production + staging |
| Error monitoring | Sentry | Free plan | Already configured |
| Domain | Namecheap / similar | ~€15/year | desksupportmonkey.com |
| Email (transactional) | Resend or Mailgun | ~€10/month | Magic links, notifications, invoices |
| Email (company) | Google Workspace or Zoho | ~€5/month | hola@desksupportmonkey.com |
| Customer support | GitHub Issues | Free | Public issues for bugs/features; private repo for customer tickets |
| Payments | Stripe | 1.5% + €0.25/tx | No monthly fee |
| **Total fixed** | | **~€210/month** | Excluding Stripe fees |

---

## Development Workflow

The entire development process runs inside the project repository with Claude Code.

```
CEO identifies need / customer feedback
        ↓
Requirements doc (docs/epics/{epic}/requirements.md)
        ↓
Slicing doc (docs/epics/{epic}/slicing.md)
        ↓
Tasks doc per feature (docs/epics/{epic}/features/{f}/tasks.md)
        ↓
Claude Code implements from tasks.md
        ↓
/check-architecture + /check-quality + /linter
        ↓
Tests pass (make test + make test-integration)
        ↓
Deploy to staging → verify → deploy to production
        ↓
Update tasks.md + slicing.md + roadmap.md
```

### Rules
- No feature ships without a tasks.md
- No tasks.md without a requirements.md
- No merge without passing tests + linter
- No "fix it later" — quality gate is non-negotiable

---

## Deployment

### Production
- Server: AWS EC2 t3.medium
- Database: AWS RDS PostgreSQL t3.small
- Storage: AWS S3
- Domain: desksupportmonkey.com
- SSL: Let's Encrypt (auto-renew)
- Deploy: `git push production main` → post-receive hook → restart services

### Staging
- Server: AWS EC2 t3.small
- Database: AWS RDS t3.micro
- Domain: staging.desksupportmonkey.com
- Purpose: test before every production deploy

### Monitoring
- Sentry: error tracking (backend + frontend)
- Health endpoint: `GET /api/v1/health` — checked after every deploy
- systemctl: service status after every deploy
- Logs: journalctl on server

---

## Customer Support

### Tier 1 — Self-service
- Help documentation in the product (Knowledge Base — Enterprise feature, but basic docs public)
- README and GitHub Wiki for self-hosted users
- GitHub Discussions for community questions

### Tier 2 — GitHub Issues
- Bugs and feature requests: public GitHub Issues
- Customer-specific issues: private repo or email
- SLA target (informal, pre-CS hire):
  - Critical bugs (data loss, login broken): same day
  - Other bugs: 48 hours
  - Feature requests: acknowledged within 1 week

### Tier 3 — Direct (CEO)
- Enterprise customers get direct email/LinkedIn access to the CEO
- No support ticket system until Head of CS is hired

---

## Finance & Admin

| Task | How | Frequency |
|---|---|---|
| Invoicing | Stripe automatic + manual PDF for annual | Monthly |
| VAT (Spain) | Modelo 303 | Quarterly |
| VAT (EU clients — OSS) | One Stop Shop via AEAT | Quarterly |
| Bookkeeping | Gestoría externa | Monthly |
| MRR tracking | Manual spreadsheet or Stripe dashboard | Weekly |
| Cashflow review | Spreadsheet | Monthly |

---

## Communication

| Channel | Purpose |
|---|---|
| GitHub Issues | Bugs, features, customer support |
| GitHub Discussions | Community questions, open source users |
| Email | Customer onboarding, invoicing, direct support |
| LinkedIn | Marketing, build in public, CEO presence |
| No Slack, no Notion, no Jira | Not needed at this stage |

---

## Incident Response

If production goes down:

1. Check Sentry for errors
2. `systemctl status dsm-api` on server
3. Check `journalctl -u dsm-api -n 100`
4. Check RDS status in AWS console
5. Rollback: `git push production previous-commit` if needed
6. Post incident summary in GitHub as an issue (transparency)

---

## What We Don't Use (and why)

| Tool | Why not |
|---|---|
| Slack | Team of 1-2, GitHub + email is enough |
| Notion | GitHub + markdown files cover all documentation needs |
| Jira | GitHub Issues + tasks.md files replace it entirely |
| Intercom / Zendesk | GitHub Issues + email until Head of CS is hired |
| HubSpot | Overkill for <50 customers — spreadsheet + LinkedIn DMs |
| Datadog | Sentry + journalctl is sufficient at this scale |
| Figma | Orchestrator designs directly in code with Claude Code |
| HR software | No employees — no HR needed |
| Payroll | No employees — no payroll until MRR justifies it |
