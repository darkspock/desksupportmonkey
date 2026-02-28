# Development Process

Single source of truth for how work flows from idea to production in DSM.

## Work Types

| Type | Purpose | Folder | Full Pipeline? |
|------|---------|--------|----------------|
| **Epic** | Large initiative with business justification | `docs/epics/{epic-name}/` | Yes (all phases) |
| **Feature** | Part of an epic, references parent | `docs/epics/{epic-name}/features/{feature-name}/` | Yes (simplified validation) |
| **Hotfix** | Urgent production fix | `docs/hotfixes/{name}/` | Abbreviated (problem → fix → test) |
| **Case** | Incident investigation (NO implementation) | `docs/cases/{name}/` | Investigation only |

## Output Locations

All artifacts live alongside the work they describe:

```
docs/epics/{epic}/
  requirements.md           <- Master / /requirement-write
  validation.md             <- Validator / /requirement-validate
  slicing.md                <- Slicer / /requirement-slice
  features/{feature}/
    requirements.md          <- Master (feature-level)
    design.md                <- Planner / /requirement-design
    tasks.md                 <- Planner / /requirement-tasks

docs/hotfixes/{name}/
  requirements.md
  tasks.md

docs/cases/{name}/
  requirements.md
  investigation.md
```

## Phase Pipeline

### Epic (full pipeline)

```
1. /requirement-write      -> docs/epics/{epic}/requirements.md
2. /requirement-validate   -> docs/epics/{epic}/validation.md
3. /requirement-slice      -> docs/epics/{epic}/slicing.md + features/ (OPTIONAL)
4. /requirement-design     -> docs/epics/{epic}/features/{feature}/design.md
5. /requirement-tasks      -> docs/epics/{epic}/features/{feature}/tasks.md
6. [IMPLEMENT]             -> Developer codes (backend + frontend)
7. /check-architecture     -> Verify architecture compliance
8. /check-quality          -> Review code quality
9. /check-performance      -> Identify performance issues
10. /linter                -> Static analysis (mypy + flake8)
11. /testing               -> Run and analyze tests
12. /check-dod             -> Final verification against acceptance criteria
```

### Feature (simplified)

Same as epic but starts at step 4 (design) since epic-level requirements already exist. Feature-level `requirements.md` is optional if the epic's slicing already defines scope.

### Hotfix (abbreviated)

```
1. Document problem        -> docs/hotfixes/{name}/requirements.md
2. /requirement-validate   -> Quick validation (hotfix mode)
3. [IMPLEMENT]             -> Developer fixes
4. /linter + /testing      -> Verify fix
5. /check-dod              -> Confirm fix meets criteria
```

### Case (investigation only)

```
1. Document incident       -> docs/cases/{name}/requirements.md
2. Investigate             -> docs/cases/{name}/investigation.md
3. Recommendations         -> Create Hotfix or Feature if fix needed
NO IMPLEMENTATION in cases.
```

## Two Session Modes

### Single-Session (Slash Commands)

Run slash commands within any Claude session. Best for:
- Quick iterations on a single feature
- Validation passes on existing code
- Small epics / hotfixes

All slash commands reference agent instruction files in `ai_docs/agents/` for their detailed logic.

### Multi-Session (ai/ Roles)

Launch separate Claude sessions per role. Best for:
- Large epics touching many bounded contexts
- When context window pressure is a concern
- Parallel backend + frontend implementation

```bash
cd ai/master   && claude    # Business Analyst
cd ai/planner  && claude    # Technical Architect
cd ai/worker-back && claude # Backend Developer
cd ai/worker-front && claude # Frontend Developer
```

Both modes produce artifacts in the same `docs/epics/` (or `docs/hotfixes/`, `docs/cases/`) locations.

## Unified Role Map

| Role | Slash Command | Multi-Session |
|------|---------------|---------------|
| Master (Business Analyst) | `/requirement-write` | `ai/master/` |
| Validator | `/requirement-validate` | any session |
| Slicer | `/requirement-slice` | any session |
| Planner (Technical Architect) | `/requirement-design`, `/requirement-tasks` | `ai/planner/` |
| Worker (Backend) | -- | `ai/worker-back/` |
| Worker (Frontend) | -- | `ai/worker-front/` |
| Reviewer | `/check-*`, `/linter`, `/testing` | any session |

## Progress Tracking (Mandatory)

After completing implementation, ALWAYS update:

1. **`docs/epics/{epic}/features/{feature}/tasks.md`** -- mark checkboxes `- [x]`
2. **`docs/epics/{epic}/slicing.md`** -- mark feature as "Done" in summary table
3. **`docs/product/roadmap.md`** -- mark epic as "Done" when all features complete

## Philosophy

**Analysis informs, never blocks.** Validation agents flag concerns and risks. The user always decides whether to proceed.
