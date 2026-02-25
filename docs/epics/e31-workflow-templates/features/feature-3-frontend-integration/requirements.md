# Feature 3: Queue & Icons

**Parent Epic:** [../../requirement.md](../../requirement.md)
**Feature #:** 3
**Dependencies:** Feature 0
**Complexity:** S

## Scope

### Included
- **Install lucide-react**: Add to `web/app/package.json` for icon rendering.
- **RequestQueuePage.tsx**: Show template name and icon instead of hardcoded enum values in both table and kanban views.
- **Icon rendering component**: Shared component that renders a lucide icon by name string (from template.icon field). Used in NewRequestPage (F1), RequestQueuePage, WorkflowTemplatesPage, RequestDetailPage.

### Excluded (in other features)
- NewRequestPage type picker (Feature 1)
- Checklist functionality (Feature 2)
- Data migration (Feature 4)

## User Value

Technicians see meaningful template names and icons in the request queue instead of raw enum values. The icon system provides visual consistency across all pages that display request types.

## Acceptance Criteria

- [x] lucide-react installed in web/app
- [x] RequestQueuePage table view shows template name + icon
- [x] RequestQueuePage kanban view shows template name + icon
- [x] Icon component renders lucide icon from string name
- [x] Fallback for unknown/missing icon names
- [x] TypeScript compiles clean
- [x] No bundle size regression > 50KB

## Technical Scope

### Key Components
- `web/app/package.json` — Add lucide-react dependency
- `web/app/src/pages/technician/RequestQueuePage.tsx` — Replace enum display with template name/icon
- `web/app/src/components/ui/WorkflowIcon.tsx` — Shared icon-by-name component (new)
