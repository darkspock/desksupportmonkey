# Solution Design: Feature 3 — Queue & Icons

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-25
**Bounded Context:** Frontend only (no backend changes)

## Summary

Install `lucide-react` and create a shared `WorkflowIcon` component that renders any lucide icon by its string name. Replace all hardcoded inline SVG icon maps (ICON_MAP in NewRequestPage, TYPE_ICONS in RequestDetailPage) with this component. Update RequestQueuePage to show template name/icon in both table and kanban views. Update WorkflowTemplatesPage admin table to render actual icons instead of text badges.

## Architecture Decision

**Approach: Dynamic lucide icon lookup via `icons` object**

lucide-react exports an `icons` object that maps icon names to components. We can look up icons dynamically:

```typescript
import { icons } from 'lucide-react';
const IconComponent = icons['alert-circle']; // → LucideAlertCircle component
```

This is simpler than a manual switch/map and automatically supports all 1400+ lucide icons. We wrap this in a `WorkflowIcon` component with a fallback for unknown names.

**Why not tree-shake individual imports?** The icon names come from the database at runtime. We can't statically import individual icons. The full lucide-react icons object adds ~200KB to the bundle (gzipped ~40KB), which is acceptable for an admin/technician app.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ICON_MAP + TemplateIcon | `NewRequestPage.tsx:20-69` | No (local) | Replace with WorkflowIcon |
| TYPE_ICONS | `RequestDetailPage.tsx:194-228` | No (local) | Replace with WorkflowIcon |
| Icon text badge | `WorkflowTemplatesPage.tsx:339-345` | No | Replace with WorkflowIcon |
| RequestQueuePage table | `RequestQueuePage.tsx:599-602` | — | Add icon next to type label |
| ServiceRequest TS type | `types/index.ts:169-190` | Yes | Add workflow_template_name/icon fields |
| Backend schemas | `schemas.py` | Done (F1) | Already has workflow_template_name/icon |
| Backend router list enrichment | `routers.py` | Done (F1) | Already enriches list response |

## Implementation Plan

### 1. Install lucide-react

```bash
cd web/app && npm install lucide-react
```

### 2. Create WorkflowIcon Component

**File:** `web/app/src/components/ui/WorkflowIcon.tsx` (NEW)

```typescript
import { icons, type LucideProps } from 'lucide-react';

interface WorkflowIconProps extends LucideProps {
  name?: string | null;
}

export function WorkflowIcon({ name, ...props }: WorkflowIconProps) {
  if (!name) return null;
  // lucide-react icon names are PascalCase internally, but our DB stores kebab-case
  // The icons object uses PascalCase keys like "AlertCircle"
  const pascalName = name.replace(/(^|-)(\w)/g, (_, __, c) => c.toUpperCase());
  const Icon = icons[pascalName as keyof typeof icons];
  if (!Icon) return null;
  return <Icon {...props} />;
}
```

### 3. Update TypeScript Types

**File:** `web/app/src/types/index.ts`

Add to ServiceRequest interface:
```typescript
workflow_template_name?: string | null;
workflow_template_icon?: string | null;
```

### 4. Replace NewRequestPage Icons

Remove ICON_MAP and TemplateIcon. Import WorkflowIcon. Use:
```tsx
<WorkflowIcon name={tmpl.icon} className="h-5 w-5" />
```

### 5. Replace RequestDetailPage Icons

Remove TYPE_ICONS map. Use workflow_template_icon from request data:
```tsx
<WorkflowIcon name={request.workflow_template_icon} className="h-6 w-6" />
```

Fall back to a generic icon when no template icon is available (old requests without template).

### 6. Update RequestQueuePage

**Table view:** Add icon before type text:
```tsx
<WorkflowIcon name={r.workflow_template_icon} className="h-4 w-4" />
<span>{r.workflow_template_name || t(`enum.${r.type}`)}</span>
```

**Kanban view:** Add small type badge with icon to cards.

### 7. Update WorkflowTemplatesPage

Replace text badge with rendered icon:
```tsx
<WorkflowIcon name={tmpl.icon} className="h-4 w-4" />
```

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `web/app/src/components/ui/WorkflowIcon.tsx` | New | Shared icon component |
| `web/app/src/types/index.ts` | Modify | Add template fields to ServiceRequest |
| `web/app/src/pages/employee/NewRequestPage.tsx` | Modify | Replace ICON_MAP with WorkflowIcon |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Modify | Replace TYPE_ICONS with WorkflowIcon |
| `web/app/src/pages/technician/RequestQueuePage.tsx` | Modify | Add template name/icon to table + kanban |
| `web/app/src/pages/admin/WorkflowTemplatesPage.tsx` | Modify | Render actual icons |
| `web/app/package.json` | Modify | Add lucide-react |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| TypeScript compile | All modified files | High |
| Bundle size check | After lucide-react install | Medium |
| Visual verification | All 4 pages render icons | High |

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bundle size increase | Certain | Low | lucide-react gzipped ~40KB, acceptable |
| Icon name mismatch | Low | Low | WorkflowIcon returns null for unknown names, graceful fallback |
| Old requests without template | Certain | Low | Fall back to `t('enum.${type}')` for display name |
