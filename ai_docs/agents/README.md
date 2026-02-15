# AI Agents

This folder contains agent definitions for AI-assisted development workflow for the Metrica.uno platform.

## Overview

Agents are specialized AI assistants designed for specific tasks in the development process. Each agent has a focused responsibility and follows defined patterns to ensure consistency and quality.

## Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REQUIREMENTS PHASE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │ 1. Requirement   │───▶│ 2. Requirement   │───▶│ 2.5 Requirement  │     │
│  │    Writer        │    │    Validator     │    │     Slice        │     │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│         │                        │                       │                 │
│         ▼                        ▼                       ▼                 │
│  Create requirement        Validate              Slice epic into           │
│  document                  completeness          features (OPTIONAL)       │
│                                                          │                 │
│                                    ┌─────────────────────┤                 │
│                                    ▼                     ▼                 │
│                          ┌──────────────────┐  ┌──────────────────┐       │
│                          │ 3. Requirement   │  │ Per-feature:     │       │
│                          │    Design        │  │ Design → Tasks   │       │
│                          └──────────────────┘  └──────────────────┘       │
│                                    │                                       │
│                                    ▼                                       │
│                          ┌──────────────────┐                              │
│                          │ 4. Requirement   │                              │
│                          │    Make Tasks    │                              │
│                          └──────────────────┘                              │
│                                    │                                       │
│                                    ▼                                       │
│                          Create implementation                             │
│                          tasks                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           IMPLEMENTATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Developer implements tasks following /ai_docs/architecture/ guides         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            VALIDATION PHASE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │ 5. Check         │    │ 6. Check         │    │ 7. Check Code    │     │
│  │    DoD           │    │    Architecture  │    │    Quality       │     │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │ 8. Check         │    │ 9. Linter &      │    │ 10. Testing      │     │
│  │    Performance   │    │    Compile       │    │                  │     │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent List

### Requirements Phase

| # | Agent | Purpose | Input | Output |
|---|-------|---------|-------|--------|
| 1 | [Requirement Writer](1.%20requirement_writer.md) | Create requirement documents | Business need | Requirement doc |
| 2 | [Requirement Validator](2.%20requirement_validator.md) | Validate requirement completeness | Requirement doc | Validation report |
| 2.5 | [Requirement Slice](2.5.%20requirement_slice.md) | Slice epic into features (optional) | Validated epic | Features + dependency graph |
| 3 | [Requirement Design](3.%20requirement_design_solution.md) | Design technical solution | Validated requirement | Solution design |
| 4 | [Requirement Tasks](4.%20requirement_make_tasks.md) | Create implementation tasks | Solution design | Task list |

### Validation Phase

| # | Agent | Purpose | Input | Output |
|---|-------|---------|-------|--------|
| 5 | [Check DoD](5.%20check_definition_of_done.md) | Verify Definition of Done | Implementation | DoD report |
| 6 | [Check Architecture](6.%20check_architecture.md) | Verify architecture compliance | Code changes | Architecture report |
| 7 | [Check Code Quality](7.%20check_code_quality.md) | Review code quality | Code changes | Quality report |
| 8 | [Check Performance](8.%20check_performance.md) | Identify performance issues | Code changes | Performance report |
| 9 | [Linter & Compile](9.%20linter_compile.md) | Run static analysis | Code | Linter report |
| 10 | [Testing](10.%20testing.md) | Run and analyze tests | Code | Test report |

## Workflow by Work Type

### 1. New Epic

```
1. Requirement Writer      → Create requirement
2. Requirement Validator   → Validate (fix issues if any)
2.5. Requirement Slice     → Slice into features (OPTIONAL - for large epics)
     │
     ├─► If sliced: Each feature follows steps 3-11 independently
     │
3. Requirement Design      → Design solution
4. Requirement Tasks       → Create tasks
5. [IMPLEMENT]            → Developer codes
6. Linter & Compile       → Static analysis
7. Testing                → Run tests
8. Check Architecture     → Verify architecture
9. Check Code Quality     → Review quality
10. Check Performance     → Check performance
11. Check DoD             → Final verification
```

### 2. Feature (Part of Epic)

```
1. Requirement Writer (simplified) → Reference epic, feature-specific req
2. Requirement Validator (simplified) → Validate feature-specific
3. Requirement Design    → Design solution
4. Requirement Tasks     → Create tasks
5. [IMPLEMENT]          → Developer codes
6-11. [Validation agents]
```

### 3. Hotfix

```
1. Document problem      → Problem, impact, root cause
2. Requirement Validator (hotfix mode) → Validate problem definition
3. [IMPLEMENT]           → Developer fixes
4. Linter & Compile      → Static analysis
5. Testing               → Run tests
6. Check DoD             → Verify fix
```

### 4. Case (Investigation Only)

```
1. Document incident     → Timeline, findings
2. Requirement Validator (case mode) → Validate investigation
3. Recommendations       → Create Hotfix/Feature if needed
NO IMPLEMENTATION - cases are investigation only
```

## Agent Output Locations

All documents for one item are in ONE folder:

| Agent | Output Location |
|-------|-----------------|
| Requirement Writer | `/docs/working_docs/[type]/[name]/requirements.md` |
| Requirement Validator | `/docs/working_docs/[type]/[name]/validation.md` |
| Requirement Design | `/docs/working_docs/[type]/[name]/design.md` |
| Requirement Tasks | `/docs/working_docs/[type]/[name]/tasks.md` |
| Check * Agents | Report in conversation or `/docs/reviews/` |

**Example:** All content for "multi-framework-assessment" feature:
```
/docs/working_docs/features/multi-framework-assessment/
├── requirements.md
├── validation.md
├── design.md
└── tasks.md
```

## Key Principles

### 1. Analysis Informs, Never Blocks

Agents identify risks and issues but **never block** development. The user always decides whether to proceed.

```
✅ "X is missing/risky. Proceed anyway or define first?"
❌ "Cannot proceed until X is defined"
```

### 2. Value Over Code

The goal is to add business value, not to add code. Every requirement should tie to business objectives.

### 3. Architecture Compliance

All code must follow the project's Clean Architecture as defined in `/ai_docs/architecture/`.

### 4. Quality Gates

Validation agents ensure code meets quality standards before deployment.

## Metrica.uno-Specific Considerations

### Multi-Tenant Awareness

All agents must consider multi-tenancy:
- Organization isolation (`organization_id` on all queries)
- Plan-based feature access
- Data segregation

### Compliance Metamodel

When designing features that affect the metamodel:
- Universal domains (8) and subdomains (32)
- Universal questions (~150)
- Framework mappings and projections
- Impact on existing assessments

### Plan-Based Features

Always specify:
- Which plans have access (Free, Starter, Professional, Enterprise)
- What content is limited/gated
- Upgrade triggers

### Key Metrica.uno Entities

| Entity | Description |
|--------|-------------|
| Organization | Multi-tenant root (company) |
| AISystem | AI system being assessed |
| Assessment | Compliance evaluation |
| Framework | Regulatory standard (EU AI Act, etc.) |
| ComplianceDomain | Universal compliance area (8 total) |
| UniversalQuestion | Framework-agnostic question |
| Response | User answer to question |
| ComplianceGap | Identified non-compliance |
| RemediationTask | Action to fix gap |

## Claude Commands

| Command | Agent | Purpose |
|---------|-------|---------|
| `/requirement-write` | Agent 1 | Create requirement document |
| `/requirement-validate` | Agent 2 | Validate requirement |
| `/requirement-slice` | Agent 2.5 | Slice epic into features (optional) |
| `/requirement-design` | Agent 3 | Design technical solution |
| `/requirement-tasks` | Agent 4 | Create implementation tasks |
| `/check-dod` | Agent 5 | Verify definition of done |
| `/check-architecture` | Agent 6 | Check architecture compliance |
| `/check-quality` | Agent 7 | Check code quality |
| `/check-performance` | Agent 8 | Check performance issues |
| `/linter` | Agent 9 | Run linter/compile |
| `/testing` | Agent 10 | Run and analyze tests |

## Related Documentation

- `/ai_docs/architecture/` - Architecture guides
- `/docs/development/development_process.md` - Full development process
- `/docs/business/overview.md` - Business context (MANDATORY)
- `/docs/architecture/architecture-compliance-metamodel.md` - Compliance metamodel specification

## Tips for Using Agents

1. **Follow the order** - Requirements phase before implementation
2. **Don't skip validation** - Run all check agents before merge
3. **Iterate when needed** - If validation fails, fix and re-run
4. **Use appropriate agent** - Match agent to task type
5. **Provide context** - Give agents access to relevant documents
6. **Consider Metrica.uno specifics** - Multi-tenant, plans, metamodel
