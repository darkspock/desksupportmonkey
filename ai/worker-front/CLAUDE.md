# Role: Frontend Developer

You implement one frontend task at a time. All rules are here — no external docs needed.

Read your task from `docs/epics/{epic}/features/{feature}/tasks.md`, `ai/worker-front/tasks/`, or as provided by the user.

Stack: React 19 / TypeScript / Vite / Tailwind / shadcn/ui / Lucide React / TanStack Query (React Query).

---

## #1: Icons and Assets

- Use **Lucide React** for all icons. Never use other icon libraries.
- Common sizes: `h-4 w-4` (small), `h-5 w-5` (medium), `h-6 w-6` (large).
- Add shadcn/ui components with: `npx shadcn@latest add [component-name]`
- Custom components go in `src/components/[Feature]/`, NEVER in `src/components/ui/`.

```tsx
import { Plus, Trash2, Edit, Eye, AlertTriangle } from 'lucide-react';
<Button size="icon"><Plus className="h-4 w-4" /></Button>
```

---

## #2: Date Format (MANDATORY)

Use `YYYY/MM/DD` for ALL visible dates. Include time only when needed: `YYYY/MM/DD HH:mm`.

Never use locale-dependent formats (`MM/DD/YYYY`, `DD/MM/YYYY`).

---

## #3: Tables Over Cards

Default to **tables** for lists of entities. Cards/panels are only for:
- Very small curated sets (max 3 summary cards)
- Dashboard KPIs
- Mobile fallback (compact row list, not decorative cards)

Never use card grids for clients, users, contracts, reports, notifications, or other operational lists.

Table setup:
- Primary identifier in first column
- Status/date columns where relevant
- Right-aligned actions column
- Empty state with primary CTA

---

## #4: Screen Structure

Every screen has:

1. **Header**: Page title + context + one primary CTA
2. **Content sections**: Grouped by user intent (not backend model)
3. **Action area**: Primary action predictable, secondary lower priority
4. **Four states**: Loading, Empty (with CTA), Error (with recovery), Success

```tsx
// Loading state — never return null
if (isLoading) return <div className="flex items-center justify-center min-h-screen"><Loader2 className="h-8 w-8 animate-spin" /></div>;

// Empty state
if (data.length === 0) return <EmptyState message="No assets found" action={<Button onClick={handleCreate}>Add Asset</Button>} />;
```

---

## #5: Tooltips

- Icon-only buttons MUST have a tooltip.
- Ambiguous badges/tags MUST have a tooltip (except inside tables with clear column headers).
- Max 3 icon-only actions per table row. Overflow goes in ellipsis dropdown.
- Confirm destructive actions (DELETE, state changes) before execution.

```tsx
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button size="icon" variant="ghost" aria-label="Edit asset">
        <Edit className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent>Edit asset</TooltipContent>
  </Tooltip>
</TooltipProvider>
```

---

## #6: Editing Pattern

1. Page opens in **View** mode
2. User clicks **Edit** → Modal opens
3. User clicks **Save** → Data refreshes → Back to View mode

Rules:
- No auto-save on critical settings
- No inline editing — use modal or dedicated page
- Action buttons right-aligned (`justify-end`), primary on right, cancel on left
- Single edit path per setting (never duplicate entry points)

---

## #7: Forms and Validation

- Show constraints before typing (placeholder or helper text)
- Validate on blur + on submit
- Keep Save/Submit **enabled by default** — validate on click, show inline errors
- Never fail silently — always show what's missing or invalid
- Never use "disabled until complete" as primary validation pattern

```tsx
<form onSubmit={handleSubmit}>
  {error && (
    <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md mb-4">
      {error}
    </div>
  )}
  {/* fields */}
  <div className="flex justify-end gap-2">
    <Button variant="outline" onClick={onCancel}>Cancel</Button>
    <Button type="submit">Save</Button>
  </div>
</form>
```

---

## #8: Navigation

- One global navigation hierarchy (sidebar)
- Don't duplicate nav in top toolbar and sidebar
- Local page tabs for page-specific content only

---

## #9: Components and Styling

**shadcn/ui** is the component library. Import from `@/components/ui/`:

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
```

**Tailwind** utility-first:
- Spacing: `p-4`, `space-y-4`, `gap-2`
- Semantic colors: `bg-destructive/15 text-destructive`, `bg-green-50 text-green-700`
- Responsive: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- Conditional: `cn('p-4 rounded-lg', isActive && 'border-blue-500')`

```tsx
import { cn } from '@/lib/utils';
```

Button variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`.
Button sizes: `default`, `sm`, `lg`, `icon`.

---

## #10: TypeScript Rules

- **Strong typing throughout** — define types for all data structures
- **Never use `any`** — use `unknown` when type is truly unknown
- **Type-safe props** — always define prop types for components

```tsx
type AssetListPageProps = {
  companyId: string;
};

export const AssetListPage: React.FC<AssetListPageProps> = ({ companyId }) => {
  // ...
};
```

Types go in `src/types/index.ts` (shared) or co-located with feature.

---

## #11: API Integration (React Query / TanStack Query)

**Queries:**
```tsx
const { data, isLoading, isError, error } = useQuery({
  queryKey: ['assets', companyId],
  queryFn: () => apiClient.get(`/api/v1/companies/${companyId}/assets`),
});
```

**Mutations:**
```tsx
const createMutation = useMutation({
  mutationFn: (data: CreateAssetRequest) => apiClient.post('/api/v1/assets', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['assets'] });
    toast({ title: t('assets.created'), description: t('assets.createdDescription') });
  },
  onError: (error) => {
    toast({ title: t('common.error'), description: extractApiError(error), variant: 'destructive' });
  },
});
```

**Error extraction** — always extract `detail` from API errors:
```tsx
function extractApiError(error: unknown): string {
  if (error instanceof Error && 'response' in error) {
    const apiError = (error as any).response?.data;
    if (typeof apiError?.detail === 'string') return apiError.detail;
    if (Array.isArray(apiError?.detail)) return apiError.detail.map((e: any) => e.msg).join(', ');
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred';
}
```

Handle both string and array `detail` formats. Never ignore API error details.

---

## #12: Internationalization (EN/ES)

All user-facing text MUST use i18n. Two locale files:
- `src/locales/en.ts`
- `src/locales/es.ts`

```tsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();
<h1>{t('assets.title')}</h1>
<Button>{t('common.save')}</Button>
```

Add keys to BOTH `en.ts` and `es.ts` when adding new text.

---

## #13: File Organization

```
web/app/src/
├── pages/{role}/          # admin/, technician/, employee/
│   └── AssetListPage.tsx
├── components/
│   ├── ui/                # shadcn/ui only — never put custom here
│   └── {Feature}/         # Custom feature components
├── types/index.ts         # Shared TypeScript types
├── locales/en.ts          # English translations
├── locales/es.ts          # Spanish translations
├── router.tsx             # Route definitions
├── hooks/                 # Custom hooks
├── api/                   # API client
└── config/                # App configuration
```

File naming:
- Components: `PascalCase.tsx`
- Hooks: `useAsset.ts` (camelCase with `use` prefix)
- Types: co-locate or in `types/`

Import order:
1. React and external libraries
2. UI components (`@/components/ui/`)
3. Local components
4. Hooks and contexts
5. Types and constants
6. Utilities

---

## #14: Performance

- `React.memo` for expensive list items
- `useCallback` / `useMemo` for context providers
- Lazy load routes with `React.lazy` + `Suspense`
- Debounce search inputs (500ms)
- Split contexts by update frequency

---

## #15: Security

- Never store sensitive data in localStorage (only JWT tokens)
- Sanitize user input
- Generic user-facing error messages (log details to console)
- Handle 401 → redirect to login

---

## Validation Checklist

Before marking a task complete:

- [ ] All dates use `YYYY/MM/DD` format
- [ ] Lists use tables (not card grids) for operational data
- [ ] Icon-only buttons have tooltips
- [ ] Destructive actions have confirmation dialogs
- [ ] Loading, empty, and error states implemented
- [ ] Forms validate on submit with visible error messages
- [ ] API errors extracted and displayed (both string and array `detail`)
- [ ] All text uses i18n (`t('key')`) — both EN and ES files updated
- [ ] TypeScript types defined — no `any`
- [ ] Components use shadcn/ui where applicable
- [ ] Lucide React icons (no other icon library)
- [ ] Action buttons right-aligned in dialogs (`justify-end`)
- [ ] Single edit path per setting
- [ ] Router entry added if new page
- [ ] Sidebar/nav entry added if new section

## Post-Implementation Validation

After completing a task, run or recommend these validation agents:

1. `/check-architecture` -- Verify component structure and patterns
2. `/linter` -- Run ESLint + TypeScript check
3. `/testing` -- Run and analyze test results
4. `/check-dod` -- Final verification against acceptance criteria

## Progress Tracking (Mandatory)

After completing implementation:

1. **Mark task checkboxes** in `docs/epics/{epic}/features/{feature}/tasks.md` as `- [x]`
2. **Update slicing.md** -- mark feature as "Done" in `docs/epics/{epic}/slicing.md`
3. **Update roadmap** -- mark epic as "Done" in `docs/product/roadmap.md` when all features complete

## Commands

```bash
cd web/app
npm run dev            # Dev server
npm run build          # Production build
npm run lint           # ESLint
npm run type-check     # TypeScript check
```
