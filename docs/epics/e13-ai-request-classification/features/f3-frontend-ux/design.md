# Design: F3 — Frontend UX

**Requirement:** [../../requirements.md](../../requirements.md)
**Feature:** F3 — Frontend UX
**Date:** 2026-02-18

---

## Architecture Overview

```
NEW FILES:
web/app/src/pages/admin/ClassificationSettingsPage.tsx

MODIFIED FILES:
web/app/src/pages/technician/RequestDetailPage.tsx
web/app/src/router.tsx
web/app/src/components/layout/Sidebar.tsx
web/app/src/types/index.ts
web/app/src/locales/en.ts
web/app/src/locales/es.ts
```

---

## TypeScript Types (`types/index.ts`)

```typescript
export interface CompanyClassificationConfig {
  id: string;
  company_id: string;
  is_enabled: boolean;
  provider: string;
  model?: string | null;
  confidence_threshold: number;
  prompt_template?: string | null;
  timeout_seconds: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AIClassificationData {
  ai_used: boolean;
  provider?: string;
  model?: string;
  confidence?: number;
  suggested_type?: string;
  suggested_subtype?: string | null;
  priority_hint?: number;
  override_applied?: boolean;
  user_original?: { type: string; subtype?: string | null };
  latency_ms?: number;
}
```

---

## ClassificationSettingsPage

Follow `AssignmentAISettingsPage.tsx` pattern:

- `useQuery(['classification-config'])` → `GET /api/v1/settings/request-classification`
- `useMutation` → `PUT /api/v1/settings/request-classification`
- `isDirty` flag: save button disabled when no changes
- `queryClient.invalidateQueries(['classification-config'])` on success
- Toast on save success/error

**Form fields:**
| Field | Type | Validation | Default |
|-------|------|------------|---------|
| Enable AI Classification | Toggle/checkbox | — | false |
| AI Provider | Dropdown: OpenAI / Groq | Required | openai |
| Model | Text input | Optional, max 100 chars | (empty) |
| Confidence Threshold | Number input / slider | 0.5–1.0, step 0.05 | 0.7 |
| Custom Instructions | Textarea | Optional | (empty) |
| Timeout (seconds) | Number input | 1–60 | 10 |

---

## RequestDetailPage — AI Classification Card

Follow `AutoAssignmentCard` component pattern:

**Typed interface:**
```typescript
interface AIClassificationData {
  ai_used: boolean;
  provider?: string;
  model?: string;
  confidence?: number;
  suggested_type?: string;
  suggested_subtype?: string | null;
  priority_hint?: number;
  override_applied?: boolean;
  user_original?: { type: string; subtype?: string | null };
  latency_ms?: number;
}
```

**Render conditions:**
- Only shown when `request.data?.ai_classification?.ai_used === true`
- Only visible to technician+ roles

**Card contents:**
| Field | Display |
|-------|---------|
| Suggested Type | i18n label for type enum value |
| Suggested Subtype | i18n label (or "—" if null) |
| Confidence | Percentage: e.g., "85%" |
| Override Applied | "Yes" / "No" |
| Original Classification | Type + subtype (shown only when override_applied) |
| Priority Hint | Label: -1="Lower", 0="Normal", +1="Higher", +2="Critical" |
| Provider | String value |
| Model | String value |
| Latency | Formatted: e.g., "1.2s" |

**Header badge:**
- "AI Classified" (blue) when `ai_used === true` — shown for any AI involvement, not just overrides

**Priority scoring card update:**
- Add `ai_hint_weight` row when present in `request.data.priority_scoring`

---

## Routing

```typescript
const ClassificationSettingsPage = lazy(() => import('./pages/admin/ClassificationSettingsPage'));

// In admin routes:
{
  path: 'settings/request-classification',
  element: <RequireRole roles={['admin']}><S><ClassificationSettingsPage /></S></RequireRole>,
}
```

---

## Sidebar

Add nav item in `section_management` items array (after Assignment AI):
```typescript
{ to: '/settings/request-classification', labelKey: 'nav.request_classification', roles: ['admin'] }
```

---

## i18n Keys

### English (~30 keys)

**Navigation:**
- `nav.request_classification`: "Request Classification"

**Settings page:**
- `page.classification_settings.title`: "AI Request Classification"
- `page.classification_settings.enable`: "Enable AI Classification"
- `page.classification_settings.provider`: "AI Provider"
- `page.classification_settings.model`: "Model"
- `page.classification_settings.model_placeholder`: "Leave empty for provider default"
- `page.classification_settings.threshold`: "Confidence Threshold"
- `page.classification_settings.threshold_help`: "Minimum confidence (0.5–1.0) required to override user classification"
- `page.classification_settings.prompt`: "Custom Instructions"
- `page.classification_settings.prompt_placeholder`: "Additional instructions for the AI classifier (optional)"
- `page.classification_settings.timeout`: "Timeout (seconds)"
- `page.classification_settings.save`: "Save Settings"
- `page.classification_settings.toast_saved`: "Classification settings saved"
- `page.classification_settings.toast_error`: "Failed to save classification settings"

**Request detail — AI classification card:**
- `page.request_detail.ai_classification`: "AI Classification"
- `page.request_detail.ai_suggested_type`: "Suggested Type"
- `page.request_detail.ai_suggested_subtype`: "Suggested Subtype"
- `page.request_detail.ai_confidence`: "Confidence"
- `page.request_detail.ai_override`: "Override Applied"
- `page.request_detail.ai_original`: "Original Classification"
- `page.request_detail.ai_priority_hint`: "Priority Hint"
- `page.request_detail.ai_provider`: "Provider"
- `page.request_detail.ai_model`: "Model"
- `page.request_detail.ai_latency`: "Latency"
- `page.request_detail.ai_classified_badge`: "AI Classified"
- `page.request_detail.ai_hint_weight`: "AI Hint Weight"
- `page.request_detail.priority_hint_lower`: "Lower"
- `page.request_detail.priority_hint_normal`: "Normal"
- `page.request_detail.priority_hint_higher`: "Higher"
- `page.request_detail.priority_hint_critical`: "Critical"

### Spanish
Same keys, translated.

---

## Testing Strategy

- TypeScript compiles: `cd web/app && npx tsc --noEmit`
- Build succeeds: `cd web/app && npm run build`
- No hardcoded strings (all text uses i18n keys)

---

## Design Decisions

1. **Badge condition: `ai_used === true`** — shows for any AI involvement, not just overrides. Requirements US-E13-003 AC5 says "AI Classified vs Manual" which means any AI usage, not just overrides.
2. **`isDirty` tracking on settings page** — matches `AssignmentAISettingsPage` UX pattern for consistency.
3. **`AIClassificationData` typed interface** — provides type safety for the card component, matching `AutoAssignmentData` pattern.
4. **Separate router for classification** — uses `settings/request-classification` path, consistent with `settings/assignment-ai`.
