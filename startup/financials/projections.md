# Financial Projections

**Date:** 2026-02-22
**Launch:** 2026-03-01
**Model:** Bootstrapped, no salary for 6 months (Mar–Aug 2026)
**Currency:** EUR

---

## Fixed Costs

| Concept | Monthly |
|---|---|
| AWS EC2 c6a.xlarge (production) | €110 |
| AWS RDS + S3 + staging | €40 |
| Claude Code | €100 |
| Stripe + email + misc | €10 |
| **Total** | **€260/month** |

No salaries until Month 7 (September 2026) — all MRR goes to cash reserves.

---

## Pricing Mix Assumption

| Plan | Price | Mix |
|---|---|---|
| Starter | €49 | 50% |
| Growth | €99 | 35% |
| Scale | €199 | 15% |
| **Average revenue per customer** | **~€87** | |

---

## Growth Rate Assumptions

| Phase | Period | Growth driver | Monthly growth rate |
|---|---|---|---|
| Launch | Mar–Aug 2026 | Organic, social media, open source community | C: 20% / R: 30% / O: 40% |
| NIS2 acceleration | Sep–Dec 2026 | Companies start acting on NIS2 compliance | C: 30% / R: 45% / O: 60% |
| Compliance boom | 2027 | NIS2 + DORA + CRA enforcement pressure peaks | C: 40% / R: 60% / O: 80% |

**C** = Conservative · **R** = Realistic · **O** = Optimistic

---

## Year 1 — 2026 (March to December)

### Customers

| Month | C | R | O |
|---|---|---|---|
| Mar (launch) | 4 | 5 | 6 |
| Apr | 5 | 7 | 8 |
| May | 6 | 9 | 11 |
| Jun | 7 | 11 | 16 |
| Jul | 8 | 15 | 22 |
| Aug | 10 | 19 | 31 |
| Sep (NIS2 kicks in) | 13 | 28 | 50 |
| Oct | 17 | 40 | 80 |
| Nov | 22 | 58 | 128 |
| Dec | 29 | 85 | 205 |

### MRR (€)

| Month | C | R | O |
|---|---|---|---|
| Mar | €348 | €435 | €522 |
| Apr | €435 | €609 | €696 |
| May | €522 | €783 | €957 |
| Jun | €609 | €957 | €1,392 |
| Jul | €696 | €1,305 | €1,914 |
| Aug | €870 | €1,653 | €2,697 |
| Sep | €1,131 | €2,436 | €4,350 |
| Oct | €1,479 | €3,480 | €6,960 |
| Nov | €1,914 | €5,046 | €11,136 |
| Dec | €2,523 | €7,395 | €17,835 |

### Cashflow after fixed costs (€260/month)

| Month | C | R | O |
|---|---|---|---|
| Mar | -€188 | -€171 | +€262 |
| Apr | -€171 | +€349 | +€436 |
| May | -€146 | +€523 | +€697 |
| Jun | -€129 | +€697 | +€1,132 |
| Jul | -€116 | +€1,045 | +€1,654 |
| Aug | +€610 | +€1,393 | +€2,437 |
| Sep | +€871 | +€2,176 | +€4,090 |
| Oct | +€1,219 | +€3,220 | +€6,700 |
| Nov | +€1,654 | +€4,786 | +€10,876 |
| Dec | +€2,263 | +€7,135 | +€17,575 |

### Cumulative cash reserve (end of year)

| Scenario | Cash at Dec 2026 |
|---|---|
| Conservative | ~€5,500 |
| Realistic | ~€20,500 |
| Optimistic | ~€43,500 |

---

## Year 2 — 2027 (Compliance Boom)

NIS2 enforcement pressure peaks. DORA fully active in financial sector. CRA phasing in. Companies that have been ignoring compliance start acting. The ICP has a legal obligation — this is no longer a "nice to have."

### Customers (end of each quarter)

| Quarter | C | R | O |
|---|---|---|---|
| Q1 2027 | 55 | 180 | 500 |
| Q2 2027 | 110 | 400 | 1,200 |
| Q3 2027 | 200 | 800 | 2,500 |
| Q4 2027 | 350 | 1,500 | 5,000 |

### MRR (end of each quarter)

| Quarter | C | R | O |
|---|---|---|---|
| Q1 2027 | ~€4,800 | ~€15,600 | ~€43,500 |
| Q2 2027 | ~€9,600 | ~€34,800 | ~€104,400 |
| Q3 2027 | ~€17,400 | ~€69,600 | ~€217,500 |
| Q4 2027 | ~€30,450 | ~€130,500 | ~€435,000 |

### ARR at end of 2027

| Scenario | ARR |
|---|---|
| Conservative | ~€365,000 |
| Realistic | ~€1,566,000 |
| Optimistic | ~€5,220,000 |

---

## Hiring Triggers (based on MRR)

| Hire | MRR trigger | Est. month (Realistic) |
|---|---|---|
| Orchestrator starts drawing salary | €2,000 MRR | Sep 2026 |
| First human advisor retainer | €3,000 MRR | Oct 2026 |
| Head of Growth (if hiring) | €7,000 MRR | Nov 2026 |
| Senior Engineer (if hiring) | €12,000 MRR | Q1 2027 |

---

## Key Risks

- **NIS2 enforcement delays** — regulators may push back timelines; the boom could arrive later than Q4 2027
- **Churn in early months** — if beta users don't convert to paid, launch MRR could be lower than conservative
- **Competition** — larger players (Freshservice, Lansweeper) could add NIS2 compliance features and undercut the positioning
- **Pricing validation** — employee-based pricing is untested; first 10 customers will tell us if €99-199 is the right range
- **AWS costs** — production server (c6a.xlarge) runs ~€110/month; if traffic stays low, could downgrade to t3.medium (~€30) to cut costs

---

## Break-even Summary

| Scenario | Break-even month |
|---|---|
| Conservative | August 2026 (month 6) |
| Realistic | April 2026 (month 2) |
| Optimistic | March 2026 (month 1) |

In all scenarios, the business covers its own costs within 6 months — which is exactly the bootstrap constraint.
