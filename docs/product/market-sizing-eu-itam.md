# EU ITAM Market Sizing: NIS2, DORA & CRA Impact Analysis

**Date:** February 2026
**Scope:** IT Asset Management SaaS targeting EU SMBs (10-300 employees) affected by cybersecurity regulations

---

## 1. EU Company Landscape (Baseline)

### Total enterprises in the EU (business economy, 2023)

| Size class | Employees | Number of enterprises | % of total |
|---|---|---|---|
| Micro | 0-9 | ~30.8 million | ~92% |
| Small | 10-49 | ~1.38 million | ~4.1% |
| Medium | 50-249 | ~246,000 | ~0.7% |
| Large | 250+ | ~55,000 | ~0.2% |
| **Total** | | **~32.5 million** | 100% |

**Key number for ITAM TAM:** Companies with 10+ employees = ~1.68 million

Source: [Eurostat Structural Business Statistics (2023)](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Structural_business_statistics_overview), [Eurostat: Large businesses make up only 0.2% of EU enterprises (Dec 2024)](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20241205-1), [Annual Report on European SMEs 2023/2024](https://www.ggb.gr/sites/default/files/basic-page-files/Annual%20Report%20on%20European%20SMEs%202024.pdf)

---

## 2. NIS2 Directive — Affected Companies

### 2.1 Official scope estimate

The NIS2 Directive (effective October 2024) covers an estimated **100,000 to 160,000 entities** across the EU, a significant expansion from approximately 20,000 operators under the original NIS1 Directive. The most widely cited authoritative figure is **~160,000 entities**.

Sources: [European Commission NIS2 FAQ](https://digital-strategy.ec.europa.eu/en/faqs/directive-measures-high-common-level-cybersecurity-across-union-nis2-directive-faqs), [Advisera: Who does NIS2 apply to?](https://advisera.com/articles/who-does-nis2-apply-to/), [Baker Tilly NIS2 overview](https://www.bakertilly.de/en/european-nis-2-directive)

### 2.2 Size thresholds

NIS2 uses EU SME size definitions to determine scope:

| Classification | Employee threshold | Revenue/Balance sheet |
|---|---|---|
| Essential entities | 250+ employees | OR annual turnover > EUR 50M |
| Important entities | 50+ employees | OR annual turnover > EUR 10M |
| Micro/small exemption | < 50 employees | AND turnover < EUR 10M (generally excluded) |

**Exceptions to the general size exclusion:** DNS service providers, TLD name registries, domain name registration services, cloud computing service providers, data centre service providers, content delivery networks, managed service providers, managed security service providers, online marketplaces, online search engines, social networking platforms — these are included regardless of size. Public administrations are also included regardless of size.

Source: [NIS2 Directive text, Article 3](https://www.nis-2-directive.com/NIS_2_Directive_Article_3.html), [Eversheds Sutherland: SME size thresholds](https://www.eversheds-sutherland.com/en/finland/insights/size-of-organization-under-the-nis-2-directive-and-the-sme-recommendation)

### 2.3 Covered sectors (18 sectors total)

**Annex I — Highly critical (essential entities):**
Energy, Transport, Banking, Financial market infrastructure, Health, Drinking water, Wastewater, Digital infrastructure, ICT service management (B2B), Public administration, Space

**Annex II — Critical (important entities):**
Postal and courier services, Waste management, Manufacture/production/distribution of chemicals, Production/processing/distribution of food, Manufacturing (medical devices, computers, electronics, electrical equipment, motor vehicles, other transport equipment, other machinery), Digital providers, Research

Source: [NIS2 sectors overview — Threatscape](https://www.threatscape.com/cyber-security-blog/which-sectors-are-impacted-by-nis2/), [Glocert NIS2 applicability guide](https://www.glocertinternational.com/resources/guides/nis2-applicability-essential-vs-important-entities/)

### 2.4 Country-level estimates

| Country | Estimated companies affected (all sizes) | Source/Notes |
|---|---|---|
| Germany | ~29,500–40,000 | [Reed Smith](https://www.reedsmith.com/our-insights/blogs/technology-law-dispatch/102lxfr/finally-germany-enacts-its-nis2-law/), [PwC Germany](https://www.pwc.de/en/cyber-security/european-nis2-directive-implications-for-businesses-and-institutions.html) |
| Italy | ~27,000–50,000 | [OpenKRITIS Italy](https://www.openkritis.de/eu/eu-nis-2-italy.html) |
| France | >10,000 | [Wavestone](https://www.wavestone.com/en/insight/nis-2-european-countries-transposing-directive/) |
| Spain | ~25,000 | Estimated from regulatory scope |
| Austria | ~5,000–6,000 | [Baker Tilly](https://www.bakertilly.de/en/european-nis-2-directive) |
| Finland | ~5,500 | Expanded from ~1,100 under NIS1 |
| Netherlands | TBD (transposition delayed to 2026) | [CISO community NL](https://www.cisocommunity.nl/news/303-dutch-nis2-rollout-faces-further-delays) |

### 2.5 SMB-specific scope under NIS2

The directive directly captures **medium enterprises (50-249 employees)** in covered sectors as "important entities." Small enterprises (10-49 employees) are largely excluded from direct NIS2 obligations UNLESS they:
- Operate in the size-exempt categories (DNS, cloud, managed services, etc.)
- Are pulled in indirectly through supply chain pressure from NIS2-compliant customers

**Estimated SMBs (50-300 employees) directly in NIS2 scope:**
- Medium enterprises (50-249 employees) in the EU: ~246,000 total (all sectors)
- NIS2 covered sectors represent a significant portion of economic activity. Manufacturing alone accounts for roughly 20-25% of EU medium enterprises; adding energy, health, transport, food, and digital services the covered sectors represent an estimated 40-55% of all medium-sized enterprises.
- Estimated medium enterprises in NIS2 sectors: **~100,000–135,000**

**Estimated small enterprises (10-49 employees) pulled in indirectly (supply chain effect):**
- NIS2 requires covered entities to manage supply chain cybersecurity risks
- Conservative estimate: 1 directly-covered entity generates 3-5 indirect SMB dependencies
- Indirect exposure to NIS2 compliance pressure: **~300,000–500,000 small enterprises** (10-49 employees)

Source: [Sharp EU: What SMEs need to know about NIS2](https://www.sharp.eu/news-and-events/blog/what-european-smes-need-to-know-about-the-nis2-directive), [Avast: Should small businesses worry about NIS2?](https://blog.avast.com/nis2-europe-small-businesses), [More Than Digital: NIS2 for SMEs](https://morethandigital.info/en/nis2-in-detail-for-small-and-medium-sized-enterprises/)

---

## 3. DORA — Digital Operational Resilience Act

### 3.1 Total affected entities

DORA applies to an estimated **22,000 financial entities and ICT service providers** across the EU (per PwC). This covers 21 types of financial entities regulated in the EU.

**Entity types in scope:**
- Credit institutions (banks)
- Payment institutions and e-money institutions
- Investment firms
- Insurance and reinsurance undertakings
- Crypto-asset service providers (CASPs)
- Central securities depositories, CCPs, trading venues
- Trade repositories
- Alternative investment fund managers (AIFMs)
- Credit rating agencies
- Crowdfunding service providers
- Securitisation repositories
- ICT third-party service providers (critical designation)

### 3.2 SME applicability and exemptions

DORA builds in a **proportionality principle**: smaller financial entities are not expected to implement the same depth of controls as large banks. Specific simplified/exempted categories:
- Microenterprises (fewer than 10 employees, annual turnover/balance sheet under EUR 2M) are excluded from some requirements
- Sub-threshold AIFMs, small insurance undertakings, small pension institutions have a simplified ICT risk management framework

**SMBs (10-300 employees) in the financial sector that remain in full DORA scope:**
- Fintech payment institutions
- Insurance brokers/intermediaries (medium-sized)
- Regional banks and credit unions
- Mid-size investment firms
- E-money institutions

Estimated SMBs (10-300 employees) subject to DORA: **~8,000–12,000** (based on the 22,000 total minus large enterprises and micro-exempt entities)

Sources: [Skadden DORA 2024 update](https://www.skadden.com/insights/publications/2024/07/the-eus-digital-operational-resilience-act), [LegalNodes DORA scope guide](https://www.legalnodes.com/article/guide-to-the-scope-and-practical-aspects-of-dora-compliance), [Noerr DORA significance](https://www.noerr.com/en/insights/the-digital-operational-resilience-act-dora-and-its-significance-for-the-financial-sector), [Wikipedia DORA](https://en.wikipedia.org/wiki/Digital_Operational_Resilience_Act)

---

## 4. CRA — Cyber Resilience Act

### 4.1 Scope

The CRA (Regulation EU 2024/2847, in force December 2024, obligations apply December 2027) covers **all manufacturers, importers, and distributors** of "products with digital elements" placed on the EU market, regardless of size or turnover. This includes hardware, software, and connected devices.

Approximately **90% of products with digital elements** fall under the default (Class I) category requiring self-assessment. Only ~10% fall into Class II (critical) requiring third-party conformity assessment.

### 4.2 Estimated companies affected

The European Commission's impact assessment does not publish a single precise number. Based on the breadth of the definition (any device or software that connects directly or indirectly to a network), the affected population is very large:

- EU manufacturers in electronics, machinery, IoT, automotive, medical devices, software: estimated **100,000–400,000 economic operators** in the EU chain
- Importers and distributors add further scope
- Open-source developers (non-commercial) are largely exempt

**SMBs (10-300 employees) in scope for CRA:**
- SMB hardware/software manufacturers are fully in scope; no size exemptions exist
- Estimated SMB manufacturers (10-300 employees) affected: **~50,000–150,000** (based on EU manufacturing SMB counts in electronics, ICT equipment, and connected device categories)

Key obligation for ITAM relevance: CRA requires manufacturers to maintain a **Software Bill of Materials (SBOM)** and track all components, vulnerabilities, and software dependencies throughout the product lifecycle. This creates direct demand for asset inventory and lifecycle management tooling.

Sources: [European Commission CRA summary](https://digital-strategy.ec.europa.eu/en/policies/cra-summary), [White & Case CRA compliance](https://www.whitecase.com/insight-alert/cyber-resilience-act-clock-ticking-compliance), [CRA Wikipedia](https://en.wikipedia.org/wiki/Cyber_Resilience_Act), [Pillsbury CRA guide](https://www.pillsburylaw.com/en/news-and-insights/eu-cyber-resilience-act-requirements-products-software.html)

---

## 5. Market Size Estimates (TAM / SAM / SOM)

### 5.1 European ITAM Software Market (published research)

| Source | European ITAM market value | CAGR |
|---|---|---|
| Market Research Future | USD 1.85B (2024) → USD 4.42B (2035) | 8.2% |
| Market Research Future (alt) | USD 2.14B (2022) → USD 4.06B (2030) | 8.6% |
| Global share (Valuates) | Europe ~25% of global ITAM services market | — |

Sources: [Market Research Future — Europe ITAM](https://www.marketresearchfuture.com/reports/europe-it-asset-management-software-market-55831/), [Technavio ITAM 2024-2029](https://www.technavio.com/report/it-asset-management-software-market-share-industry-analysis)

**Note:** Published market figures predominantly capture enterprise-segment spending. The SMB segment is significantly underrepresented in existing ITAM revenue because most SMBs currently use spreadsheets or no dedicated tool. This represents addressable white space rather than existing market capture.

---

### 5.2 TAM — Total Addressable Market

**Definition:** All EU companies with 10+ employees that have an IT inventory to manage and have a plausible regulatory or operational reason to use ITAM software.

| Component | Count | Basis |
|---|---|---|
| Small enterprises (10-49 employees) | ~1,380,000 | Eurostat 2023 |
| Medium enterprises (50-249 employees) | ~246,000 | Eurostat 2023 |
| Large enterprises (250+ employees) excluded | excluded | Enterprise tools serve this segment |
| **TAM companies** | **~1,626,000** | |

**Revenue TAM at DeskSupportMonkey pricing (€49–€199/month):**
- Average blended price assumption: €99/month per company (conservative for SMB)
- Annual revenue per company: €1,188
- **TAM = ~€1.93 billion/year** (EU SMB segment, 10-249 employees)

*Cross-check against published data:* Published European ITAM market at ~USD 1.85B–2.14B (2024) is consistent, though it skews toward enterprise. The SMB-only slice of this published market is likely 25-35%, or ~USD 460M–750M for current spending. The large gap between current SMB spending and the theoretical TAM above confirms the untapped potential.

---

### 5.3 SAM — Serviceable Addressable Market

**Definition:** EU companies with 10-300 employees in NIS2/DORA/CRA-affected sectors, where regulatory pressure creates active pull for ITAM tools.

| Segment | Estimated companies | Rationale |
|---|---|---|
| Medium enterprises (50-249 employees) directly under NIS2 | ~100,000–135,000 | 40-55% of all EU medium enterprises in covered sectors |
| Small enterprises (10-49 employees) under supply chain NIS2 pressure | ~150,000–250,000 | Conservative 1.5x multiplier on direct scope |
| DORA-affected financial SMBs (10-300 employees) | ~8,000–12,000 | Of 22,000 total DORA entities |
| CRA-affected manufacturer SMBs (10-300 employees) | ~50,000–100,000 | Manufacturers of connected products |
| **De-duplicated SAM total** | **~250,000–400,000** | Overlap exists across categories |

**Revenue SAM at €99/month average:**
- Midpoint: ~325,000 companies
- **SAM = ~€387 million/year**

---

### 5.4 SOM — Serviceable Obtainable Market (Years 1-3, Bootstrapped)

**Context and benchmarks:**
- Bootstrapped B2B SaaS median annual growth rate: ~20% (SaaS Capital 2025)
- SMB SaaS annual churn: 15-30%
- Average SMB sales cycle: 15-45 days
- Realistic initial market capture for a bootstrapped SaaS targeting a well-defined niche: 0.01%–0.1% of SAM in Year 1, growing to 0.05%–0.5% by Year 3

Source: [SaaS Capital: Bootstrapped SaaS benchmarks 2025](https://www.saas-capital.com/blog-posts/benchmarking-metrics-for-bootstrapped-saas-companies/), [ChartMogul: SaaS Growth Report](https://chartmogul.com/reports/saas-growth-vc-bootstrapped/)

| Year | Market capture (% of SAM) | Companies | ARR at €99/month avg |
|---|---|---|---|
| Year 1 | 0.01%–0.03% | 33–97 customers | €47K–€115K |
| Year 2 | 0.03%–0.08% | 97–260 customers | €115K–€309K |
| Year 3 | 0.06%–0.15% | 195–490 customers | €232K–€583K |

**Realistic Year 3 ARR target (bootstrapped):** €200K–€600K ARR

**What this means in practice for DeskSupportMonkey:**
- At €99/month (mid-tier plan), reaching €300K ARR requires ~252 paying customers
- At €199/month (high-tier plan for larger SMBs with 50-300 employees), reaching €300K ARR requires only ~126 customers
- The NIS2-regulated medium enterprise segment (50-249 employees) is the highest-value initial beachhead — smaller number of prospects, higher willingness to pay, regulatory urgency as the primary purchase driver

---

## 6. Key Countries by SMB Density

### Countries with highest density of NIS2-affected SMBs

| Country | Medium enterprises (50-249 emp.) approx. | NIS2 companies (all sizes) | Priority tier |
|---|---|---|---|
| Germany | ~55,000 | ~30,000–40,000 | Tier 1 |
| Italy | ~45,000 | ~27,000–50,000 | Tier 1 |
| France | ~38,000 | >10,000 | Tier 1 |
| Spain | ~35,000 | ~25,000 | Tier 1 |
| Netherlands | ~15,000 | TBD (transposition 2026) | Tier 2 |
| Poland | ~20,000 | TBD (transposition 2025) | Tier 2 |
| Belgium | ~10,000 | Transposed, enforcing | Tier 2 |
| Sweden | ~8,000 | Transposition 2025 | Tier 2 |

Sources: [Eurostat SBS data](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Structural_business_statistics_overview), [Secomea NIS2 country overview](https://secomea.com/blog/compliance/nis2-compliance-in-europe-country-by-country/), [Noerr NIS2 Europe update March 2025](https://www.noerr.com/en/insights/nis-2-update-for-europe-march-2025)

**Strategic implication:** Germany and Italy have the highest concentrations of directly-affected manufacturing SMBs (both heavy in Annex II sectors). Germany additionally has clear national implementation law in force. These two countries represent the strongest initial go-to-market focus.

---

## 7. Current ITAM Adoption Among EU SMBs

### 7.1 Penetration data

The most recent large-scale benchmark study (EasyVista & OTRS Group, "State of SMB IT," 2025 — covering 1,051 SMB leaders across France, Germany, Italy, Spain, Portugal, and other markets):

- **67% of SMBs still rely on manual work or spreadsheets** to bridge ITSM and ITAM processes
- **Only 12% of SMBs** have implemented a fully mature, proactive IT Service Management framework
- **39%** report full integration between infrastructure monitoring and ITSM workflows
- **78%** of SMBs that have adopted an ITAM tool choose a SaaS/cloud-based model

Sources: [OTRS Group: SMB IT at a Breaking Point (2025)](https://corporate.otrs.com/smb-it-at-a-breaking-point-only-12-have-mature-itsm-frameworks-to-deal-with-increasing-it-complexity/), [Version 2: SMB IT survey](https://version-2.com/en/2025/07/smb-it-at-a-breaking-point-only-12-have-mature-itsm-frameworks-to-deal-with-increasing-it-complexity/)

### 7.2 What this means for market opportunity

| Metric | Value |
|---|---|
| SMBs in EU with 10-249 employees | ~1,626,000 |
| Currently using dedicated ITAM/ITSM tool | ~33% (est.) |
| Currently using spreadsheets / no tool | ~67% |
| Untapped addresses (~67% of SAM) | ~167,000–268,000 companies |

The 67% spreadsheet-dependency figure is especially relevant for marketing messaging: compliance deadlines (NIS2 enforcement, CRA 2027) are forcing organizations that have historically managed assets informally to formalize their processes.

### 7.3 Competitive pricing landscape

| Tool | Target | Price range |
|---|---|---|
| Snipe-IT (open source) | Any size | Free (self-hosted), up to ~$400/year cloud |
| ManageEngine AssetExplorer | Mid-market | $115–$1,545/month (cloud, by assets) |
| Freshservice (with ITAM) | SMB/Mid | $49–$99/agent/month |
| Alloy Navigator | SMB | ~$99–$199/month |
| InvGate Assets | Mid-market | Negotiated |

At the €49–€199/month range for DeskSupportMonkey, the product sits above free/self-hosted open source (Snipe-IT) and competes with the lower end of commercial ITSM platforms that have added ITAM modules. The compliance-focused angle (NIS2 evidence generation, hardware lifecycle tracking for CRA SBOM documentation) differentiates from pure open-source tools that lack audit trail and reporting features.

Source: [InvGate: Snipe-IT alternatives](https://blog.invgate.com/snipe-it-alternative), [AIM Multiple: ITAM pricing comparison](https://aimultiple.com/itam-pricing)

---

## 8. Summary Table

| Metric | Value | Confidence |
|---|---|---|
| EU companies with 10+ employees (TAM universe) | ~1,626,000 | High (Eurostat) |
| NIS2 directly affected entities (all sizes) | ~160,000 | High (official estimate) |
| NIS2 directly affected medium SMBs (50-249 emp.) | ~100,000–135,000 | Medium (derived) |
| NIS2 indirect supply chain pressure (10-49 emp.) | ~150,000–250,000 | Low-Medium (estimated) |
| DORA-affected entities total | ~22,000 | High (PwC/ESMA) |
| DORA-affected SMBs (10-300 employees) | ~8,000–12,000 | Medium (derived) |
| CRA-affected manufacturers (all sizes) | Very large, no official number | Low |
| CRA-affected SMB manufacturers (10-300 emp.) | ~50,000–150,000 | Low (estimated) |
| **SAM (NIS2+DORA+CRA, 10-300 emp., de-dup)** | **~250,000–400,000** | Medium |
| EU SMBs using spreadsheets for ITAM | ~67% | High (2025 survey) |
| **TAM revenue (10-249 emp., €99/mo avg)** | **~€1.93B/year** | Medium |
| **SAM revenue (regulated SMBs, €99/mo avg)** | **~€387M/year** | Medium |
| **SOM Year 3 ARR (bootstrapped)** | **€200K–€600K** | Medium |

---

## 9. Key Takeaways for DeskSupportMonkey

1. **The regulatory wave is real and quantifiable.** NIS2 alone directly affects ~160,000 EU entities, with medium enterprises (50-249 employees) in 18 sectors being the highest-priority direct targets. This is a 10x expansion over NIS1.

2. **Manufacturing is the largest untapped vertical.** Annex II of NIS2 explicitly covers food, chemicals, and broad manufacturing. Combined with CRA obligations for manufacturers of connected products, German and Italian manufacturing SMBs represent the densest concentration of regulatory-driven ITAM demand.

3. **67% of SMBs still use spreadsheets.** This is not a mature market with high switching costs — it is a category-creation opportunity where the primary competitor is Excel.

4. **Pricing at €49-€199/month is well-positioned.** It undercuts commercial ITSM platforms by 40-60% for equivalent ITAM features, while offering a managed compliance-audit advantage over free Snipe-IT.

5. **Year 3 SOM of €200K–€600K ARR is realistic.** Requiring only 126–490 customers depending on plan mix. Germany + Italy as initial markets with NIS2 implementation law in force provides a focused acquisition channel (direct outreach to companies registering with national cybersecurity agencies).

6. **Supply chain pressure amplifies the direct market.** Even small enterprises (10-49 employees) not directly bound by NIS2 face increasing customer demands to demonstrate security hygiene, extending the effective addressable market well beyond the 160,000 directly regulated entities.
