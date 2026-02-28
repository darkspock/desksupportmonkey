# Multi-Session AI Workflow

Split complex features into focused AI sessions: **Master** (business context) -> **Planner** (technical decomposition) -> **Workers** (implementation).

This is one of two session modes. For slash commands in a single session, see `ai_docs/agents/README.md`. Both modes share the same pipeline and output to `docs/epics/`. Full process: `ai_docs/development_process.md`.

## Why

Single-session development loads all architecture docs + business docs per session. As the project grows (50+ epics, 26 bounded contexts), this wastes context and slows down work. The multi-session workflow loads only what each role needs.

## Quick Start

### 1. Master Session (Business Analyst)

```bash
cd ai/master
claude
```

Tell the Master what you want to build. It reads `docs/business/INDEX.md` to find relevant business docs, then outputs a structured requirements document to `docs/epics/{epic}/requirements.md`.

### 2. Planner Session (Technical Architect)

```bash
cd ai/planner
claude
```

Point it to the requirements file in `docs/epics/`. It reads the relevant architecture docs, designs the solution (`design.md`), and decomposes it into a unified task list (`tasks.md`) -- all written to the same feature folder.

### 3. Worker Sessions (Developers)

```bash
# Backend
cd ai/worker-back
claude
# Point it to tasks in docs/epics/{epic}/features/{feature}/tasks.md

# Frontend
cd ai/worker-front
claude
# Point it to tasks in docs/epics/{epic}/features/{feature}/tasks.md
```

Workers implement one task at a time. All architecture rules are inline in their CLAUDE.md -- no external doc reads needed.

## Flow Diagram

```
User Request
    |
    v
┌──────────┐    reads docs/business/INDEX.md
│  Master   │──> finds relevant business docs
│ (Business │──> reads only those docs
│  Analyst) │──> outputs requirements document
└────┬─────┘
     │ docs/epics/{epic}/requirements.md
     v
┌──────────┐    reads architecture docs (selective)
│ Planner   │──> designs solution (design.md)
│ (Tech     │──> decomposes into tasks (tasks.md)
│ Architect)│──> writes to feature folder
└────┬─────┘
     │ docs/epics/{epic}/features/{feature}/tasks.md
     ├──────────────────┐
     v                  v
┌──────────┐     ┌──────────┐
│  Worker   │     │  Worker   │
│ (Backend) │     │(Frontend) │
│           │     │           │
│ All rules │     │ All rules │
│ inline    │     │ inline    │
└──────────┘     └──────────┘
     │                  │
     v                  v
  /check-*          /check-*
  /linter            /testing
  /check-dod        /check-dod
```

## Roles

| Role | Directory | What It Loads |
|------|-----------|---------------|
| Master | `ai/master/` | Business docs (selective via INDEX.md) |
| Planner | `ai/planner/` | Architecture docs (selective) |
| Worker (Back) | `ai/worker-back/` | Nothing external -- all rules inline |
| Worker (Front) | `ai/worker-front/` | Nothing external -- all rules inline |

## Relationship to Slash Commands

Both session modes execute the **same pipeline** with the **same output locations**:

| Unified Role | Slash Command | Multi-Session |
|---|---|---|
| Master | `/requirement-write` | `ai/master/` |
| Validator | `/requirement-validate` | any session |
| Slicer | `/requirement-slice` | any session |
| Planner | `/requirement-design`, `/requirement-tasks` | `ai/planner/` |
| Reviewer | `/check-*`, `/linter`, `/testing` | any session |

Validation slash commands (`/check-*`, `/linter`, `/testing`, `/check-dod`) can be run in any session -- including after worker sessions complete.

## Tips

- **One task per worker session.** Start fresh for each task to avoid context pollution.
- **Workers are self-contained.** Their CLAUDE.md has every rule they need.
- **Master only runs once per feature.** Its output is reusable across planning iterations.
- **Planner verifies paths exist.** It checks that file paths in tasks point to real files.
- **Architecture docs still exist.** They serve as detailed reference -- they're not deleted.
- **Validation agents work alongside.** Run `/check-architecture`, `/check-quality`, etc. after implementation.

## Directory Structure

```
ai/
├── README.md              <- You are here
├── master/
│   └── CLAUDE.md          <- Business Analyst instructions
├── planner/
│   └── CLAUDE.md          <- Technical Architect instructions
├── worker-back/
│   ├── CLAUDE.md          <- Backend Developer instructions (all rules inline)
│   └── tasks/             <- Legacy: copy task here for worker to pick up
└── worker-front/
    ├── CLAUDE.md          <- Frontend Developer instructions (all rules inline)
    └── tasks/             <- Legacy: copy task here for worker to pick up
```
