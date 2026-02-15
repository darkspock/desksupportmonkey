# Requirement Analysis Guide for AI

Instructions for AI to analyze and validate requirement documents for the DeskSupportMonkey platform.

**IMPORTANT**: This is NOT a strict template validation. AI must verify that the requirement contains the necessary **content**, regardless of the exact format or structure used.

---

## Philosophy: Analysis Informs, Never Blocks

**THE USER ALWAYS DECIDES.** This analysis framework is informative, not bureaucratic.

### Core Principles

1. **Analysis identifies risks and gaps - it does NOT block development**
2. **Better upfront definition helps, but never creates bureaucracy**
3. **Context matters** - Flag concerns, ask user, execute their decision

**NEVER say:** "Cannot proceed until X is defined"
**ALWAYS say:** "X is missing/risky. Do you want to proceed anyway or define it first?"

---

## STEP 0: Detect Requirement Type (FIRST)

| Path Contains | Type | Validation Mode |
|---------------|------|-----------------|
| `/epics/` | Epic | FULL validation |
| `/features/` | Feature | SIMPLIFIED (check epic reference) |
| `/hotfixes/` | Hotfix | PROBLEM-FOCUSED |
| `/cases/` | Case | INVESTIGATION ONLY |

---

## Step-by-Step Analysis Process

### Step 1: Identify Entities
- What is the main entity/resource being acted upon?
- Are there secondary entities involved?

### Step 2: Apply CRUD Check
For each entity, verify if ALL CRUD operations are addressed or explicitly excluded.

### Step 3: Apply Status & State Analysis (MANDATORY)
For EVERY entity, verify: initial status, all statuses, transitions, triggers, conditions, side effects, delete strategy.

#### DeskSupportMonkey Common Status Patterns

| Entity Type | Common Statuses |
|-------------|-----------------|
| Request | submitted, in_review, in_progress, resolved, rejected |
| Asset | in_stock, assigned, in_repair, decommissioned |
| Company | active, suspended, deactivated |
| User | active, deactivated |

### Step 4: Apply Use Case Pattern Detection
- CRUD Pattern (Create, Read, Update, Delete, List, Filter, Search, Export, Import)
- Lifecycle Pattern (stages, permissions, time-based transitions)
- State Machine Pattern (all transitions, invalid transitions blocked, audit)
- Bulk Operations Pattern
- Reporting Pattern
- Role-Based Access Pattern

### Step 5: Inverse Operation Check
For every action, verify its opposite (Add/Remove, Enable/Disable, Assign/Unassign, etc.)

### Step 6: User Journey Check
Preconditions, Postconditions, Error recovery, Undo/cancel

### Step 7: Collateral Impact Analysis (MANDATORY)
Entities, Data, Business Rules, Workflows, Reports, Permissions, Breaking Changes

### Step 8: Requirement Slicing Analysis
Size, Independence, Value, Dependencies, Out of Scope

### Step 9: Business Alignment Check (MANDATORY for Epics)
Objective, Contribution, KPIs, Evidence

### Step 10: Time Constraints Check
Deadline, Reason, Realistic, Buffer, Fallback

### Step 11: Testing Requirements Check
Test types, Critical scenarios, Test data, Regression

### Step 12: Definition of Done Check
Acceptance criteria, Quality gates, Sign-off

---

## Output: Analysis Checklist

After analysis, produce a checklist covering: Business Alignment, Entities & Operations, Use Cases, Impact, Constraints, Gaps Identified, and Questions for Stakeholder.
