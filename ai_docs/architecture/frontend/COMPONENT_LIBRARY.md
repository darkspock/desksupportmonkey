# Component Library Documentation

Guide to the UI components used in the Metrica.uno AI Compliance Self-Assessment Platform, including shadcn/ui integration and custom components.

---

## Table of Contents

1. [Overview](#overview)
2. [shadcn/ui Components](#shadcnui-components)
3. [Custom Components](#custom-components)
4. [Adding New Components](#adding-new-components)
5. [Component Composition Patterns](#component-composition-patterns)
6. [Styling Guidelines](#styling-guidelines)

---

## Overview

This project uses a combination of:
- **shadcn/ui** - Pre-built, accessible components built with Radix UI and Tailwind CSS
- **Custom Components** - Business-logic specific components for assessments, compliance scoring, etc.
- **Lucide React** - Icon library (800+ icons)

### Why shadcn/ui?

- **Copy-paste, not package** - Components live in your codebase (`src/components/ui/`)
- **Full control** - Modify components as needed
- **TypeScript native** - Full type safety
- **Accessible** - Built on Radix UI primitives
- **Customizable** - Uses Tailwind CSS for styling

---

## shadcn/ui Components

### Installed Components

The following shadcn/ui components are recommended for Metrica.uno:

#### Form Components
- **Button** (`src/components/ui/button.tsx`)
  - Variants: default, destructive, outline, secondary, ghost, link
  - Sizes: default, sm, lg, icon

- **Input** (`src/components/ui/input.tsx`)
  - Text input with consistent styling

- **Label** (`src/components/ui/label.tsx`)
  - Form labels with accessibility support

- **Textarea** (`src/components/ui/textarea.tsx`)
  - Multi-line text input for notes and evidence

- **Switch** (`src/components/ui/switch.tsx`)
  - Toggle switch for yes/no responses

- **Select** (`src/components/ui/select.tsx`)
  - Dropdown selection for response options

- **Slider** (`src/components/ui/slider.tsx`)
  - For scale-based responses (1-5, 1-10)

- **RadioGroup** (`src/components/ui/radio-group.tsx`)
  - For single-choice questions

- **Checkbox** (`src/components/ui/checkbox.tsx`)
  - For multi-choice questions

#### Layout Components
- **Card** (`src/components/ui/card.tsx`)
  - Card container with header, content, footer sections
  - Sub-components: CardHeader, CardTitle, CardDescription, CardContent, CardFooter

- **Tabs** (`src/components/ui/tabs.tsx`)
  - For domain navigation in assessments

- **Progress** (`src/components/ui/progress.tsx`)
  - For assessment progress tracking

#### Overlay Components
- **Dialog** (`src/components/ui/dialog.tsx`)
  - Modal dialog for confirmations, details view
  - Sub-components: DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter

- **Popover** (`src/components/ui/popover.tsx`)
  - Floating popover for tooltips and additional info

- **Tooltip** (`src/components/ui/tooltip.tsx`)
  - Hover tooltip for guidance text
  - Sub-components: TooltipProvider, TooltipTrigger, TooltipContent

- **Sheet** (`src/components/ui/sheet.tsx`)
  - Slide-out panel for mobile navigation

#### Feedback Components
- **Toast** (`src/components/ui/toast.tsx`, `src/components/ui/toaster.tsx`)
  - Toast notifications for save confirmations, errors
  - Custom hook: `src/hooks/use-toast.ts`

- **Alert** (`src/components/ui/alert.tsx`)
  - For displaying gaps and warnings

- **Badge** (`src/components/ui/badge.tsx`)
  - For status indicators, risk levels

### Component Usage Examples

#### Button
```typescript
import { Button } from '@/components/ui/button';

// Basic button
<Button>Submit Response</Button>

// Variants
<Button variant="outline">Cancel</Button>
<Button variant="destructive">Delete Assessment</Button>
<Button variant="ghost">Skip</Button>

// Sizes
<Button size="sm">Previous</Button>
<Button size="lg">Complete Assessment</Button>

// With icon
<Button size="icon">
  <Plus className="h-4 w-4" />
</Button>
```

#### Card
```typescript
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Domain: Governance</CardTitle>
  </CardHeader>
  <CardContent>
    <ScoreGauge score={85} />
    <p className="text-sm text-gray-600">15 questions answered</p>
  </CardContent>
  <CardFooter>
    <Button>View Details</Button>
  </CardFooter>
</Card>
```

#### Dialog
```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const [open, setOpen] = useState(false);

<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Gap Details</DialogTitle>
    </DialogHeader>
    <GapDetails gap={selectedGap} />
  </DialogContent>
</Dialog>
```

#### Progress
```typescript
import { Progress } from '@/components/ui/progress';

<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span>Assessment Progress</span>
    <span>60%</span>
  </div>
  <Progress value={60} />
</div>
```

#### Toast
```typescript
import { useToast } from '@/hooks/use-toast';

const { toast } = useToast();

// Success toast
toast({
  title: 'Response Saved',
  description: 'Your response has been recorded',
});

// Error toast
toast({
  title: 'Error',
  description: 'Failed to save response',
  variant: 'destructive',
});
```

---

## Custom Components

### Assessment Components

Located in `src/components/Assessment/`

#### QuestionCard
**Purpose:** Display a single assessment question with response options

**Props:**
```typescript
{
  question: Question;
  response?: QuestionResponse;
  onResponseChange: (response: ResponseValue) => void;
  onEvidenceUpload: (files: File[]) => void;
  onNotesChange: (notes: string) => void;
  disabled?: boolean;
}
```

**Features:**
- Question text with guidance tooltip
- Response input (varies by question type)
- Evidence upload button
- Notes field
- Progress indicator

#### DomainSelector
**Purpose:** Navigate between the 8 universal domains

**Props:**
```typescript
{
  domains: Domain[];
  currentDomain: DomainCode;
  progress: { [key in DomainCode]: number };
  onDomainChange: (domain: DomainCode) => void;
}
```

**Features:**
- 8 domain tabs/buttons
- Progress indicator per domain
- Current domain highlight
- Completion badges

#### AssessmentProgress
**Purpose:** Show overall assessment progress

**Props:**
```typescript
{
  totalQuestions: number;
  answeredQuestions: number;
  domainProgress: DomainProgress[];
}
```

**Features:**
- Overall progress bar
- Domain-by-domain breakdown
- Questions remaining count
- Estimated time to complete

#### ResponseForm
**Purpose:** Render appropriate input for question type

**Location:** `src/components/Assessment/ResponseForm/`

**Sub-components:**
- `ScaleResponse.tsx` - 1-5 or 1-10 scale inputs
- `YesNoResponse.tsx` - Binary yes/no toggle
- `TextResponse.tsx` - Free text input
- `MultiChoiceResponse.tsx` - Multiple choice selection
- `EvidenceUpload.tsx` - File upload for evidence

### Compliance Components

Located in `src/components/Compliance/`

#### ScoreGauge
**Purpose:** Circular or bar gauge showing compliance score

**Props:**
```typescript
{
  score: number;          // 0-100
  label?: string;         // e.g., "Governance"
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  thresholds?: ScoreThresholds;
}
```

**Features:**
- Color-coded by score level (red/yellow/green)
- Animated fill
- Threshold indicators
- Score value display

#### DomainBreakdown
**Purpose:** Grid showing all 8 domain scores

**Props:**
```typescript
{
  scores: DomainScores;
  onDomainClick?: (domain: DomainCode) => void;
}
```

**Features:**
- 2x4 or 4x2 grid layout
- Domain code and name
- Individual score gauges
- Click to expand details

#### FrameworkComparison
**Purpose:** Compare scores across multiple frameworks

**Props:**
```typescript
{
  projections: FrameworkProjection[];
  selectedFrameworks?: string[];
}
```

**Features:**
- Bar chart comparison
- Framework logos/names
- Score values
- Gap indicators

#### GapAnalysis
**Purpose:** Display identified compliance gaps

**Props:**
```typescript
{
  gaps: Gap[];
  onGapClick: (gap: Gap) => void;
  filter?: GapPriority;
}
```

**Features:**
- Priority-sorted list
- Color-coded by severity (Critical, High, Medium, Low)
- Domain and question reference
- Remediation suggestions

#### GapCard
**Purpose:** Individual gap display card

**Props:**
```typescript
{
  gap: Gap;
  onViewDetails: () => void;
  onMarkResolved: () => void;
}
```

**Features:**
- Gap title and description
- Priority badge
- Affected domain
- Actions (view, resolve)

### Dashboard Components

Located in `src/components/Dashboard/`

#### OverviewCards
**Purpose:** Summary metrics cards

**Features:**
- Total AI systems count
- Active assessments
- Overall compliance score
- Critical gaps count

#### AssessmentsList
**Purpose:** Recent/active assessments list

**Props:**
```typescript
{
  assessments: Assessment[];
  onViewAssessment: (id: string) => void;
  onContinueAssessment: (id: string) => void;
}
```

**Features:**
- Assessment name and status
- Progress indicator
- Last updated date
- Quick actions

#### AlertsPanel
**Purpose:** Items requiring attention

**Features:**
- Critical gaps alert
- Incomplete assessments
- Upcoming deadlines
- Framework updates

### Navigation Components

#### GlobalHeader
**Location:** `src/components/GlobalHeader/`

**Features:**
- Organization switcher dropdown
- Navigation breadcrumbs
- User profile menu
- Notifications icon
- Help/documentation link

#### Sidebar
**Location:** `src/components/Sidebar/`

**Features:**
- Collapsible (256px ↔ 80px)
- Menu items with icons:
  - Dashboard
  - AI Systems
  - Assessments
  - Gap Analysis
  - Reports
  - Settings
- Active route highlighting
- Plan upgrade prompt (for limited plans)

### Report Components

Located in `src/components/Reports/`

#### ReportBuilder
**Purpose:** Configure and generate reports

**Features:**
- Report type selection
- Section selection
- Framework filter
- Preview option
- Export format selection

#### ExportOptions
**Purpose:** Export format and settings

**Features:**
- Format selection (PDF, Word, Excel)
- Include/exclude sections
- Add commentary
- Schedule options

---

## Adding New Components

### Adding shadcn/ui Components

```bash
# List all available components
npx shadcn@latest add

# Add a specific component
npx shadcn@latest add [component-name]

# Examples:
npx shadcn@latest add dropdown-menu
npx shadcn@latest add select
npx shadcn@latest add slider
```

**What happens:**
1. Component file created in `src/components/ui/`
2. Dependencies installed (if needed)
3. Component ready to import and use

**Configuration:** `components.json`
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

### Creating Custom Components

**Location:** Choose based on purpose:
- `src/components/[Feature]/` - Feature-specific components
- `src/components/ui/` - Only for shadcn/ui components (don't put custom here)

**Template:**
```typescript
import React from 'react';

// Import UI components
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

// Define props type
type ScoreCardProps = {
  domain: DomainCode;
  score: number;
  onViewDetails: () => void;
};

// Component
export const ScoreCard: React.FC<ScoreCardProps> = ({ domain, score, onViewDetails }) => {
  return (
    <Card>
      <CardContent className="p-4">
        <h3 className="font-semibold">{domain}</h3>
        <ScoreGauge score={score} size="sm" />
        <Button variant="outline" size="sm" onClick={onViewDetails}>
          View Details
        </Button>
      </CardContent>
    </Card>
  );
};
```

**Best Practices:**
- Use TypeScript for props
- Use shadcn/ui components as building blocks
- Follow Tailwind CSS utility-first approach
- Extract reusable logic to custom hooks
- Keep components focused (single responsibility)

---

## Component Composition Patterns

### Pattern 1: Container and Presentation

**Container Component** (handles logic):
```typescript
// AssessmentWizardContainer.tsx
export const AssessmentWizardContainer = () => {
  const { assessment, questions, submitResponse } = useAssessment();
  const [currentDomain, setCurrentDomain] = useState<DomainCode>('GOV');

  const handleResponse = (questionId: string, response: ResponseValue) => {
    submitResponse(questionId, response);
  };

  if (!assessment) return <LoadingSpinner />;

  return (
    <AssessmentWizard
      questions={questions}
      currentDomain={currentDomain}
      onDomainChange={setCurrentDomain}
      onResponse={handleResponse}
    />
  );
};
```

**Presentation Component** (handles UI):
```typescript
// AssessmentWizard.tsx
type AssessmentWizardProps = {
  questions: Question[];
  currentDomain: DomainCode;
  onDomainChange: (domain: DomainCode) => void;
  onResponse: (questionId: string, response: ResponseValue) => void;
};

export const AssessmentWizard: React.FC<AssessmentWizardProps> = ({
  questions,
  currentDomain,
  onDomainChange,
  onResponse,
}) => {
  return (
    <div className="space-y-6">
      <DomainSelector currentDomain={currentDomain} onChange={onDomainChange} />
      <QuestionList questions={questions} onResponse={onResponse} />
    </div>
  );
};
```

### Pattern 2: Compound Components

**Parent with Sub-components:**
```typescript
// Assessment form with field components
<AssessmentForm>
  <DomainSelector />
  <QuestionCard />
  <ResponseField />
  <EvidenceUpload />
  <NotesField />
  <NavigationButtons />
</AssessmentForm>
```

### Pattern 3: Render Props

**Flexible rendering:**
```typescript
<DataList
  data={gaps}
  renderItem={(gap) => <GapCard gap={gap} />}
  renderEmpty={() => <EmptyState message="No gaps identified" />}
/>
```

---

## Styling Guidelines

### Tailwind CSS Utilities

**Spacing:**
```typescript
<div className="p-4">           {/* Padding */}
<div className="m-4">           {/* Margin */}
<div className="space-y-4">     {/* Vertical spacing between children */}
<div className="gap-4">         {/* Gap in flex/grid */}
```

**Layout:**
```typescript
<div className="flex items-center justify-between">
<div className="grid grid-cols-2 gap-4">
<div className="hidden md:block">  {/* Responsive */}
```

**Colors:**
```typescript
<div className="bg-gray-100 text-gray-900">
<div className="bg-blue-600 text-white">
<div className="border border-gray-200">
```

**Typography:**
```typescript
<h1 className="text-2xl font-bold">
<p className="text-sm text-gray-600">
<span className="font-semibold">
```

### Component Variants

**Use cn() utility for conditional classes:**
```typescript
import { cn } from '@/lib/utils';

<div
  className={cn(
    'p-4 rounded-lg border',
    score >= 80 && 'border-green-500 bg-green-50',
    score >= 50 && score < 80 && 'border-yellow-500 bg-yellow-50',
    score < 50 && 'border-red-500 bg-red-50'
  )}
/>
```

### Consistent Spacing Scale

Use Tailwind's spacing scale consistently:
- `space-y-1` = 0.25rem = 4px
- `space-y-2` = 0.5rem = 8px
- `space-y-4` = 1rem = 16px (most common)
- `space-y-6` = 1.5rem = 24px
- `space-y-8` = 2rem = 32px

---

## Icon Usage

### Lucide React Icons

**Import:**
```typescript
import {
  ClipboardCheck,
  Shield,
  AlertTriangle,
  BarChart3,
  FileText,
  Settings,
  Plus,
  ChevronRight,
} from 'lucide-react';
```

**Usage:**
```typescript
<Button>
  <Plus className="h-4 w-4 mr-2" />
  New Assessment
</Button>

<AlertTriangle className="h-5 w-5 text-amber-500" />
```

**Common Icons for Metrica.uno:**
- `ClipboardCheck` - Assessments
- `Shield` - Compliance/Security
- `AlertTriangle` - Gaps/Warnings
- `BarChart3` - Scores/Analytics
- `FileText` - Reports
- `Settings` - Settings
- `Building2` - Organizations
- `Bot` - AI Systems
- `CheckCircle` - Completed
- `XCircle` - Failed/Critical
- `Info` - Information/Guidance
- `HelpCircle` - Help tooltips

**Icon Sizes:**
- Small: `h-4 w-4` (16px)
- Medium: `h-5 w-5` (20px)
- Large: `h-6 w-6` (24px)

---

## Best Practices

### DO

- Use shadcn/ui components as building blocks
- Compose components from smaller components
- Extract reusable logic to custom hooks
- Use TypeScript for all component props
- Follow Tailwind utility-first approach
- Use semantic color tokens
- Keep components focused (single responsibility)
- Add proper accessibility (ARIA labels, keyboard nav)

### DON'T

- Don't put custom components in `src/components/ui/`
- Don't hardcode colors (use Tailwind classes)
- Don't use inline styles (use Tailwind)
- Don't create monolithic components (break them down)
- Don't duplicate UI logic (create shared components)
- Don't forget TypeScript types
- Don't skip accessibility features

---

## Component Checklist

When creating a new component:

- [ ] TypeScript props type defined
- [ ] Uses shadcn/ui components where applicable
- [ ] Follows Tailwind utility-first styling
- [ ] Responsive design considered
- [ ] Accessible (keyboard nav, ARIA labels)
- [ ] Loading states handled
- [ ] Error states handled
- [ ] Proper component location (feature folder)
- [ ] Reusable logic extracted to hooks
- [ ] Icons from Lucide React
- [ ] Follows project naming conventions

---

## Additional Resources

- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Lucide React Icons](https://lucide.dev/)
- [Recharts](https://recharts.org/)
- [Coding Standards](./CODING_STANDARDS.md)
- [Technical Architecture](./TECHNICAL_ARCHITECTURE.md)

---

**Last Updated:** January 2026
**Maintained by:** Development Team
