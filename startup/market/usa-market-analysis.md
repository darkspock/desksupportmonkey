# USA Market Analysis

**Date:** 2026-02-25
**Status:** Exploratory — potentially accelerated via DoD channel partner
**Focus:** CMMC as primary angle, HIPAA and SOC 2 as secondary

---

## Regulatory Landscape: No Single NIS2 Equivalent

The US does not have a single, cross-sector cybersecurity directive like NIS2. Instead, there is a patchwork of sector-specific regulations, federal mandates, and voluntary frameworks that create similar compliance pressure in isolated segments.

### Key Regulations Relevant to DSM Control's ICP

| Regulation | Sector | What it requires | Similarity to NIS2 |
|---|---|---|---|
| **CMMC 2.0** | Defense / DoD contractors | Asset inventory, access control, incident management, audit trail | Very high — closest NIS2 equivalent |
| **SEC Cybersecurity Rules (2023)** | Public companies | Report material incidents in 4 days, document risk management | Medium — more reporting than asset management |
| **HIPAA Security Rule** | Healthcare | Inventory of devices with ePHI, access controls, audit trail | High for healthcare sector |
| **CIRCIA (2022)** | Critical infrastructure | Report incidents to CISA within 72h (final rules in progress) | Medium — focused on reporting |
| **FedRAMP / FISMA** | Federal government and vendors | Asset management, configuration control, monitoring | High but public sector only |
| **SOC 2 Type II** | SaaS / tech (voluntary but required by clients) | Asset control, incident management, traceability | High — de facto mandatory in B2B SaaS |
| **State laws (NY SHIELD, CCPA/CPRA)** | Varies by state | Data protection, technical controls | Low-medium |

### Key Difference vs EU

**EU:** One directive (NIS2) creating a simultaneous compliance wave across hundreds of thousands of companies. Massive domino effect.

**USA:** Fragmented regulation by sector and by state. There is no single "NIS2 moment" where the entire market needs to act at once. The message "comply with X from day 1" is less powerful because X changes depending on the audience.

---

## The CMMC Opportunity

CMMC (Cybersecurity Maturity Model Certification) 2.0 is the regulation most similar to NIS2 in terms of ICP fit for DSM Control.

### What CMMC Requires

- **Asset inventory** — documented hardware and software assets
- **Access control** — who has access to what devices and data
- **Incident response** — documented incident handling tied to specific assets
- **Audit and accountability** — audit trail of all actions on controlled systems
- **Configuration management** — baseline configurations for all devices

### Addressable Market

| Segment | Companies |
|---|---|
| DoD contractors requiring CMMC certification | ~300,000+ |
| Of those: SMBs (10-300 employees) | ~200,000+ |
| Of those: currently using spreadsheets for asset tracking | ~130,000+ (estimated 65%) |

These are machine shops, small manufacturers, IT services firms, engineering companies, and defense subcontractors. Many are 20-100 employee companies with one IT person who has just been told by their prime contractor that they need CMMC Level 2 certification.

### CMMC Timeline

```
2024     — CMMC 2.0 final rule published
2025     — DoD begins including CMMC requirements in contracts
2025-26  — Contractors scrambling to prepare for assessments
2027+    — Full enforcement across all new DoD contracts
```

The pain is real and the timeline is active. Companies that cannot demonstrate CMMC compliance risk losing government contracts — their primary revenue source.

---

## HIPAA Opportunity

### Addressable Market

| Segment | Companies |
|---|---|
| HIPAA-covered entities in the US | ~725,000 |
| Of those: small practices and clinics (10-300 employees) | ~400,000+ |
| Of those: with meaningful IT asset management needs | ~100,000+ |

Small hospitals, clinics, dental offices, and medical practices have the same chaos as EU healthcare: hundreds of devices (nursing stations, diagnostic equipment, admin laptops) tracked in spreadsheets or not at all. HIPAA requires safeguards for devices that store or transmit ePHI, and enforcement is real — fines range from $100 to $50,000 per violation, up to $1.5M per year.

---

## Competitive Landscape

### Direct Competitors (ITAM + Incidents)

| Competitor | Base | Pricing | Strengths | Weakness |
|---|---|---|---|---|
| **Freshservice** | India/US | $19-119/agent + asset add-ons | Best UX in market, strong US brand | Expensive for SMBs, no CMMC/compliance narrative |
| **Jira Service Management** | US (Atlassian) | $0-47/agent | Ubiquitous in tech companies, Atlassian ecosystem | ITAM only in Premium plan, no full lifecycle |
| **ManageEngine ServiceDesk+** | India/US | $13-67/tech | Full functionality, good price | Dated UX, requires 2 products for ITAM+ITSM |
| **SysAid** | Israel/US | Custom pricing | ITSM+ITAM integrated, AI features | Opaque pricing, mid-market and up |
| **InvGate** | Argentina/US | $17/agent | ITSM+ITAM combined, modern UX, good price | Small, low US awareness |

### ITAM Only (No Incidents)

| Competitor | Pricing | Strengths | Weakness |
|---|---|---|---|
| **Snipe-IT** | Open source / $40-250/mo cloud | 12K+ GitHub stars, r/sysadmin reference | **No incident management** — same gap as in EU |
| **Asset Panda** | Custom (from ~$1,500/yr) | Popular in US mid-market, configurable | No service desk, no compliance narrative |
| **Axonius** | Enterprise ($$$) | Asset intelligence, integrations, compliance mapping | Out of range for SMBs, enterprise pricing |
| **runZero (ex-Rumble)** | $0-custom | Network discovery, technically excellent | Discovery only, no lifecycle, no incidents |

### The MSP Channel (Very Relevant in USA)

In the US, many SMBs do not have internal IT — they outsource to MSPs (Managed Service Providers). MSPs use their own tooling:

| Tool | What it is | Why it matters |
|---|---|---|
| **ConnectWise** | RMM + PSA + ITAM | Dominates the MSP channel. Thousands of MSPs manage client assets here |
| **Kaseya/Datto** | RMM + PSA | Second largest in MSP space. Aggressive acquisitions |
| **NinjaOne** | RMM + endpoint management | Explosive growth, modern UX, loved by sysadmins |
| **Atera** | All-in-one IT management | Per-technician pricing (not per device), popular with small MSPs |

These are NOT direct competitors — they are RMM/PSA tools, not ITAM with full lifecycle. But they cover part of the problem and MSPs already use them. Any US strategy must account for the MSP channel as either a distribution partner or an indirect competitor.

---

## Competitive Matrix (USA Focus)

| Capability | DSM Control | Freshservice | Snipe-IT | NinjaOne | ManageEngine |
|---|---|---|---|---|---|
| Full lifecycle (purchase → decommission) | Yes | Partial | Yes | No | Yes (2 products) |
| Incidents natively linked to assets | Yes | Yes | No | No | Yes (2 products) |
| SMB flat pricing (no per-agent trap) | Yes | No | Yes (self-hosted) | No | No |
| Open source version | Yes | No | Yes | No | No |
| CMMC compliance narrative | **Not yet** | No | No | No | No |
| HIPAA compliance narrative | **Not yet** | No | No | No | No |
| SaaS-first, no DevOps required | Yes | Yes | No | Yes | Yes |

### The Gap

**Nobody in the US positions ITAM + incident management as a CMMC compliance tool.** The same vacuum that exists for NIS2 in Europe exists for CMMC in the US defense supply chain. The 300K+ DoD contractors need exactly what DSM Control provides, but nobody is speaking their language.

Similarly, **nobody targets small healthcare providers with a combined ITAM + incidents + HIPAA compliance narrative** at SMB-friendly pricing.

---

## US vs EU: Strategic Comparison

| Factor | EU (current) | USA (hypothetical) |
|---|---|---|
| Regulatory driver | NIS2 — single, universal | Fragmented (CMMC, HIPAA, SOC 2...) |
| Competition intensity | Low in the niche | More saturated |
| MSP channel | Smaller | Massive — potential partners or competitors |
| CAC | Low (organic) | Likely higher (noisy market) |
| Language | ES native, EN secondary | EN mandatory, no linguistic advantage |
| Pricing competitiveness | €49-199 very competitive | $49-199 still competitive vs Freshservice |
| Market size | ~250K-400K regulated SMBs | Millions of SMBs, but addressable niche varies |
| Sales cycle | Short (NIS2 = auditor told them to buy) | Longer (fragmented triggers) |
| Self-hosting demand | Moderate | High (privacy-conscious sysadmin culture) |

---

## Entry Strategy

### Recommended angle: CMMC for small defense contractors

**Why CMMC first:**
- Clearest regulatory pressure with enforcement timeline
- ICP matches perfectly: 10-200 employee companies with one IT person
- Pain is identical to NIS2: "the auditor asked and I had no answer"
- Nobody owns this niche yet
- Pricing advantage is significant vs Freshservice/ServiceNow

**What would be needed:**
1. CMMC-specific landing page mapping product features to CMMC Level 2 practices
2. CMMC compliance report/export feature in the product
3. Content: "How to meet CMMC asset management requirements without ServiceNow"
4. Community presence: r/CMMC, defense contractor LinkedIn groups, CMMC-focused events
5. Potential MSP partnerships — many MSPs serve defense contractors and need ITAM tools for their clients

### Timing (Organic — No Partner)

Phase 3+ (2027 earliest). Priorities in order:
1. Spain — home market, NIS2 (current)
2. Germany + Italy — NIS2 expansion (2026-2027)
3. France + Netherlands — NIS2 expansion (2027)
4. USA / CMMC — only after EU product-market fit is proven and compliance playbook is validated

---

## Accelerated Entry: DoD Channel Partner / Investment Fund

### The scenario

A US-based investment fund or holding company that acquires, invests in, or distributes software to the DoD contractor supply chain. They bring the channel; DSM Control brings the product.

### Why this changes the equation

Without a partner, entering the US requires building awareness, credibility, distribution, compliance certifications, and US infrastructure from scratch — high CAC, long timeline, no competitive advantage in distribution.

With a DoD channel partner:

| What the partner brings | What DSM Control brings |
|---|---|
| Direct access to DoD contractors (the channel) | The product (nobody has this for the niche) |
| Credibility in the defense market | Unbeatable pricing vs ServiceNow/Freshservice |
| Deep CMMC requirements knowledge | Open source + SaaS flexibility |
| Network of MSPs serving DoD contractors | Rapid development (AI-managed model) |
| Capital for US infrastructure | >90% gross margins |
| Sales and onboarding in US timezone | Product roadmap and engineering |

### Possible structures

| Model | Description | Pros | Cons |
|---|---|---|---|
| **Equity investment + distribution** | Fund takes minority stake, distributes to its portfolio/network | Aligned incentives, capital injection, skin in the game | Dilution, potential governance friction |
| **White-label / OEM** | Partner rebrands DSM Control for the DoD market | Zero CAC for DSM, partner owns the relationship | Lose brand, lose direct customer relationship |
| **Revenue share / reseller** | Partner resells DSM Control at markup, keeps margin | No dilution, DSM keeps brand | Less alignment, partner may deprioritize |
| **Portfolio company** | Fund acquires majority, DSM Control becomes a portfolio asset | Maximum resources and distribution | Founder loses control |

**Recommended: Equity investment + distribution agreement.** Partner gets skin in the game and a return on investment; DSM Control gets channel access without losing control or brand.

### What would need to be validated

1. **Product-CMMC fit** — Does the current feature set map to CMMC Level 2 practices without major rework? Likely yes, but needs formal mapping.
2. **US data residency** — DoD contractors almost certainly require US-hosted infrastructure. Would need AWS us-east or us-west deployment.
3. **Branding** — White-label under partner's brand, co-branded, or DSM Control brand? Depends on partner preference and deal structure.
4. **Exclusivity** — The partner will likely want exclusivity for the DoD channel. Acceptable if limited to defense sector and US market only, preserving freedom for HIPAA, SOC 2, and all EU markets.
5. **Dilution** — How much equity for channel access? Benchmark: 10-25% for a strategic partner that delivers distribution + capital, depending on investment amount.
6. **Timeline** — With a partner, US entry could run in parallel with EU expansion (2026-2027) rather than waiting until Phase 3+ (2027+).

### Impact on roadmap

| Without partner | With partner |
|---|---|
| USA is Phase 3+ (2027+) | USA runs in parallel with EU (2026-2027) |
| Must build awareness from zero | Partner provides instant distribution |
| Organic CAC in a noisy market | Partner absorbs CAC through existing relationships |
| Need to hire US-based support | Partner handles first-line support and onboarding |
| Compete against established US brands alone | Partner's credibility opens doors |

### Risks specific to this model

- **Partner dependency** — If the fund underperforms or pivots, the US channel dries up
- **Conflicting priorities** — Fund may push features for large defense contractors (100+ employees) over SMB focus
- **Exclusivity lock-in** — If exclusivity is too broad, it blocks other US opportunities (HIPAA, SOC 2, commercial)
- **Cultural mismatch** — US defense sector has specific UX and compliance expectations (FedRAMP, ITAR) that may require dedicated engineering effort
- **Distraction** — Running US + EU simultaneously could stretch a 1-person company thin, even with AI agents

---

## Key Risks

- **Regulatory fragmentation** — the message "comply with X from day 1" requires different X for each audience segment, making marketing less efficient than in the EU
- **MSP channel competition** — ConnectWise, Kaseya, and NinjaOne could add compliance features and block the SMB channel through their MSP relationships
- **Higher CAC** — the US SaaS market is noisier; organic channels may not be sufficient
- **Support expectations** — US B2B buyers expect faster support (chat, phone) than EU buyers; this conflicts with the AI-managed company model
- **Data residency** — US government contractors may require US-hosted infrastructure (no EU servers)
- **Snipe-IT adds incidents** — Snipe-IT has strong US community presence; if they add a proper incident module, the open source angle weakens significantly in the US market

---

## Sources

- DoD CMMC 2.0 Final Rule (2024)
- HHS HIPAA Enforcement Data
- SEC Final Rule: Cybersecurity Risk Management (2023)
- CISA CIRCIA rulemaking documentation
- G2 Grid Reports: ITSM, ITAM (2025)
- Gartner Magic Quadrant: ITSM (2025)
- r/sysadmin, r/msp community discussions
- ConnectWise, Kaseya, NinjaOne public pricing and feature pages
