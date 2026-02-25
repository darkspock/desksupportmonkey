# Implementation Tasks: Feature 3 — Queue & Icons

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-25
**Total Tasks:** 7
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Setup - Install lucide-react | 1 | XS |
| Component - WorkflowIcon | 1 | S |
| Types - ServiceRequest update | 1 | XS |
| Pages - NewRequestPage cleanup | 1 | S |
| Pages - RequestDetailPage cleanup | 1 | S |
| Pages - RequestQueuePage icons | 1 | M |
| Pages - WorkflowTemplatesPage icons | 1 | XS |

---

## Phase 1: Setup

### TASK-001: Install lucide-react

**Phase:** Setup
**Complexity:** XS
**Dependencies:** None

**Implementation:**
```bash
cd web/app && npm install lucide-react
```

**Acceptance Criteria:**
- [x] lucide-react in package.json dependencies
- [x] npm install succeeds
- [x] TypeScript recognizes lucide-react imports

---

## Phase 2: Shared Component

### TASK-002: Create WorkflowIcon Component

**Phase:** Component
**Complexity:** S
**Dependencies:** TASK-001

**File:** `web/app/src/components/ui/WorkflowIcon.tsx` (NEW)

**Implementation:**
Create a component that takes a lucide icon name string (kebab-case, e.g. "alert-circle") and renders the corresponding lucide-react component. Convert kebab-case to PascalCase for the `icons` lookup. Return null for unknown/missing names.

Props: `name?: string | null` + all standard lucide SVG props (className, size, etc.)

**Acceptance Criteria:**
- [x] Renders correct icon for known names ("alert-circle", "monitor", "wrench", etc.)
- [x] Returns null for null/undefined/unknown names
- [x] Accepts className, size, and other SVG props
- [x] TypeScript compiles clean

---

## Phase 3: Type Updates

### TASK-003: Add Template Fields to ServiceRequest TypeScript Type

**Phase:** Types
**Complexity:** XS
**Dependencies:** None

**File:** `web/app/src/types/index.ts`

**Implementation:**
Add to the ServiceRequest interface:
```typescript
workflow_template_name?: string | null;
workflow_template_icon?: string | null;
```

These fields are already returned by the backend (added in F1 to RequestListItemResponse and RequestResponse schemas).

**Acceptance Criteria:**
- [x] Fields added to ServiceRequest type
- [x] Optional with null union
- [x] TypeScript compiles clean

---

## Phase 4: Page Updates

### TASK-004: Replace NewRequestPage Inline SVGs with WorkflowIcon

**Phase:** Pages
**Complexity:** S
**Dependencies:** TASK-002

**File:** `web/app/src/pages/employee/NewRequestPage.tsx`

**Implementation:**
- Remove the entire `ICON_MAP` constant (lines 21-58)
- Remove the `TemplateIcon` function component (lines 60-69)
- Import `WorkflowIcon` from `../../components/ui/WorkflowIcon`
- Replace `<TemplateIcon name={tmpl.icon} />` with `<WorkflowIcon name={tmpl.icon} className="h-5 w-5" />`
- Keep the fallback behavior: WorkflowIcon returns null for unknown icons, which is fine since the 10x10 colored container still shows

**Acceptance Criteria:**
- [x] ICON_MAP removed
- [x] TemplateIcon removed
- [x] WorkflowIcon used for template cards
- [x] Icons render correctly for all 6 template types
- [x] TypeScript compiles clean

---

### TASK-005: Replace RequestDetailPage Inline SVGs with WorkflowIcon

**Phase:** Pages
**Complexity:** S
**Dependencies:** TASK-002, TASK-003

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation:**
- Remove the `TYPE_ICONS` map
- Import `WorkflowIcon`
- Use `request.workflow_template_icon` to render icon:
  ```tsx
  <WorkflowIcon name={request.workflow_template_icon} className="h-6 w-6" />
  ```
- For old requests without template icon, show a generic fallback (e.g. a `ClipboardList` icon from lucide-react)

**Acceptance Criteria:**
- [x] TYPE_ICONS map removed
- [x] WorkflowIcon used with template icon from response data
- [x] Fallback for requests without template icon
- [x] TypeScript compiles clean

---

### TASK-006: Add Template Name/Icon to RequestQueuePage

**Phase:** Pages
**Complexity:** M
**Dependencies:** TASK-002, TASK-003

**File:** `web/app/src/pages/technician/RequestQueuePage.tsx`

**Implementation:**

**Table view:**
- In the type column, add icon before text:
  ```tsx
  <div className="flex items-center gap-1.5">
    <WorkflowIcon name={r.workflow_template_icon} className="h-4 w-4 text-muted-foreground" />
    <span className="text-sm text-muted-foreground">
      {r.workflow_template_name || t(`enum.${r.type}`)}
    </span>
  </div>
  ```
- Show `workflow_template_name` when available, fall back to `t('enum.${r.type}')` for old requests

**Kanban view:**
- Add a small type indicator with icon to kanban cards (below priority/status badges or near the title)

**Acceptance Criteria:**
- [x] Table view shows icon + template name
- [x] Falls back to translated enum for old requests
- [x] Kanban cards show type indicator
- [x] TypeScript compiles clean

---

### TASK-007: Render Actual Icons in WorkflowTemplatesPage

**Phase:** Pages
**Complexity:** XS
**Dependencies:** TASK-002

**File:** `web/app/src/pages/admin/WorkflowTemplatesPage.tsx`

**Implementation:**
- Import `WorkflowIcon`
- Replace the text badge in the table with:
  ```tsx
  <WorkflowIcon name={tmpl.icon} className="h-4 w-4 text-muted-foreground" />
  ```
- Keep fallback dash for templates without icon

**Acceptance Criteria:**
- [x] Actual icons rendered in table
- [x] Fallback for no icon
- [x] TypeScript compiles clean

---

## Dependency Graph

```
TASK-001 (npm install)
    │
    TASK-002 (WorkflowIcon component) ◄── TASK-001
    │
    ├── TASK-004 (NewRequestPage) ◄── TASK-002
    ├── TASK-005 (RequestDetailPage) ◄── TASK-002 + TASK-003
    ├── TASK-006 (RequestQueuePage) ◄── TASK-002 + TASK-003
    └── TASK-007 (WorkflowTemplatesPage) ◄── TASK-002

TASK-003 (Types) — independent
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-003
**Batch 2:** TASK-002
**Batch 3 (Parallel):** TASK-004, TASK-005, TASK-006, TASK-007

## Final Checklist

- [x] lucide-react installed
- [x] WorkflowIcon component works for all 6 icon names
- [x] NewRequestPage uses WorkflowIcon (no inline SVGs)
- [x] RequestDetailPage uses WorkflowIcon (no inline SVGs)
- [x] RequestQueuePage shows template name + icon
- [x] WorkflowTemplatesPage shows actual icons
- [x] TypeScript compiles clean
- [x] No inline SVG icon maps remain
