# Competitive Analysis: Compliance Focus (NIS2, DORA, ISO 27001, CRA)

**Date:** 2026-02-27
**Product:** DSM Control / DeskSupportMonkey
**Focus:** How competitors position themselves around EU regulatory compliance

---

## Executive Summary

The EU compliance landscape (NIS2 effective Oct 2024, DORA effective Jan 2025, CRA expected 2027) has created a massive demand signal. Yet the competitive field splits clearly:

1. **Pure GRC tools** (ServiceNow GRC, Archer, CyberArrow) — compliance dashboards, not operational ITSM/ITAM
2. **Discovery-only tools** (Lansweeper, Ivanti) — strong compliance marketing, no service desk
3. **ITSM suites** (Freshservice, JSM, ManageEngine) — operational tools with zero or weak compliance narrative
4. **EU-native ITSM+ITAM combos** (GLPI, ALVAO, Proactivanet, Matrix42, Deepser) — functional overlap with DSM but varied compliance positioning

**The gap remains:** No sub-€300/month tool combines ITSM + ITAM + asset-linked incidents + explicit multi-framework compliance narrative (NIS2 + DORA + ISO 27001 + CRA) + flat SMB pricing + open source tier. DSM Control fills this.

---

## Tier 1: Strong Compliance Marketing (Dangerous Competitors)

### Lansweeper 🇧🇪 — The NIS2/DORA Marketing Leader

- **Compliance positioning:** THE most aggressive. Dedicated solution pages for [NIS2](https://www.lansweeper.com/solutions/use-cases/nis2-directive-compliance/), [DORA](https://www.lansweeper.com/compliance/dora/), whitepapers, checklists, partner integrations (Valiantys + HYCU + Appfire for Jira-based GRC)
- **What they cover:** Asset discovery, vulnerability reports, encryption status, backup coverage, access control mappings, OT device scanning
- **NIS2:** Full solution page, readiness checklist PDF, blog series, webinars
- **DORA:** [Dedicated page](https://www.lansweeper.com/blog/partners-and-integrations/navigating-compliance-with-dora-and-nis2-a-simple-solution/) but requires partner stack (Jira + Confluence + third-party apps) for incident management, risk registers, and audit workflows
- **ISO 27001:** Mentioned as foundation, not a standalone offering
- **CRA:** Not mentioned
- **Pricing:** $2,400/year Starter (2,000 assets), $4,308/year Pro (up to 9,000 assets), Enterprise custom (10,000+)
- **Fatal gap:** STILL no service desk, no ticket-to-asset linking, no incident management. Requires Freshservice/Jira integration for incidents. Targeted at security teams, not IT managers.
- **Risk level: HIGH** — They have the SEO, the content, the brand trust. If they ever add a service desk, the gap closes fast.

### Matrix42 🇩🇪 — The European Enterprise Choice

- **Compliance positioning:** Strong. [NIS2 + DORA compliance guide](https://www.matrix42.com/en/nis2-and-dora-compliance-guide), webinars, blog posts. Positions as "The European Choice in Service Management"
- **What they cover:** Full ITSM + ITAM + SAM + Identity Governance + Endpoint Protection + Risk Management, all integrated. GDPR, NIS2, DORA, EU AI Act compliance built into messaging
- **NIS2:** Dedicated guide and webinar
- **DORA:** [Full blog post](https://blog.matrix42.com/achieving-dora-compliance) on achieving DORA with integrated ITAM/ITSM/SAM
- **ISO 27001:** Foundation for their compliance narrative
- **CRA:** Mentioned in broader EU regulation context
- **Pricing:** Not public. Enterprise quotes only. Estimated €5,000-15,000+/year based on market analysis
- **Fatal gap:** Enterprise-only. No SMB pricing. No open source. Overkill for a 25-100 person company.
- **Risk level: MEDIUM** — Not competing for SMBs, but validates the EU compliance + ITSM/ITAM narrative.

### Ivanti 🇺🇸 — Enterprise Compliance Suite

- **Compliance positioning:** Strong. Dedicated pages for [NIS2](https://www.ivanti.com/compliance/nis2-directive-compliance) and [DORA](https://www.ivanti.com/compliance/dora). Full UEM + ITSM + GRC stack
- **What they cover:** Endpoint management, risk management, self-healing devices, automated compliance processes, real-time compliance status monitoring
- **NIS2:** Dedicated solution page with detailed mapping
- **DORA:** Dedicated page with incident management, resilience testing, third-party risk
- **ISO 27001:** Foundation framework
- **CRA:** Not specifically addressed
- **Pricing:** Not public. Custom quotes. Reviews describe it as "expensive" and requiring "multiple professional service partners to implement"
- **Fatal gap:** Enterprise-only. Complex implementation. No SMB path. No open source.
- **Risk level: LOW** — Not our market segment.

---

## Tier 2: Compliance-Aware (Functional Competitors)

### Proactivanet 🇪🇸 — Direct Spanish Competitor

- **Compliance positioning:** Active. Blog posts on [NIS2 + DORA readiness](https://www.proactivanet.com/en/blog/press/are-companies-really-ready-to-comply-with-nis2-and-dora-regulations-keys-to-anticipate-change/), [NIS2 + ENS + DORA regulatory challenge](https://www.proactivanet.com/en/blog/proactivanet-en/nis2-ens-and-dora-the-regulatory-challenge-putting-cybersecurity-teams-to-the-test/), cyber-attack prevention guides
- **What they cover:** Full ITAM + ITSM. ISO 9001, ISO 20000, ISO 27001, ISO 27017 certified. 16 PinkVERIFY certified ITSM processes. Spanish ENS compliance
- **NIS2:** Blog content and ITAM-focused compliance messaging. Positions ITAM as essential for NIS2 evidence
- **DORA:** Mentioned alongside NIS2 in blog posts
- **ISO 27001:** Fully certified themselves
- **CRA:** Not addressed
- **Pricing:** Not publicly available. Traditional enterprise licensing
- **Strengths:** Same Spanish market. Already ISO certified. Strong ITIL credentials. Referenced by Deloitte's 2025 ITAM survey
- **Fatal gap:** No open source. Old-school enterprise sales. No modern SaaS pricing for SMBs. Blog content only — no dedicated compliance solution pages
- **Risk level: HIGH for Spain** — They are the incumbent in the Spanish IT management space and are starting to talk compliance. But their compliance positioning is blog-level, not product-level.

### ALVAO 🇨🇿 — Czech EU-Native ITSM+ITAM

- **Compliance positioning:** Moderate-Strong. Dedicated [ISO 27001 solution page](https://www.alvao.com/en/ISO-27001), NIS2 guide, cybersecurity blog content
- **What they cover:** Full ITSM + ITAM + CMDB. ISO 27001 and SOC 2 Type 2 certified. Runs on Microsoft Azure EU. Supports NIS2, DORA, Cyber Essentials
- **NIS2:** [Dedicated guide](https://lp.alvao.com/cs/pruvodce-nis2) (Czech), blog posts on ITAM/ITSM role in cybersecurity
- **DORA:** Listed as supported framework
- **ISO 27001:** Full solution page showing how ALVAO maps to ISO 27001 controls (change management, incident management, asset management, audit trails)
- **CRA:** Not specifically addressed
- **Pricing:** Not publicly available. GetApp lists as subscription-based
- **Strengths:** EU-native, Azure-hosted, proper certifications, ITSM+ITAM combination, audit trail capabilities
- **Fatal gap:** Czech-focused (limited Spanish/DACH presence). No open source. No public SMB pricing. Limited English content
- **Risk level: MEDIUM** — Validates our approach. Could become a competitor if they expand west.

### ManageEngine ServiceDesk Plus 🇮🇳 (Zoho)

- **Compliance positioning:** Moderate. Dedicated [NIS2 page](https://www.manageengine.com/nis2-directive.html), [ISO 27001 ITSM guide](https://www.manageengine.com/products/service-desk/itsm/iso-27001-requirements.html), DORA compliance page (via Endpoint Central)
- **What they cover:** ITSM (ServiceDesk Plus) + UEM (Endpoint Central) + ITAM (AssetExplorer) — but SEPARATE products. NIS2 compliance spread across multiple modules
- **NIS2:** Dedicated page, but mostly pointing to Endpoint Central, not ServiceDesk Plus
- **DORA:** Via [Endpoint Central](https://www.manageengine.com/products/desktop-central/digital-operational-resilience-act-compliance.html), not the service desk
- **ISO 27001:** ManageEngine itself is ISO 27001 certified. Published detailed [PDF mapping](https://download.manageengine.com/products/service-desk/itsm/iso-27001-requirement.pdf) ISO 27001 to ITSM practices
- **CRA:** Not addressed
- **Pricing:** ServiceDesk Plus $13-66/tech/month + AssetExplorer $795/year/250 assets separately
- **Fatal gap:** You need 2-3 separate ManageEngine products to get full compliance coverage. Module fragmentation. Not EU-based (India/US). Complex pricing
- **Risk level: MEDIUM** — Strong brand, weak compliance execution. The ISO 27001 guide is actually useful content that we should match or exceed.

### InvGate 🇦🇷 — The Spanish-Speaking ITSM+ITAM Heavyweight

- **Company profile:** Founded 2008 in Buenos Aires. ~252 employees across 5 continents. **$30.3M revenue (2023)**. Bootstrapped until $35M funding round (Bossa Invest, Endeavor Catalyst). Named 2026 Champion in Midmarket ITSM by Info-Tech (composite score 9.1). Customers include NASA JPL, PwC, Collins Aerospace, PeoplesBank
- **Compliance positioning:** Moderate. ISO 27001:2022 and SOC 2 Type II certified (themselves). Published [NIS2 compliance blog](https://blog.invgate.com/nis2-requirements-asset-management) mapping 10 NIS2 requirements to ITAM/ITSM
- **What they cover:** ITSM (InvGate Service Management) + ITAM (InvGate Asset Management) as separate products. CMDB with auto-discovery, visual workflow builder, self-service portal, software license compliance tracking, CI change tracking with full audit trails
- **NIS2:** Blog content only — ["10 Ideas in Which Asset Management And ITSM Can Help"](https://blog.invgate.com/nis2-requirements-asset-management). No dedicated solution page
- **DORA:** Not specifically addressed
- **ISO 27001:** Multiple blog posts on [incident management](https://blog.invgate.com/iso-27001-incident-management), [checklist](https://blog.invgate.com/iso-27001-checklist), [IT audit software](https://blog.invgate.com/it-audit-software). Good SEO content, but blog-level — no product-level compliance feature
- **CRA:** Not addressed
- **Pricing:** ITSM: $17/agent/month (Starter, up to 5 agents), $40/agent/month (Pro, 6-50 agents), Enterprise custom. ITAM: separate — $0.21/node/month. Enterprise tier adds on-premise hosting, concurrent licensing, BYOAI
- **Strengths:**
  - **Content marketing machine** — Their blog (blog.invgate.com) dominates SEO for "X vs Y" ITSM comparisons. They write comparison pages for every competitor (Freshservice, ManageEngine, Snipe-IT, Ivanti, Jira, NinjaOne)
  - **Modern UI** — Consistently praised in reviews. Visual workflow builder, intuitive self-service portal
  - **Spanish-speaking** — Argentine company with natural advantage in LATAM and Spanish EU markets. G2 reviews appear in Spanish
  - **ITSM + ITAM combined** — Both products exist, with CMDB auto-discovery and CI audit trails
  - **Integrations** — Native connections to SCCM, Filewave, Kandji, and Lansweeper (!)
  - **Scale** — $30M revenue, 252 employees. This is not a small startup
- **Weaknesses:**
  - **Two separate products** — ITSM and ITAM are different purchases. Not as unified as DSM Control
  - **Per-agent + per-node pricing** — Adds up fast. A 50-person company with 500 assets: ~$2,000+/month ITSM + ~$105/month ITAM = ~$2,100/month. DSM Control: €149-299/month
  - **No EU hosting** — Company HQ in Argentina, infrastructure not EU-native. GDPR exposure for EU customers
  - **No open source tier** — Proprietary only
  - **Blog-level compliance** — Extensive NIS2/ISO content as SEO bait, but no product-level compliance features (no compliance dashboards, no regulatory report templates, no framework mapping in the product itself)
  - **Not EU-based** — Can't claim EU data sovereignty the way DSM Control can
- **Risk level: MEDIUM-HIGH** — They have the revenue ($30M), the content marketing engine, the Spanish language advantage, and the functional depth. They're one product merge + one EU compliance push away from being dangerous. The fact that they integrate with Lansweeper suggests they could bolt on compliance via partnership. **Monitor closely.**
- **Our angle:** "Same ITSM+ITAM features at 1/10 the price, with EU hosting, open source option, and built-in compliance mapping — not just blog posts about compliance"

---

## Tier 3: Zero Compliance Positioning

### Freshservice 🇮🇳 (Freshworks)

- **NIS2:** Zero content. No mention anywhere
- **DORA:** Zero content
- **ISO 27001:** Freshworks is certified, but no compliance solution pages for customers
- **CRA:** Nothing
- **Pricing:** $19-119/agent/month + $75-1,500/month for assets
- **Status:** Best ITSM UX on the market, but has completely ignored EU compliance. US-focused post-IPO trajectory
- **Risk level: LOW on compliance** — If they wake up and add NIS2 content + EU hosting, they're dangerous. But their DNA is US SaaS, not EU regulation.

### Jira Service Management 🇺🇸 (Atlassian)

- **NIS2/DORA:** Atlassian has NO official compliance pages. Community forum posts asking about NIS2 go [unanswered by Atlassian](https://community.atlassian.com/forums/Jira-Service-Management/Jira-Service-Management-Atlassian-NIS2-compliance/qaq-p/2513522). Third-party partners (Revyz, Cyrima, Automation Consultants) fill the gap with [guides](https://www.automation-consultants.com/complying-with-dora-and-nis2-a-guide-for-atlassian-users/) and Marketplace add-ons
- **ISO 27001:** Atlassian is certified. No customer-facing compliance tools
- **CRA:** Nothing
- **Pricing:** Free (3 agents), $22-53/agent/month. Assets only in Premium+
- **Status:** Relies entirely on ecosystem/Marketplace for compliance. [Cyrima add-on](https://marketplace.atlassian.com/apps/1234334/cyrima-cyber-risk-management-compliance-for-jira) turns NIS2/DORA/CRA/GDPR into Jira tasks — proves market demand
- **Risk level: LOW** — Too generic, too US-focused, too reliant on add-ons for compliance

### Snipe-IT 🇺🇸 — The Open Source ITAM King (With a Compliance Blind Spot)

- **Company profile:** Created by Grokability, Inc. Open source (AGPL-3.0). Most starred open source ITAM on GitHub (~11k+ stars). Written in PHP/Laravel. Self-hosted free, cloud tiers at $39.99/month (Basic), $99.99/month (Small Business), $249.99/month (Dedicated). Enterprise support: $4,999.99/year
- **Compliance positioning:** Absolute zero. No NIS2, no DORA, no ISO 27001, no CRA — neither in marketing, content, nor product features
- **What they cover:** Hardware asset lifecycle (check-in/check-out, assignment, audit), custom fields, custom asset models, software license tracking (basic), REST API, bcrypt + 2FA + HTTPS security, audit logs for every action
- **NIS2:** Nothing. Zero content, zero features
- **DORA:** Nothing
- **ISO 27001:** Nothing
- **CRA:** Nothing
- **Pricing:** Free self-hosted (unlimited assets/users) | Cloud: $39.99-249.99/month | Enterprise support: $4,999.99/year
- **Strengths:**
  - **Open source community** — Largest ITAM open source community. High trust among self-hosters and DevOps teams
  - **Asset lifecycle basics** — Check-in/out, assignment, warranty tracking, depreciation, model grouping — all solid
  - **Audit logs** — Every action logged (assignment, status change, check-in/check-out). Good for accountability
  - **Free self-hosted** — Zero cost barrier to entry. Very attractive to budget-conscious organizations
  - **REST API** — Powerful API enables custom integrations. Community has built connections to Jira, JAMF, Kandji
  - **Simplicity** — Does one thing (asset tracking) and does it well. Low learning curve
- **Weaknesses:**
  - **NO service desk / incident management** — This is the [most requested feature](https://github.com/snipe/snipe-it/issues/663) (GitHub issue #663, open since 2015). A helpdesk/ticket system has been requested for 10+ years and never implemented. [Integration requests](https://github.com/snipe/snipe-it/issues/14145) for Zendesk/ticketing are also open and unresolved
  - **No asset-linked incidents** — Without a service desk, there's no way to link an incident to the device that caused it. The core compliance requirement (NIS2 Art.21, DORA Chapter II) of tracing incidents to specific assets is impossible
  - **No automation** — Everything manual. No workflow builder, no auto-assignment, no escalation rules
  - **No network discovery** — Assets must be entered manually or via CSV import. No auto-discovery of devices on the network
  - **Limited reporting** — Basic reports only. No advanced analytics, no customizable dashboards, no compliance-ready exports
  - **Software license management is weak** — Hardware tracking is strong, but software compliance tracking is frequently cited as insufficient
  - **PHP/Laravel stack** — Not a weakness per se, but limits the developer pool compared to Python/Node ecosystems. Makes it harder to extend
  - **No SaaS-first UX** — Cloud version exists but feels like "hosted self-hosted" rather than a polished SaaS product
  - **Stagnant on big features** — The helpdesk request has been open for 10+ years. The project is actively maintained (frequent releases) but focused on incremental improvements, not scope expansion
- **Risk level: ZERO on compliance** — They have never shown interest in compliance, EU regulation, or incident management. The project scope is deliberately narrow: asset tracking only
- **Risk of adding incidents:** LOW in the short term. The maintainer has kept scope tight for 10+ years. Adding a full service desk would be a fundamental architecture change. More likely that users who outgrow Snipe-IT migrate to a tool like DSM Control than that Snipe-IT adds incidents natively
- **Our angle:** "We are what Snipe-IT users graduate to. Same open source ethos, same asset lifecycle — plus incidents linked to assets, compliance mapping, and a service desk. No more juggling Snipe-IT + Zendesk + spreadsheets"
- **Migration opportunity:** Snipe-IT's ~11k GitHub stars represent thousands of organizations that will eventually need incidents, compliance, and a service desk. A Snipe-IT → DSM migration guide + CSV import tool could capture this migration path

### GLPI 🇫🇷

- **NIS2/DORA:** Zero official content. No compliance solution pages, no blog posts
- **ISO 27001:** Not addressed
- **CRA:** Nothing
- **Status:** Full ITAM + ITSM functionality. French (EU-native). But they have completely ignored the compliance wave. Their website talks about ITIL, not regulation
- **Risk level: MEDIUM** — They have the functional depth. If they add NIS2 content and modernize the UI, they're a real threat. But as of Feb 2026, nothing.

### Deepser 🇮🇹

- **Compliance positioning:** Minimal. One [blog post on ISO compliance + ITSM](https://www.deepser.com/why-use-itsm-software-for-compliance-and-quality-management/). No NIS2, DORA, or CRA content
- **Status:** Italian, EU-based, modular ITSM, ISO 20000 focused. ~$35/user/month. But compliance is an afterthought
- **Risk level: LOW** — Could wake up (Italian companies face NIS2 too), but no signs of it

---

## Adjacent Category: Pure GRC/Compliance Software

These tools DON'T do ITSM/ITAM but compete for the "compliance budget" of SMBs.

| Tool | Origin | NIS2 | DORA | ISO 27001 | CRA | SMB Pricing | Notes |
|------|--------|------|------|-----------|-----|-------------|-------|
| **Cyberday** | 🇫🇮 Finland | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ~€200/mo | ISMS-focused. Templates + task mapping. No ITAM/ITSM |
| **CyberArrow** | 🇦🇪 UAE | ✅ | ✅ | ✅ | Partial | Not public | GRC automation. 80+ framework support |
| **ISMS.online** | 🇬🇧 UK | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ~£400/mo | Premium content marketing. Compliance mapping guides |
| **Sprinto** | 🇮🇳 India | Partial | Partial | ✅ Full | ❌ | $8k-20k/yr | SOC 2 + ISO focused. Continuous monitoring |
| **ServiceNow GRC** | 🇺🇸 | ✅ | ✅ | ✅ | ✅ | Enterprise only | Full GRC module. Pre-built NIS2/ISO 27001 content packs |
| **USU GRC** | 🇩🇪 | ✅ | ✅ | ✅ | ✅ | Enterprise only | German. Full [GRC product](https://www.usu.com/en/it-service-management/governance-risk-compliance-grc-cyber-resilience-act) |

**Key insight:** These tools are NOT competition — they're potential **complementary** partners. A company needs Cyberday for compliance framework management AND DSM Control for the operational evidence (assets, incidents, audit trails). This is a co-marketing opportunity, not a conflict.

---

## Compliance Coverage Matrix (Updated)

| Capability | DSM Control | Lansweeper | InvGate | Snipe-IT | Proactivanet | ALVAO | Matrix42 | ManageEngine | GLPI | Freshservice | JSM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **NIS2 solution page** | ✅ | ✅ Strong | Blog only | ❌ | Blog only | ✅ (CZ) | ✅ | ✅ (via Endpoint) | ❌ | ❌ | ❌ |
| **DORA solution page** | ✅ | ✅ (partner) | ❌ | ❌ | Blog only | Mentioned | ✅ | ✅ (via Endpoint) | ❌ | ❌ | ❌ |
| **ISO 27001 mapping** | ✅ | Foundation | Blog only | ❌ | Certified | ✅ Full | ✅ | ✅ PDF guide | ❌ | ❌ | ❌ |
| **CRA content** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Mentioned | ❌ | ❌ | ❌ | ❌ |
| **ITSM (incidents)** | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **ITAM (lifecycle)** | ✅ | Discovery only | ✅ (separate) | ✅ | ✅ | ✅ | ✅ | Separate product | ✅ | Extra cost | Premium only |
| **Asset-linked incidents** | ✅ | ❌ | ✅ (2 products) | ❌ | ✅ | ✅ | ✅ | 2 products needed | ✅ | ✅ | Partial |
| **EU-based** | ✅ 🇪🇸 | ✅ 🇧🇪 | ❌ 🇦🇷 | ❌ 🇺🇸 | ✅ 🇪🇸 | ✅ 🇨🇿 | ✅ 🇩🇪 | ❌ 🇮🇳 | ✅ 🇫🇷 | ❌ 🇮🇳 | ❌ 🇺🇸 |
| **SMB flat pricing** | ✅ | ❌ | ❌ (per-agent) | ✅ (self-hosted) | ❌ | ❌ | ❌ | ❌ | ✅ (self-hosted) | ❌ | ❌ |
| **Open source** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Under €300/mo (50-person co.)** | ✅ | ❌ (~€200+) | ❌ (~€2,100) | ✅ (free) | Unknown | Unknown | ❌ | ❌ (fragmented) | ✅ (self-hosted) | ❌ (~€500+) | ✅ (limited) |

---

## Strategic Findings

### 1. DSM Control is the ONLY tool with all four compliance frameworks
No competitor has dedicated content for NIS2 + DORA + ISO 27001 + CRA in a single ITSM/ITAM product. Lansweeper covers NIS2 + DORA but has no service desk. Matrix42 covers NIS2 + DORA but is enterprise-only. ManageEngine fragments across products. GLPI, Freshservice, and JSM cover none.

### 2. The "compliance + operations" gap is real
Pure GRC tools (Cyberday, ISMS.online) handle framework documentation but don't manage assets or incidents. ITSM tools manage operations but don't map to compliance. DSM Control sits in the intersection — operational tool with compliance narrative.

### 3. Lansweeper is the only dangerous compliance competitor
They have the SEO dominance, the content depth, and the EU presence. But they STILL can't manage incidents or run a service desk. Their DORA solution requires a 4-vendor stack (Lansweeper + Jira + Confluence + Appfire). Our pitch: "Do it all in one tool."

### 4. Proactivanet is the Spanish market risk
They're the Spanish incumbent, already ISO 27001 certified, and starting to publish compliance blog content. But their compliance positioning is blog-level (not product-level), their pricing isn't SMB-friendly, and they have no open source offering. We need to establish SEO dominance for "NIS2 + gestion de activos" before they do.

### 5. The CRA is unoccupied territory
The Cyber Resilience Act (expected 2027) is almost completely ignored by competitors. Only ISMS.online and Cyberday mention it. DSM Control has a full CRA page — this gives us 12-18 months of SEO advantage for CRA-related searches.

### 6. GLPI is a sleeping giant
French, open source, full ITAM+ITSM. If they add NIS2 content and modernize their UI, they become the most dangerous competitor. As of Feb 2026, they haven't moved. Monitor quarterly.

---

## Recommended Actions

### Immediate (Q1 2026)
1. **SEO offensive:** Create long-form guides for "NIS2 + IT asset management", "DORA + ITSM", "ISO 27001 + service desk", "CRA compliance for SMBs" in both ES and EN
2. **Comparison pages:** Create vs-pages for Lansweeper, Proactivanet, and GLPI with explicit compliance angle
3. **Co-marketing:** Approach Cyberday (Finland) and ISMS.online (UK) for integration partnerships — "Use us for operational evidence, use them for framework management"

### Short-term (Q2 2026)
4. **Compliance readiness checklist:** Interactive self-assessment tool on dsmcontrol.com — captures leads
5. **Audit trail dashboard:** Build a compliance evidence export feature (PDF/CSV) that maps DSM data to NIS2 Art.21, DORA Chapter II, ISO 27001 Annex A controls
6. **ENS (Esquema Nacional de Seguridad):** Add Spanish ENS compliance page — Proactivanet mentions it, we should too

### Medium-term (Q3-Q4 2026)
7. **ISO 27001 self-certification narrative:** Document how DSM Control's own infrastructure meets ISO 27001
8. **DORA reporting templates:** Pre-built incident report templates matching DORA's 4-hour/72-hour reporting requirements
9. **Partner certifications:** Get PinkVERIFY or similar ITSM certification to match Proactivanet's credentialing

---

## Sources

- [Lansweeper NIS2 Compliance](https://www.lansweeper.com/solutions/use-cases/nis2-directive-compliance/)
- [Lansweeper DORA + NIS2 Partner Solution](https://www.lansweeper.com/blog/partners-and-integrations/navigating-compliance-with-dora-and-nis2-a-simple-solution/)
- [ALVAO ISO 27001 Solution](https://www.alvao.com/en/ISO-27001)
- [ALVAO ITAM/ITSM Cybersecurity Role](https://www.alvao.com/en/blog/role-of-itam-and-itsm-cybersecurity)
- [Matrix42 NIS2/DORA Guide](https://www.matrix42.com/en/nis2-and-dora-compliance-guide)
- [Matrix42 DORA with ITAM/ITSM/SAM](https://blog.matrix42.com/achieving-dora-compliance)
- [Proactivanet NIS2/DORA Readiness](https://www.proactivanet.com/en/blog/press/are-companies-really-ready-to-comply-with-nis2-and-dora-regulations-keys-to-anticipate-change/)
- [Proactivanet NIS2/ENS/DORA Challenge](https://www.proactivanet.com/en/blog/proactivanet-en/nis2-ens-and-dora-the-regulatory-challenge-putting-cybersecurity-teams-to-the-test/)
- [ManageEngine NIS2](https://www.manageengine.com/nis2-directive.html)
- [ManageEngine ISO 27001 ITSM Guide](https://www.manageengine.com/products/service-desk/itsm/iso-27001-requirements.html)
- [ManageEngine DORA via Endpoint Central](https://www.manageengine.com/products/desktop-central/digital-operational-resilience-act-compliance.html)
- [Ivanti NIS2](https://www.ivanti.com/compliance/nis2-directive-compliance)
- [Ivanti DORA](https://www.ivanti.com/compliance/dora)
- [InvGate NIS2 + ITAM](https://blog.invgate.com/nis2-requirements-asset-management)
- [USU GRC NIS2/DORA/CRA](https://www.usu.com/en/it-service-management/governance-risk-compliance-grc-cyber-resilience-act)
- [Atlassian Community NIS2 Discussion](https://community.atlassian.com/forums/Jira-Service-Management/Jira-Service-Management-Atlassian-NIS2-compliance/qaq-p/2513522)
- [Atlassian NIS2/DORA Guide (Automation Consultants)](https://www.automation-consultants.com/complying-with-dora-and-nis2-a-guide-for-atlassian-users/)
- [Cyrima NIS2/DORA for Jira](https://marketplace.atlassian.com/apps/1234334/cyrima-cyber-risk-management-compliance-for-jira)
- [Deepser ISO Compliance](https://www.deepser.com/why-use-itsm-software-for-compliance-and-quality-management/)
- [ServiceNow NIS2/DORA (Plat4mation)](https://plat4mation.com/workflow/steering-governance/going-beyond-nis2-dora/)
- [Cyberday NIS2/DORA Comparison](https://www.cyberday.ai/blog/comparing-eu-cybersecurity-frameworks)
- [ISMS.online NIS2/DORA/CRA Guide](https://www.isms.online/nis-2/vs/dora-vs-eu-ai-act-vs-cra/)
- [CyberArrow Top 5 GRC 2026](https://www.cyberarrow.io/blog/top-5-compliance-software-solutions/)
- [NIS2/DORA/ISO 27001 2026 Compliance Manual](https://kymatio.com/blog/nis2-iso-27001-and-dora-compliance-manual-version-2026)
- [Deloitte 2025 ITAM Survey via Proactivanet](https://www.proactivanet.com/en/blog/itam-software/it-asset-management-5-strategic-keys-according-to-deloitte/)
