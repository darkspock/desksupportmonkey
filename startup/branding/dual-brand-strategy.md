# Dual Brand Strategy

**Date:** 2026-02-24
**Decision:** Split the product into two brands targeting different audiences

---

## Why Two Brands

DeskSupportMonkey has two fundamentally different audiences with opposing expectations:

| Audience | What they expect |
|---|---|
| **IT Manager at a hospital, factory, or bank** | Professional design, compliance focus, trust signals, corporate tone, "request a demo" |
| **Developer, sysadmin, self-hoster** | Dark theme, GitHub, open source, technical details, build-in-public narrative |

A single brand cannot credibly serve both. A cartoon monkey mascot kills trust for the compliance buyer. A corporate light theme kills engagement for the open source community. Trying to do both results in neither audience feeling at home.

---

## The Two Brands

### DSM Control (dsmcontrol.com) — Commercial / SaaS

**Purpose:** The brand that sells. Targets IT managers, CISOs, and operations leads at regulated SMBs (10-300 employees).

**Tone:** Professional, authoritative, compliance-first.

**Visual identity:** Light theme, navy + teal palette, clean typography, no mascot, screenshots of real product.

**Key messages:**
- "Control total de tus activos TIC"
- NIS2, DORA, CRA compliance from day one
- Full device lifecycle with audit trail
- Flat pricing per company size — no per-agent trap

**What does NOT appear here:**
- The monkey mascot
- "Built with AI" / "AI-managed company"
- "View on GitHub" as a primary CTA
- Dark theme
- Developer jargon
- The word "monkey"

### DeskSupportMonkey (desksupportmonkey.com) — Community / Open Source

**Purpose:** The brand that builds community. Targets developers, sysadmins, self-hosters, and the build-in-public audience.

**Tone:** Technical, approachable, transparent, community-driven.

**Visual identity:** Dark theme, monkey mascot, GitHub-forward, developer-oriented.

**Key messages:**
- Open source ITAM + incident management
- Self-host for free (AGPL)
- 100% AI-managed company experiment
- Build in public — code, strategy, financials all on GitHub

---

## How They Connect

```
DSM Control                              DeskSupportMonkey
(dsmcontrol.com)                         (desksupportmonkey.com)
    │                                         │
    │  "Powered by DeskSupportMonkey"         │  "The open source engine
    │   (small footer link)                   │   behind DSM Control"
    │                                         │
    ▼                                         ▼
Commercial SaaS                          GitHub repo + community
Paid customers                           Self-hosters, contributors
€49-199/month                            Free forever
```

### Cross-references
- **DSM Control footer:** "Built on open source. View the code on GitHub." (subtle, not a primary CTA)
- **DeskSupportMonkey README:** "Want the managed cloud version? Visit dsmcontrol.com"
- **GitHub repo name:** stays `desksupportmonkey` — the open source identity
- **Product UI:** branded as "DSM Control" for cloud customers, "DeskSupportMonkey" for self-hosted

### Legal entity
Both brands belong to **Plan Zeta Tech S.L.** — no separate legal structure needed.

---

## Domain Strategy

| Domain | Status | Use |
|---|---|---|
| dsmcontrol.com | **Available** — register immediately | Commercial brand |
| desksupportmonkey.com | Already owned | Open source / community brand |

---

## Impact on Existing Documents

| Document | Change needed |
|---|---|
| `startup/go-to-market/strategy.md` | Add DSM Control as the commercial distribution channel |
| `startup/pitch/pitch-en.md` | Create DSM Control version targeting compliance buyers |
| `startup/pitch/pitch-es.md` | Create DSM Control version in Spanish |
| `startup/business-model/business-model.md` | Reference DSM Control as the paid brand |
| `web/site/` | Current site becomes DeskSupportMonkey community; new site needed for DSM Control |
