# Working Documentation

## Philosophy: Analysis Informs, Never Blocks

**THE USER ALWAYS DECIDES.**

| Principle | Meaning |
|-----------|---------|
| Analysis is informative | Shows risks, gaps, impacts - does NOT block |
| User decides | If they say "proceed", we proceed |
| Not bureaucracy | Better definition helps, but never creates gates |
| Purpose | Help avoid repeating patterns, but as a tool, not a barrier |

**In practice:** Flag concerns -> Ask user -> Execute their decision

---

## Work Types

| Type | Purpose | Folder | Full Pipeline? |
|------|---------|--------|----------------|
| **Epic** | Large initiative with business justification | `docs/epics/{epic-name}/` | Yes (all phases) |
| **Feature** | Part of an epic, references parent | `docs/epics/{epic-name}/features/{feature-name}/` | Yes (simplified) |
| **Hotfix** | Urgent production fix | `docs/hotfixes/{name}/` | Abbreviated |
| **Case** | Incident investigation (NO implementation) | `docs/cases/{name}/` | Investigation only |

For the full development process (phases, output locations, session modes, role map), see **`ai_docs/development_process.md`**.

---

## Progress Tracking (MANDATORY)

**After completing ANY feature or epic, ALWAYS update:**

1. **Task Documents** -- Mark checkboxes as `- [x]` in `docs/epics/{epic}/features/{feature}/tasks.md`
2. **Slicing Documents** -- Mark features as complete in `docs/epics/{epic}/slicing.md`
3. **Roadmap** -- Mark epic as "Done" in `docs/product/roadmap.md` when all features complete

**NEVER skip progress tracking. The user needs visibility into what's done.**
