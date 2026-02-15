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

## Requirement Types & Folder Structure

```
ai_docs/
├── epics/           # Large initiatives with full business justification
├── features/        # Features linked to epics (can reference parent epic)
├── hotfixes/        # Urgent fixes for production issues
└── cases/           # Incident analysis (investigation, NOT implementation)
```

Each type has different requirements and workflows:

| Type | Purpose | Business Justification | Full Analysis | Implementation |
|------|---------|----------------------|---------------|----------------|
| **Epic** | Large initiative | MANDATORY (full) | MANDATORY | Yes |
| **Feature** | Part of an epic | Reference to epic | Simplified | Yes |
| **Hotfix** | Fix production issue | Problem-focused | Minimal | Yes |
| **Case** | Analyze incident | N/A | Investigation only | NO |

---

## 1. EPICS (`ai_docs/epics/`)

### Purpose
Large business initiatives that justify investment. Epics contain the full business case.

### Required Content (ALL MANDATORY)
- Business Alignment (objectives, KPIs, evidence)
- Full context and problem statement
- Complete use case analysis
- Entity states and transitions
- Slicing strategy
- Time constraints
- Testing requirements
- Definition of Done

### Workflow
```
Epic Requirement -> Full Validation -> Design -> Tasks -> Implementation
```

---

## 2. FEATURES (`ai_docs/features/`)

### Purpose
Individual features that are part of an epic. Can reference the parent epic instead of duplicating information.

### Required Content
- **Reference to parent epic** (MANDATORY)
- Feature-specific requirements
- Feature-specific acceptance criteria

### Workflow
```
Feature Requirement -> Simplified Validation -> Design -> Tasks -> Implementation
```

---

## 3. HOTFIXES (`ai_docs/hotfixes/`)

### Purpose
Urgent fixes for production issues. Focus on solving the problem, not business justification.

### Required Content
- **Problem description** (MANDATORY)
- **Impact** (who is affected, severity)
- **Root cause** (if known)
- **Proposed solution**
- **Testing to verify fix**
- **Rollback plan**

### Workflow
```
Problem Report -> Quick Analysis -> Fix -> Test -> Deploy
```

---

## 4. CASES (`ai_docs/cases/`)

### Purpose
**INVESTIGATION ONLY** - Analyze incidents to understand what happened. NOT for implementing solutions.

### Workflow
```
Incident Report -> Investigation -> Root Cause Analysis -> Recommendations
                                                              |
                            (If fix needed) -> Create Hotfix or Feature
```

---

## Progress Tracking (MANDATORY)

**After completing ANY feature or epic, ALWAYS update:**

1. **Slicing Documents** - Mark features as complete in status table
2. **Task Documents** - Check off completed acceptance criteria

**NEVER skip progress tracking. The user needs visibility into what's done.**
