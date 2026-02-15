# Frontend Technical Architecture

Complete technical documentation of the Metrica.uno AI Compliance Self-Assessment Platform frontend architecture, technology stack, and implementation details.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Technology Stack](#technology-stack)
3. [Architecture Overview](#architecture-overview)
4. [Core Features](#core-features)
5. [API Integration](#api-integration)
6. [Key Components](#key-components)
7. [State Management](#state-management)

---

## Introduction

**Project Name:** Metrica.uno Frontend
**Type:** Single Page Application (SPA)
**Purpose:** Web-based AI compliance self-assessment platform
**Target Users:** Compliance officers, AI system owners, risk managers, auditors

This is a **React + TypeScript web application** designed to provide a comprehensive web interface for conducting AI compliance assessments across multiple regulatory frameworks (EU AI Act, NIST AI RMF, ISO 42001, etc.) using a unified metamodel approach.

### Business Context

Metrica.uno enables organizations to:
- **Self-assess** AI systems against regulatory requirements
- **Answer once, comply everywhere** through the universal compliance metamodel
- **Project scores** to multiple frameworks from a single assessment
- **Identify gaps** and generate remediation roadmaps
- **Export reports** for auditors and stakeholders

---

## Technology Stack

### Core Framework
- **React 19** - Modern React with hooks and concurrent features
- **TypeScript 5.x** - Type-safe development with strict mode
- **Vite 5.x** - Fast build tool and dev server with HMR

### UI & Styling
- **Tailwind CSS 3.x** - Utility-first CSS framework
- **shadcn/ui** - High-quality, accessible component library
  - Button, Input, Card, Switch, Dialog, Popover, Tooltip, etc.
- **Lucide React** - Icon library (800+ icons)
- **clsx** - Conditional class name utility
- **tailwind-merge** - Intelligent Tailwind class merging

### Routing & Navigation
- **React Router v6** - Client-side routing with URL-based state management
- Protected and public route wrappers
- Programmatic navigation

### State Management
- **React Context API** - Global state management with multiple contexts:
  - `AuthContext` - Authentication and JWT token
  - `UserContext` - User profile and organization data
  - `AssessmentContext` - Current assessment state, responses
  - `OrganizationContext` - Organization, AI systems, plan limits

### Data Visualization
- **Recharts** - Charts for compliance scores and gap analysis
- **React Table** - Advanced data tables for assessments
- Progress indicators and score gauges

### Date & Time
- **date-fns 3.x** - Modern date utility library
- Lightweight alternative to moment.js
- Locale-aware formatting

### Internationalization
- **i18next 23.x** - i18n framework
- **react-i18next 14.x** - React bindings for i18next
- **Supported Languages:** English, Spanish (initial)

### Development Tools
- **ESLint** - Code linting with TypeScript support
- **TypeScript Compiler** - Strict type checking
- **Git** - Version control

---

## Architecture Overview

### Directory Structure

```
metrica-frontend/
├── src/
│   ├── api/                      # API client configuration
│   │   └── apiClient.ts          # Fetch wrapper with auth
│   ├── components/
│   │   ├── Assessment/           # Assessment-related components
│   │   │   ├── QuestionCard.tsx
│   │   │   ├── AssessmentProgress.tsx
│   │   │   ├── DomainSelector.tsx
│   │   │   └── ResponseForm/
│   │   ├── Compliance/           # Compliance visualization
│   │   │   ├── ScoreGauge.tsx
│   │   │   ├── FrameworkComparison.tsx
│   │   │   ├── GapAnalysis.tsx
│   │   │   └── DomainBreakdown.tsx
│   │   ├── Dashboard/            # Dashboard components
│   │   │   ├── OverviewCards.tsx
│   │   │   ├── AssessmentsList.tsx
│   │   │   └── AlertsPanel.tsx
│   │   ├── Reports/              # Report components
│   │   │   ├── ReportBuilder.tsx
│   │   │   └── ExportOptions.tsx
│   │   ├── Sidebar/              # Navigation
│   │   │   └── Sidebar.tsx
│   │   ├── GlobalHeader/         # Top navigation
│   │   │   └── GlobalHeader.tsx
│   │   └── ui/                   # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── card.tsx
│   │       └── ...
│   ├── constants/
│   │   ├── api.constants.ts      # API endpoint URLs
│   │   ├── domains.constants.ts  # 8 universal domains
│   │   └── frameworks.constants.ts
│   ├── contexts/                 # React contexts
│   │   ├── AuthContext.tsx       # Authentication state
│   │   ├── UserContext.tsx       # User and organization data
│   │   ├── AssessmentContext.tsx # Current assessment
│   │   └── OrganizationContext.tsx
│   ├── hooks/                    # Custom React hooks
│   │   ├── useAssessment.ts
│   │   ├── useFrameworkScores.ts
│   │   └── use-toast.ts
│   ├── locales/                  # Translation files
│   │   ├── en.json
│   │   └── es.json
│   ├── pages/                    # Page components (routes)
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── AISystems.tsx
│   │   ├── NewAssessment.tsx
│   │   ├── AssessmentWizard.tsx
│   │   ├── AssessmentResults.tsx
│   │   ├── FrameworkDetails.tsx
│   │   ├── GapAnalysis.tsx
│   │   ├── Reports.tsx
│   │   ├── Settings.tsx
│   │   └── Organization.tsx
│   ├── types/                    # TypeScript definitions
│   │   ├── assessment.types.ts
│   │   ├── framework.types.ts
│   │   ├── domain.types.ts
│   │   └── organization.types.ts
│   ├── utils/                    # Utility functions
│   │   ├── scoring.utils.ts
│   │   └── validation.utils.ts
│   ├── App.tsx                   # Root component with routing
│   ├── i18n.ts                   # i18n configuration
│   └── main.tsx                  # Entry point
├── docs/                         # Documentation
├── dist/                         # Build output (gitignored)
├── public/                       # Static assets
├── index.html                    # HTML template
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
├── vite.config.ts                # Vite configuration
└── tailwind.config.js            # Tailwind configuration
```

### Context Provider Hierarchy

```
App (BrowserRouter)
 └── AuthProvider
      └── UserProvider
           └── OrganizationProvider
                └── AssessmentProvider (route-specific)
                     └── MainLayout
                          ├── GlobalHeader
                          ├── Sidebar
                          └── Page Components
```

**Why this order?**
- Auth first (needed by all)
- User data depends on auth
- Organization context depends on user (multi-tenant)
- Assessment data depends on organization and selected AI system

### Data Flow

1. **Authentication Flow**
   ```
   Login → JWT Token → localStorage → AuthContext
   ```

2. **Organization Selection**
   ```
   User selects org → API call → OrganizationContext → Plan limits applied
   ```

3. **Assessment Data Flow**
   ```
   AI System selected → Questions loaded → Responses collected → Scores calculated
   ```

4. **Scoring Flow**
   ```
   Responses → Domain Scores → Framework Projections → Gap Analysis
   ```

---

## Core Features

### 1. Authentication System
- **Email/password login** or SSO (Enterprise plan)
- JWT token management in localStorage
- Automatic token refresh
- Protected routes with redirect
- Role-based access (Admin, Assessor, Viewer)

### 2. Dashboard
- **Overview Cards**: Total AI systems, active assessments, compliance score
- **Recent Assessments**: List with status and scores
- **Framework Summary**: Quick view of compliance across frameworks
- **Alerts Panel**: Items requiring attention (gaps, deadlines)

### 3. AI System Management
- **List View**: All AI systems with risk levels and compliance status
- **Create AI System**: Name, description, risk classification
- **Risk Classification**: Minimal, Limited, High-Risk, Unacceptable
- **Assessment History**: View past assessments per system

### 4. Assessment Wizard
- **Domain-by-Domain Navigation**: 8 universal domains
- **Question Interface**:
  - Question text with guidance
  - Response options (scale, yes/no, text)
  - Evidence upload capability
  - Notes field
- **Progress Tracking**: Visual progress per domain
- **Save & Continue**: Auto-save responses
- **Skip Logic**: Conditional questions based on risk level

### 5. Compliance Scoring
- **Domain Scores**: GOV, TRA, HUM, DAT, FAI, TEC, SAF, DOC
- **Framework Projections**: Map domain scores to specific frameworks
- **Score Visualization**: Gauges, radar charts, bar comparisons
- **Historical Trending**: Track score changes over time

### 6. Gap Analysis
- **Gap Identification**: Missing or insufficient controls
- **Priority Ranking**: Critical, High, Medium, Low
- **Remediation Suggestions**: AI-powered recommendations
- **Action Items**: Track remediation tasks

### 7. Report Generation
- **Report Types**: Executive summary, detailed, framework-specific
- **Export Formats**: PDF, Word, Excel
- **Customization**: Select sections, add commentary
- **Audit Trail**: Full history of changes

### 8. Plan-Based Features
| Feature | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| AI Systems | 1 | 3 | 15 | Unlimited |
| Frameworks | 1 | 2 | All | All + Custom |
| Questions | 30 | 60 | 150 | Custom |
| Gaps Shown | 5 | 10 | All | All |
| Reports | Basic | Standard | Advanced | White-label |

---

## API Integration

### Base URL
```
https://api.metrica.com/v1/
```

### Authentication Pattern

All authenticated requests include JWT token:
```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
  'X-Organization-ID': organizationId
}
```

### Key API Endpoints

#### Authentication
- `POST /auth/login` - Email/password login
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout and invalidate token

#### Organizations
- `GET /organizations` - List user's organizations
- `GET /organizations/:id` - Get organization details
- `GET /organizations/:id/plan` - Get plan limits

#### AI Systems
- `GET /organizations/:orgId/ai-systems` - List AI systems
- `POST /organizations/:orgId/ai-systems` - Create AI system
- `GET /ai-systems/:id` - Get AI system details
- `PATCH /ai-systems/:id` - Update AI system

#### Assessments
- `GET /ai-systems/:id/assessments` - List assessments
- `POST /ai-systems/:id/assessments` - Start new assessment
- `GET /assessments/:id` - Get assessment with responses
- `PATCH /assessments/:id` - Update assessment

#### Questions & Responses
- `GET /assessments/:id/questions` - Get questions for assessment
- `POST /assessments/:id/responses` - Submit responses (batch)
- `PATCH /responses/:id` - Update single response

#### Scores & Reports
- `GET /assessments/:id/scores` - Get domain scores
- `GET /assessments/:id/framework-projections` - Get framework scores
- `GET /assessments/:id/gaps` - Get gap analysis
- `POST /assessments/:id/reports` - Generate report

### API Response Format

Standard response structure:
```typescript
{
  success: boolean;
  data: T;
  meta?: {
    pagination?: PaginationMeta;
    planLimits?: PlanLimits;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

---

## Key Components

### Page Components

1. **Login** (`/login`)
   - Email/password form
   - SSO buttons (Enterprise)
   - Forgot password link

2. **Dashboard** (`/dashboard`)
   - Overview metrics
   - Recent activity
   - Quick actions

3. **AISystems** (`/ai-systems`)
   - AI systems list
   - Risk classification badges
   - Compliance status indicators

4. **NewAssessment** (`/ai-systems/:id/assess`)
   - Select assessment scope
   - Choose frameworks
   - Start wizard

5. **AssessmentWizard** (`/assessments/:id/wizard`)
   - Domain navigation
   - Question cards
   - Response forms
   - Progress tracking

6. **AssessmentResults** (`/assessments/:id/results`)
   - Score summary
   - Domain breakdown
   - Framework projections
   - Gap overview

7. **GapAnalysis** (`/assessments/:id/gaps`)
   - Detailed gaps list
   - Priority filtering
   - Remediation tracking

8. **Reports** (`/reports`)
   - Report templates
   - Generation queue
   - Download history

### Reusable Components

#### GlobalHeader
- Organization switcher
- Navigation breadcrumbs
- User menu
- Notifications icon

#### Sidebar
- Collapsible navigation (256px ↔ 80px)
- Menu items with Lucide icons
- Active route highlighting
- Plan upgrade prompt

#### QuestionCard
- Question text with context
- Response input (varies by type)
- Evidence upload
- Notes field
- Guidance tooltip

#### ScoreGauge
- Circular or bar visualization
- Score value display
- Threshold indicators
- Color-coded by level

#### DomainBreakdown
- 8 domains grid
- Individual domain scores
- Click to expand details
- Visual comparison

#### FrameworkComparison
- Side-by-side framework scores
- Bar chart visualization
- Gap highlighting

---

## State Management

### AuthContext

**Purpose:** Manage authentication state and JWT token

**State:**
- `userToken: string | null`
- `isAuthenticated: boolean`
- `user: User | null`

**Methods:**
- `login(email, password)`
- `logout()`
- `refreshToken()`

**Storage:** JWT token in `localStorage`

### UserContext

**Purpose:** Store user profile data

**State:**
- `user: UserProfile | null`
- `preferences: UserPreferences`

**Methods:**
- `updateProfile(data)`
- `updatePreferences(prefs)`

### OrganizationContext

**Purpose:** Manage organization and plan limits

**State:**
- `organization: Organization | null`
- `planLimits: PlanLimits`
- `aiSystemsCount: number`

**Methods:**
- `switchOrganization(orgId)`
- `checkPlanLimit(feature)`

### AssessmentContext

**Purpose:** Manage current assessment state

**State:**
- `assessment: Assessment | null`
- `questions: Question[]`
- `responses: Map<string, Response>`
- `currentDomain: DomainCode`
- `progress: AssessmentProgress`

**Methods:**
- `loadAssessment(id)`
- `submitResponse(questionId, response)`
- `navigateToDomain(domain)`
- `calculateScores()`

---

## Multi-Tenant Architecture

### Organization Isolation

All API calls include `X-Organization-ID` header:
```typescript
const apiClient = {
  get: async (endpoint) => {
    const { organization } = useOrganization();
    return fetch(endpoint, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': organization.id
      }
    });
  }
};
```

### Plan-Based Feature Gating

```typescript
const PlanGate: React.FC<{ feature: string; children: ReactNode }> = ({
  feature,
  children
}) => {
  const { checkPlanLimit } = useOrganization();

  if (!checkPlanLimit(feature)) {
    return <UpgradePrompt feature={feature} />;
  }

  return <>{children}</>;
};

// Usage
<PlanGate feature="unlimited_frameworks">
  <FrameworkSelector />
</PlanGate>
```

---

## Performance Considerations

### Code Splitting
- Lazy load routes
- Separate chunks for heavy components (charts, reports)

### Optimizations
- Memoization with useMemo and useCallback
- Debounced search inputs
- Pagination for large lists
- Response caching

### Bundle Size
- Tree-shaking for unused code
- Dynamic imports for optional features

---

**Last Updated:** January 2026
**Version:** 1.0

For coding standards, see [Coding Standards](./CODING_STANDARDS.md)
For component library, see [Component Library](./COMPONENT_LIBRARY.md)
