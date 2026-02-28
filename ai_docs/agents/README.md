# AI Agents

Agent instruction files for the DSM development workflow. Each agent is invoked via a slash command and follows its instruction file for detailed logic.

For the full development process (phases, output locations, session modes), see **`ai_docs/development_process.md`**.

## Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REQUIREMENTS PHASE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │ 1. Requirement   │───>│ 2. Requirement   │───>│ 2.5 Requirement  │     │
│  │    Writer        │    │    Validator     │    │     Slice        │     │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│         │                        │                       │                 │
│         v                        v                       v                 │
│  Create requirement        Validate              Slice epic into           │
│  document                  completeness          features (OPTIONAL)       │
│                                                          │                 │
│                                    ┌─────────────────────┤                 │
│                                    v                     v                 │
│                          ┌──────────────────┐  ┌──────────────────┐       │
│                          │ 3. Requirement   │  │ Per-feature:     │       │
│                          │    Design        │  │ Design -> Tasks  │       │
│                          └──────────────────┘  └──────────────────┘       │
│                                    │                                       │
│                                    v                                       │
│                          ┌──────────────────┐                              │
│                          │ 4. Requirement   │                              │
│                          │    Make Tasks    │                              │
│                          └──────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           IMPLEMENTATION PHASE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Developer implements tasks following ai_docs/architecture/ guides          │
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

| # | Agent | Slash Command | Output Location |
|---|-------|---------------|-----------------|
| 1 | [Requirement Writer](1.%20requirement_writer.md) | `/requirement-write` | `docs/epics/{epic}/requirements.md` |
| 2 | [Requirement Validator](2.%20requirement_validator.md) | `/requirement-validate` | `docs/epics/{epic}/validation.md` |
| 2.5 | [Requirement Slice](2.5.%20requirement_slice.md) | `/requirement-slice` | `docs/epics/{epic}/slicing.md` + `features/` |
| 3 | [Requirement Design](3.%20requirement_design_solution.md) | `/requirement-design` | `docs/epics/{epic}/features/{feature}/design.md` |
| 4 | [Requirement Tasks](4.%20requirement_make_tasks.md) | `/requirement-tasks` | `docs/epics/{epic}/features/{feature}/tasks.md` |

### Validation Phase

| # | Agent | Slash Command | Input |
|---|-------|---------------|-------|
| 5 | [Check DoD](5.%20check_definition_of_done.md) | `/check-dod` | Implementation + tasks.md |
| 6 | [Check Architecture](6.%20check_architecture.md) | `/check-architecture` | Code changes |
| 7 | [Check Code Quality](7.%20check_code_quality.md) | `/check-quality` | Code changes |
| 8 | [Check Performance](8.%20check_performance.md) | `/check-performance` | Code changes |
| 9 | [Linter & Compile](9.%20linter_compile.md) | `/linter` | Code |
| 10 | [Testing](10.%20testing.md) | `/testing` | Code |

## Key Principles

### 1. Analysis Informs, Never Blocks

Agents identify risks and issues but **never block** development. The user always decides whether to proceed.

### 2. Value Over Code

The goal is to add business value, not to add code. Every requirement should tie to business objectives.

### 3. Architecture Compliance

All code must follow the project's Clean Architecture as defined in `ai_docs/architecture/`.

### 4. Multi-Tenant Awareness

All agents must consider multi-tenancy: company isolation (`company_id` on all queries), plan-based feature access, data segregation.

## Related Documentation

- `ai_docs/development_process.md` -- Full development process (single source of truth)
- `ai_docs/architecture/` -- Architecture guides
- `ai/README.md` -- Multi-session workflow (Master -> Planner -> Workers)
- `ai_docs/working_documentation.md` -- Philosophy and work types
