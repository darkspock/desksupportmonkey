# Local Development Setup

This guide covers everything needed to run DeskSupportMonkey locally, including optional Stripe billing testing.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.13 | `brew install python@3.13` |
| uv | latest | `brew install uv` |
| Node.js | ≥ 20 | `brew install node` |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop |
| Git | any | pre-installed on macOS |

Optional (for Stripe local testing):

| Tool | Install |
|------|---------|
| Stripe CLI | `brew install stripe/stripe-cli/stripe` |

---

## First-time setup

### 1. Clone and configure environment

```bash
git clone <repo-url> desksupportmonkey
cd desksupportmonkey
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local development — no edits required unless you want to enable optional features (OAuth, Stripe, AI).

### 2. Install dependencies

```bash
make install
```

This runs `uv sync` (backend) and `npm install` (frontend).

### 3. Start Docker services

```bash
make start-docker
```

Starts four containers:

| Service | URL / Port | Credentials |
|---------|-----------|-------------|
| PostgreSQL | `localhost:5444` | `postgres / postgres` |
| Redis | `localhost:6399` | — |
| MinIO (S3) | API: `localhost:9002` · Console: `http://localhost:9003` | `minioadmin / minioadmin` |
| Mailpit (SMTP) | UI: `http://localhost:8028` | — |

### 4. Apply database migrations

```bash
make db-upgrade
```

### 5. (Optional) Seed demo data

```bash
make seed
```

Creates a demo company, users, assets, and requests so you can explore the app immediately.

### 6. Start everything

```bash
make start
```

This starts Docker (if not already running), the Celery worker, the Vite dev server, and the FastAPI backend. The terminal stays attached to the backend — Ctrl+C stops it cleanly.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8001 |
| API docs (Swagger) | http://localhost:8001/docs |
| Mailpit (catch-all email) | http://localhost:8028 |

---

## Day-to-day development

### Starting services individually

```bash
make start-docker     # Docker only
make start-backend    # FastAPI (auto-reload on file changes)
make start-frontend   # Vite dev server
make queue            # Celery worker (background tasks / PDF reports)
```

### Running tests

```bash
make test              # Unit tests (fast, no Docker needed)
make test-integration  # Integration tests (requires Docker PostgreSQL on port 5444)
make test-all          # Both suites
```

Integration tests use a dedicated `dsm_test` database. Tables are created fresh at the start of each test session and dropped at the end — no manual setup required.

### Linting

```bash
make lint   # mypy (type checking) + flake8 (style)
```

### Database migrations

```bash
# Create a new migration (autogenerate from model changes)
make db-migrate msg="describe_what_changed"

# Apply pending migrations
make db-upgrade

# Roll back one step
make db-downgrade
```

---

## Architecture overview

```
desksupportmonkey/
├── src/                   # Domain + application layer (DDD/CQRS)
│   ├── auth_bc/           # Authentication bounded context
│   ├── company_bc/        # Companies, departments, billing
│   ├── asset_bc/          # IT asset inventory
│   ├── request_bc/        # Service requests / help desk tickets
│   └── ...
├── adapters/http/api/     # FastAPI routers and schemas
├── core/                  # Config, database, JWT, email, Stripe client
├── alembic/               # Database migrations
├── web/app/src/           # React 19 + TypeScript frontend
│   ├── pages/             # Route-level pages
│   ├── components/        # Shared UI components
│   └── lib/               # API client, i18n, hooks
└── tests/
    ├── unit/              # Fast, isolated (MagicMock)
    └── integration/       # Real PostgreSQL, full HTTP stack
```

---

## Optional features

### OAuth login (Google / Microsoft)

Set in `.env`:

```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
MICROSOFT_CLIENT_ID=your-microsoft-app-client-id
MICROSOFT_TENANT_ID=common
```

OAuth buttons appear on the login page only when the corresponding `CLIENT_ID` is set.

### AI equipment classification

```env
OPENAI_API_KEY=sk-...
# or
GROQ_API_KEY=gsk_...
```

### Open Source / self-hosted mode (no billing)

```env
OPEN_SOURCE_MODE=true
```

All plan limits and billing gates are bypassed. No Stripe keys needed. Every company gets full access indefinitely.

---

## Stripe billing — local testing

New companies always receive a **15-day free trial** (no card required). Stripe is only needed to test plan upgrades, payment flows, and webhooks.

### Step 1 — Install and authenticate Stripe CLI

```bash
brew install stripe/stripe-cli/stripe
make stripe-login    # opens browser for Stripe authentication
```

### Step 2 — Add test keys to `.env`

Get these from **https://dashboard.stripe.com/test/apikeys** (make sure you are in test mode):

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Step 3 — Create test prices

In the Stripe dashboard (test mode), go to **Products → Add product** and create two recurring prices:

| Product | Billing | Price |
|---------|---------|-------|
| Premium | Monthly | any amount |
| Enterprise | Monthly | any amount |

Copy the `price_...` IDs into `.env`:

```env
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### Step 4 — Start the webhook forwarder

With the backend running (`make start-backend`), open a **second terminal** and run:

```bash
make stripe-listen
```

The CLI will print:

```
> Ready! Your webhook signing secret is whsec_test_51...
```

Copy that value into `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_test_51...
```

Then **restart the backend** so it picks up the new secret.

### Step 5 — Test a checkout flow

1. Log in as a company admin and go to **Settings → Billing**
2. Click **Upgrade to Premium**
3. You are redirected to Stripe Checkout — use the test card:

| Field | Value |
|-------|-------|
| Card number | `4242 4242 4242 4242` |
| Expiry | Any future date (e.g. `12/29`) |
| CVC | Any 3 digits |
| ZIP | Any 5 digits |

4. After completing checkout, the Stripe CLI terminal shows the forwarded events and the backend processes them in real time.
5. The `/billing/processing` page polls until the plan activates, then redirects to Billing.

### Testing other Stripe scenarios

| Scenario | How |
|----------|-----|
| Payment failure → grace period | Card `4000 0000 0000 0341` (always fails) |
| Subscription cancelled | Cancel from Customer Portal or Stripe Dashboard |
| Restore after payment | Use a valid card after a failed charge |
| Super admin plan override | Super admin → Companies → Billing button |

### Stripe CLI reference

```bash
# List forwarded events in real time (already running via make stripe-listen)
stripe listen --forward-to http://localhost:8001/api/v1/billing/webhook

# Manually trigger a specific event
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed

# Open Stripe dashboard
stripe open dashboard
```

---

## Troubleshooting

**Backend fails to start — port 8001 already in use**

```bash
lsof -ti:8001 | xargs kill -9
```

**Database connection refused**

Make sure Docker is running:
```bash
make start-docker
docker ps   # should show desksupportmonkey-db-1 as healthy
```

**Migrations fail**

```bash
make db-downgrade   # roll back one step
make db-upgrade     # re-apply
```

**Email not arriving in Mailpit**

Check `http://localhost:8028` — all outbound email is caught there in development. Verify `SMTP_PORT=1028` in `.env`.

**Stripe webhook returns 400 (invalid signature)**

The `STRIPE_WEBHOOK_SECRET` in `.env` must match the `whsec_test_...` printed by `make stripe-listen`. Restart the backend after updating `.env`.

**Celery tasks not running**

```bash
make queue          # start worker in foreground to see errors
cat /tmp/celery-dsm.log   # or check background worker logs
```
