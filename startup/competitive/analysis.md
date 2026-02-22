# Competitive Analysis

**Date:** 2026-02-22
**Product:** DeskSupportMonkey — IT asset lifecycle management with asset-linked incidents and NIS2 compliance

---

## The Market Gap in One Sentence

No sub-€500/month tool combines full asset lifecycle management + incidents natively linked to assets + explicit NIS2 compliance narrative + SMB flat pricing + open source tier + EU-native SaaS. That combination is unoccupied.

---

## Direct Competitors (same functional scope)

### GLPI — Closest functional equivalent
- **What it is:** French open-source GPL tool. Full ITAM + ITIL service desk with tickets linked to assets. Self-hosted free, cloud €19–45/month.
- **Strengths:** Strong EU/French community, full lifecycle, asset-to-ticket linking
- **Weaknesses:** PHP architecture from the early 2000s, setup requires DevOps skill, cloud version is an afterthought, no purchase-to-decommission workflow, **zero NIS2 narrative**
- **Our angle:** Same functional scope, modern stack, SaaS-first (no DevOps required), explicit NIS2 positioning

### Alloy Navigator
- **What it is:** US commercial ITSM + ITAM, tickets native to assets, cloud and on-premises
- **Pricing:** $19–83/tech/month + separate asset audit licenses ($70+/month) — confusing per-tech + per-node billing
- **Weaknesses:** No EU presence, no NIS2 positioning, pricing model is complex and expensive for SMBs
- **Our angle:** Simpler pricing (per company size, not per tech), EU-native, NIS2 ready

### ManageEngine AssetExplorer
- **What it is:** Full lifecycle (purchase, warranty, disposal, procurement). $795/year for 250 assets.
- **Weaknesses:** Tickets are in a **separate product** (ServiceDesk Plus) — you need two ManageEngine products to get asset + incidents. UI is dated. No NIS2.
- **Our angle:** Assets + incidents in one product, no module fragmentation

---

## Partial Competitors (cover part of the scope)

### Lansweeper 🇧🇪 — Most dangerous competitor on NIS2
- **What it is:** Belgian IT asset discovery tool. The only competitor with a comprehensive NIS2 marketing program.
- **Pricing:** Free (100 assets) → €199/month Starter. Jumps fast.
- **Strengths:** Strong NIS2 content (solution pages, checklists, DORA overlap guides), EU-based, enterprise trust
- **Weaknesses:** Discovery tool only — **no service desk, no ticket-to-asset linking** (requires Freshservice/Jira integration). Targeted at security teams, not SMB office managers. Not a lifecycle workflow tool.
- **Our angle:** We do what Lansweeper can't — manage the full lifecycle AND link incidents to assets, all in one tool, at SMB prices

### Freshservice
- **What it is:** Best-in-class ITSM SaaS UX with an asset module
- **Pricing trap:** Tickets cost $19–119/agent/month AND assets cost extra ($75/month for 500 assets; $1,500/month unlimited). A 50-person company ends up at €400–600+/month.
- **Weaknesses:** Expensive at scale, no NIS2, not EU-hosted, not open source
- **Our angle:** Flat pricing per company size, not per agent + per asset. 10x cheaper for SMBs.

### Jira Service Management
- **What it is:** Atlassian ITSM. Asset management only in Premium plan ($47–53/agent/month)
- **Weaknesses:** No lifecycle workflow (no purchase, warehouse). Complex for SMBs. Atlassian explicitly has no NIS2 resources. US company, GDPR exposure.
- **Our angle:** Purpose-built for IT asset lifecycle, not bolted onto a project management tool

### Snipe-IT — Most starred open source ITAM (~12,000 GitHub stars)
- **What it is:** US open-source AGPL hardware lifecycle tracker. Self-hosted free, cloud $39.99–249/month.
- **Strengths:** Great open source community, good lifecycle (purchase → assignment → check-in/out → audit)
- **Fatal gap:** **No incident management. No service desk. No ticket linked to any asset.** The most cited limitation in reviews.
- **Weaknesses:** No NIS2 content, no SaaS-first experience, no EU presence
- **Our angle:** We are Snipe-IT + a proper incident module + NIS2 narrative + EU SaaS

### Spiceworks
- **What it is:** Free, ad-supported helpdesk with basic network scanning
- **Weaknesses:** Ad-supported (unprofessional for compliance use), stagnant development, no lifecycle, no NIS2, no EU
- **Our angle:** Not a real competitor at this point — legacy product for companies that haven't upgraded

### Device42 (acquired by Freshworks 2023)
- **What it is:** Enterprise CMDB and autodiscovery. $1,449/year minimum.
- **Weaknesses:** Enterprise-only, datacenter-focused, no employee portal, no service desk, overkill for SMBs
- **Not a competitor** — different market segment entirely

---

## Competitive Matrix

| Capability | DSM | Lansweeper | Snipe-IT | Freshservice | GLPI |
|---|---|---|---|---|---|
| Full lifecycle (purchase → warehouse → assign → decomm) | ✅ | Partial | ✅ | Partial | ✅ |
| Incidents natively linked to assets | ✅ | ❌ (integration) | ❌ | ✅ | ✅ |
| SMB flat pricing (no per-agent trap) | ✅ | ❌ | ✅ (self-hosted) | ❌ | ✅ (self-hosted) |
| Open source version | ✅ | ❌ | ✅ | ❌ | ✅ |
| NIS2 EU compliance narrative | ✅ | ✅ (strong) | ❌ | ❌ | ❌ |
| SaaS-first, no DevOps required | ✅ | ✅ | ❌ | ✅ | ❌ |
| EU-based company | ✅ 🇪🇸 | ✅ 🇧🇪 | ❌ | ❌ | ✅ 🇫🇷 |
| Under €200/month for 50-person company | ✅ | ❌ | ✅ (self-hosted) | ❌ | ✅ (self-hosted) |

---

## NIS2 — The Market Timing Advantage

Only Lansweeper has a serious NIS2 marketing program. Every other tool — Freshservice, JSM, Snipe-IT, ManageEngine, GLPI — has zero NIS2 positioning.

Under NIS2 Article 21, organizations must implement:
- **Asset management** — hardware + software inventory, explicitly required
- **Incident reporting** — 24h preliminary, 72h full report, tied to specific assets
- **Supply chain security** — knowing what hardware/software is deployed and by whom
- **Audit trails** — documented history of every device and every incident

DeskSupportMonkey answers all four natively. Lansweeper only answers the first.

**The window:** Lansweeper is targeting security teams at larger companies. Nobody is targeting the IT manager at a 25-100 person company who has just been told by their lawyer that they need to document their devices. That person needs something that works in a day, costs under €100/month, and doesn't require a DevOps engineer.

---

## Positioning Statement

> DeskSupportMonkey is the only IT asset management tool built for SMBs that combines full device lifecycle, asset-linked incidents, and NIS2 compliance — without a per-agent pricing trap, without DevOps setup, and with a free open source version for companies that want to self-host.

---

## Risks

- **Lansweeper adds a service desk** — they have the NIS2 brand and the distribution. If they add lifecycle workflows and incidents natively, the gap closes. Monitor their product roadmap.
- **Snipe-IT adds incidents** — if the open source community builds a proper incident module, the open source angle weakens. Unlikely in the short term given the project's scope.
- **Freshservice cuts pricing for SMBs** — possible but unlikely given their enterprise trajectory post-Freshworks IPO.
- **GLPI gets a modern UI and NIS2 content** — they have the functional parity; if they execute on UX and marketing, they're a real threat in the EU market.
