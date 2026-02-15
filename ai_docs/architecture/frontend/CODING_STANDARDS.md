# Frontend Coding Standards and Best Practices

This document outlines the coding standards and best practices to follow when contributing to the Metrica.uno frontend. These guidelines ensure consistency, maintainability, and high code quality.

---

## Table of Contents

1. [Contract-First Development](#contract-first-development) **(READ FIRST)**
2. [React Best Practices](#react-best-practices)
3. [TypeScript Guidelines](#typescript-guidelines)
4. [shadcn/ui Component Usage](#shadcnui-component-usage)
5. [Tailwind CSS Standards](#tailwind-css-standards)
6. [Architecture Patterns](#architecture-patterns)
7. [Security Guidelines](#security-guidelines)
8. [API Error Handling](#api-error-handling)
9. [Performance Optimization](#performance-optimization)
10. [Code Organization](#code-organization)

---

## Contract-First Development

**MANDATORY: Read this before implementing any API integration.**

### The Problem

Frontend and backend implemented separately often result in:
- Different field names (`full_name` vs `first_name` + `last_name`)
- Different data formats (form-urlencoded vs JSON)
- Different response structures (`{tokens}` vs `{user, organization, tokens}`)
- Unhandled error cases (expecting 422, getting 500)

### The Solution: API Contracts

Before implementing ANY API integration:

1. **Check the API contract** in `/docs/api-contracts/{feature}.md`
2. **Verify request format** matches contract exactly
3. **Verify response handling** matches contract structure
4. **Handle ALL error cases** listed in contract

### Example: Login Implementation

```typescript
// CHECK CONTRACT FIRST: /docs/api-contracts/auth/login.md

// Contract says: form-urlencoded with "username" field
const formData = new URLSearchParams()
formData.append('username', credentials.email)  // NOT "email"!
formData.append('password', credentials.password)

const response = await apiClient.post('/api/v1/auth/login', formData, {
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
})

// Contract says: response is {user, organization, tokens}
// Extract tokens from nested structure!
const { tokens } = response.data  // NOT response.data directly!
setStoredTokens(tokens)
```

### Checklist Before API Integration

- [ ] Read API contract in `/docs/api-contracts/`
- [ ] Request format matches contract (headers, body structure)
- [ ] Response handling matches contract structure
- [ ] All error status codes handled
- [ ] Error messages extracted correctly for user display

### When Contract Doesn't Exist

If no contract exists for the endpoint you need:
1. **STOP** - Don't implement without a contract
2. Create contract first in `/docs/api-contracts/`
3. Get contract reviewed
4. Then implement

See: [Development Workflow](/ai_docs/architecture/development-workflow.md)

---

## React Best Practices

### Custom Hooks for Context Consumption

**Always create custom hooks to consume React contexts:**

```typescript
// GOOD: Custom hook with error handling
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Usage in components
const { userToken, isAuthenticated } = useAuth();
```

**Why?**
- Simplifies component code
- Provides better error messages
- Centralizes context access logic
- Makes refactoring easier

---

### Performance Optimization with useCallback and useMemo

**Use `useCallback` and `useMemo` for context providers to prevent unnecessary re-renders:**

```typescript
// GOOD: Memoized functions and context value
const submitResponse = useCallback((questionId: string, response: Response) => {
  setResponses(prev => new Map(prev).set(questionId, response));
  // Auto-save to API
  saveResponseToApi(questionId, response);
}, []);

const calculateScores = useCallback(() => {
  const domainScores = computeDomainScores(responses);
  setScores(domainScores);
}, [responses]);

const value = useMemo(
  () => ({
    assessment,
    responses,
    scores,
    submitResponse,
    calculateScores,
  }),
  [assessment, responses, scores, submitResponse, calculateScores]
);
```

**Why?**
- Prevents function recreations on every render
- Prevents context value object recreation
- Reduces unnecessary re-renders of consuming components
- Proper dependency arrays ensure correct behavior

---

### Loading States for Hydration

**Always show a loading state during hydration, never return `null`:**

```typescript
// BAD: Returns null, causes layout shift
if (!isHydrated) {
  return null;
}

// GOOD: Shows loading state
if (!isHydrated) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}
```

**Why?**
- Prevents layout shift when content appears
- Better user experience
- Avoids potential issues with child component hooks

---

### Proper Error Handling

**Handle errors with proper type checking:**

```typescript
// BAD: Using 'any' loses type safety
catch (err: any) {
  console.error('Error:', err);
  setError(err.message);
}

// GOOD: Proper error type handling
catch (err) {
  const error = err instanceof Error ? err : new Error('Unknown error');
  console.error('Error:', error);
  setError(error.message || 'An error occurred');
}
```

**Why?**
- Maintains TypeScript type safety
- Handles non-Error objects gracefully
- Provides better error messages

---

### Component Composition

**Break down complex components into smaller, reusable pieces:**

```typescript
// GOOD: Separate field components for Assessment form
<AssessmentForm>
  <DomainSelector />
  <QuestionCard />
  <ResponseField />
  <EvidenceUpload />
  <NotesField />
  <ProgressIndicator />
</AssessmentForm>
```

**Why?**
- Easier to test individual components
- Better reusability
- Cleaner, more maintainable code
- Follows single responsibility principle

---

## TypeScript Guidelines

### Strong Typing Throughout

**Define proper types for all data structures:**

```typescript
// GOOD: Well-defined types for Metrica.uno domain
export type Assessment = {
  id: string;
  aiSystemId: string;
  organizationId: string;
  status: AssessmentStatus;
  createdAt: string;
  completedAt: string | null;
  domainScores: DomainScores;
  frameworkProjections: FrameworkProjection[];
};

export type DomainCode = 'GOV' | 'TRA' | 'HUM' | 'DAT' | 'FAI' | 'TEC' | 'SAF' | 'DOC';

export type DomainScores = {
  [K in DomainCode]: number;
};

export type QuestionResponse = {
  questionId: string;
  value: ResponseValue;
  evidence?: Evidence[];
  notes?: string;
  answeredAt: string;
};

// GOOD: Type-safe API functions
export const get = async <T>(
  endpoint: string,
  options?: RequestOptions
): Promise<ApiResponse<T>> => {
  // implementation
};
```

---

### Avoid 'any' Type

**Use proper types instead of `any`:**

```typescript
// BAD: Using 'any'
const handleResponse = (data: any) => {
  console.log(data.score);
};

// GOOD: Proper typing
type ScoreData = {
  score: number;
  domain: DomainCode;
  confidence: number;
};

const handleResponse = (data: ScoreData) => {
  console.log(data.score);
};

// GOOD: Use 'unknown' when type is truly unknown
const handleUnknownData = (data: unknown) => {
  if (typeof data === 'object' && data !== null && 'score' in data) {
    console.log((data as { score: number }).score);
  }
};
```

---

### Type-Safe Props

**Always define prop types for components:**

```typescript
// GOOD: Well-defined component props
type QuestionCardProps = {
  question: Question;
  response?: QuestionResponse;
  onResponseChange: (response: ResponseValue) => void;
  onEvidenceUpload: (files: File[]) => void;
  disabled?: boolean;
};

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  response,
  onResponseChange,
  onEvidenceUpload,
  disabled = false,
}) => {
  // implementation
};
```

---

## shadcn/ui Component Usage

### Standard Import Pattern

**Use path aliases for consistent imports:**

```typescript
// GOOD: Standard shadcn/ui imports
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
```

---

### Proper Component Composition

**Follow shadcn/ui's component hierarchy:**

```typescript
// GOOD: Proper Card composition for Assessment results
<Card className="w-full">
  <CardHeader>
    <CardTitle>Domain Score: Governance</CardTitle>
    <CardDescription>Assessment of governance practices</CardDescription>
  </CardHeader>
  <CardContent>
    <ScoreGauge score={85} />
    <p className="text-sm text-gray-600 mt-2">
      Strong governance framework with minor gaps
    </p>
  </CardContent>
  <CardFooter>
    <Button variant="outline">View Details</Button>
  </CardFooter>
</Card>
```

---

### Use Component Variants

**Leverage built-in variants instead of custom styling:**

```typescript
// GOOD: Using variants
<Button variant="outline">Cancel</Button>
<Button variant="destructive">Delete Assessment</Button>
<Button variant="ghost">Skip Question</Button>
<Button variant="default">Submit Response</Button>

// GOOD: Size variants
<Button size="sm">Previous</Button>
<Button size="default">Next Domain</Button>
<Button size="lg">Complete Assessment</Button>
```

---

### Extend Components Properly

**When extending shadcn/ui components, maintain the API:**

```typescript
// GOOD: Extending with additional props
import { Button, ButtonProps } from '@/components/ui/button';

interface LoadingButtonProps extends ButtonProps {
  isLoading?: boolean;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  isLoading,
  children,
  disabled,
  ...props
}) => {
  return (
    <Button disabled={disabled || isLoading} {...props}>
      {isLoading && <Spinner className="mr-2" />}
      {children}
    </Button>
  );
};
```

---

## Tailwind CSS Standards

### Utility-First Approach

**Build layouts entirely with utility classes:**

```typescript
// GOOD: Utility-first approach
<div className="flex items-center justify-between p-4 border-b">
  <h2 className="text-lg font-semibold">Assessment Progress</h2>
  <span className="text-sm text-gray-500">4 of 8 domains complete</span>
</div>
```

**Avoid custom CSS files whenever possible.**

---

### Use Semantic Color Tokens

**Use Tailwind's semantic color system:**

```typescript
// GOOD: Semantic colors with opacity
<div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">
  {error}
</div>

<div className="bg-green-50 text-green-700 border border-green-200 p-3 rounded-md">
  Assessment completed successfully
</div>

<div className="bg-amber-50 text-amber-700 border border-amber-200 p-3 rounded-md">
  3 gaps identified - review recommended
</div>

// BAD: Hardcoded color values
<div style={{ backgroundColor: '#fee2e2', color: '#991b1b' }}>
  {error}
</div>
```

**Why?**
- Maintains theme consistency
- Allows easy theme customization
- Better maintainability

---

### Consistent Spacing

**Use Tailwind's spacing scale consistently:**

```typescript
// GOOD: Consistent spacing utilities
<div className="space-y-4">  {/* Vertical spacing between children */}
  <div className="p-4">      {/* Padding */}
    <h3 className="mb-2">Domain: Governance</h3>
    <p className="text-sm text-gray-600">15 questions</p>
  </div>
</div>

<div className="flex gap-2">  {/* Gap in flex containers */}
  <Button>Previous</Button>
  <Button>Next</Button>
</div>
```

---

### Responsive Design

**Use Tailwind's responsive modifiers:**

```typescript
// GOOD: Mobile-first responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {domains.map(domain => <DomainCard key={domain.code} domain={domain} />)}
</div>

<div className="text-sm md:text-base lg:text-lg">
  Responsive text
</div>
```

---

### Extract Repeated Patterns

**For repeated utility combinations, create reusable components:**

```typescript
// BAD: Repeated utility strings
<div className="flex items-center justify-center p-4 bg-gray-50 rounded-lg border border-gray-200">
  Domain 1
</div>
<div className="flex items-center justify-center p-4 bg-gray-50 rounded-lg border border-gray-200">
  Domain 2
</div>

// GOOD: Extract to component
const DomainBox = ({ children }) => (
  <div className="flex items-center justify-center p-4 bg-gray-50 rounded-lg border border-gray-200">
    {children}
  </div>
);

<DomainBox>Domain 1</DomainBox>
<DomainBox>Domain 2</DomainBox>
```

---

## Architecture Patterns

### Separation of Concerns

**Organize code by responsibility:**

```
src/
├── api/              # API client and HTTP logic
├── components/       # UI components
│   ├── ui/          # shadcn/ui components
│   └── [Feature]/   # Feature-specific components
├── contexts/         # React contexts and providers
├── hooks/           # Custom React hooks
├── pages/           # Page components (routes)
├── types/           # TypeScript type definitions
├── constants/       # Constants and configuration
└── utils/           # Utility functions
```

**Example:**

```typescript
// GOOD: Separated concerns

// api/apiClient.ts - HTTP logic only
export const post = async <T>(endpoint: string, data: any) => { ... };

// hooks/useAssessment.ts - Business logic
export const useAssessment = () => {
  const { post } = useApi();
  const submitResponse = async (questionId: string, response: ResponseValue) => {
    return await post(`/responses/${questionId}`, { response });
  };
  return { submitResponse };
};

// components/QuestionCard.tsx - UI only
export const QuestionCard = () => {
  const { submitResponse } = useAssessment();
  // UI implementation
};
```

---

### Context Usage Patterns

**Use contexts for global state, local state for component-specific data:**

```typescript
// GOOD: Context for global authentication
export const AuthContext = createContext<AuthContextType | null>(null);

// GOOD: Context for assessment-related global state
export const AssessmentContext = createContext<AssessmentContextType | null>(null);

// GOOD: Local state for form inputs
const [selectedDomain, setSelectedDomain] = useState<DomainCode>('GOV');
```

---

### Custom Hooks for Reusability

**Extract reusable logic into custom hooks:**

```typescript
// GOOD: Reusable score calculation hook
export const useFrameworkScores = (assessmentId: string) => {
  const [scores, setScores] = useState<FrameworkScore[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const calculateProjections = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/assessments/${assessmentId}/framework-projections`);
      setScores(response.data);
    } finally {
      setIsLoading(false);
    }
  }, [assessmentId]);

  return { scores, isLoading, calculateProjections };
};
```

---

### Avoid Duplicating Business Logic

**IMPORTANT:** Always try to reuse existing components and business logic instead of reimplementing the same functionality.

**When to reuse:**
- Same business logic (score calculation, response validation, etc.)
- Similar UI patterns (forms, modals, cards)
- Common data transformations
- Shared validation logic
- API call patterns

**Examples:**

```typescript
// BAD: Duplicating score calculation logic
// In AssessmentResults.tsx
const calculateDomainScore = (responses: Response[]) => {
  return responses.reduce((sum, r) => sum + r.value, 0) / responses.length;
};

// In DomainBreakdown.tsx (duplicated!)
const calculateDomainScore = (responses: Response[]) => {
  return responses.reduce((sum, r) => sum + r.value, 0) / responses.length;
};

// GOOD: Shared utility
// utils/scoring.utils.ts
export const calculateDomainScore = (responses: Response[]): number => {
  if (responses.length === 0) return 0;
  return responses.reduce((sum, r) => sum + r.value, 0) / responses.length;
};

// Both components import and use it
import { calculateDomainScore } from '@/utils/scoring.utils';
```

**Before creating new logic, ask yourself:**
1. Does a similar component/hook already exist?
2. Can I extend an existing component with props/variants?
3. Can I extract common logic into a shared utility?
4. Is the duplication worth the independence?

---

## Security Guidelines

### NEVER Store Sensitive Data in localStorage

```typescript
// CRITICAL SECURITY ISSUE: Never do this
localStorage.setItem('password', password);
localStorage.setItem('apiKey', apiKey);

// GOOD: Only store non-sensitive tokens
localStorage.setItem('userToken', jwtToken);

// BETTER: Use httpOnly cookies for production (if possible)
// Set by backend, not accessible via JavaScript
```

**Why?**
- localStorage is not encrypted
- Accessible via JavaScript (XSS vulnerability)
- Persists across sessions
- Visible in browser dev tools

---

### Sanitize User Input

```typescript
// GOOD: Always validate and sanitize inputs
const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const sanitizeInput = (input: string): string => {
  return input.trim().replace(/[<>]/g, '');
};
```

---

### Handle Errors Securely

```typescript
// BAD: Leaking sensitive information
catch (error) {
  alert(`Database error: ${error.stack}`);
}

// GOOD: Generic user-facing messages
catch (error) {
  console.error('Internal error:', error); // Log for debugging
  toast({
    title: 'Error',
    description: 'An error occurred. Please try again.',
    variant: 'destructive',
  });
}
```

---

## API Error Handling

### CRITICAL: Always Handle API Error Responses

**The backend returns structured error responses. The frontend MUST display these to users.**

### Backend Error Response Format

```json
{
  "detail": "Password must contain uppercase letter"
}
```

Or for validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

### Error Handling Pattern

**✅ CORRECT: Extract and display API error messages**

```typescript
const handleSubmit = async (data: RegisterData) => {
  try {
    await register(data);
    navigate('/dashboard');
  } catch (error) {
    // Extract error message from API response
    if (error instanceof Error && 'response' in error) {
      const apiError = (error as any).response?.data;

      // Handle string detail
      if (typeof apiError?.detail === 'string') {
        setError(apiError.detail);
        return;
      }

      // Handle array of validation errors
      if (Array.isArray(apiError?.detail)) {
        const messages = apiError.detail.map((e: any) => e.msg).join(', ');
        setError(messages);
        return;
      }
    }

    // Fallback for unknown errors
    setError('An unexpected error occurred. Please try again.');
  }
};
```

**❌ WRONG: Ignoring API error details**

```typescript
catch (error) {
  // BAD: Generic message, ignores useful API error
  setError('Registration failed');
}
```

### TanStack Query Error Handling

**With mutations:**

```typescript
const registerMutation = useMutation({
  mutationFn: register,
  onError: (error: any) => {
    // Extract API error message
    const message = error.response?.data?.detail || 'Registration failed';
    toast({
      title: 'Error',
      description: typeof message === 'string' ? message : 'Validation error',
      variant: 'destructive',
    });
  },
});
```

**With queries:**

```typescript
const { data, error, isError } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
});

// Display error to user
if (isError) {
  const message = (error as any)?.response?.data?.detail || 'Failed to load user';
  return <ErrorMessage message={message} />;
}
```

### Create Error Extraction Utility

**Centralize error extraction logic:**

```typescript
// utils/api-error.ts
export function extractApiError(error: unknown): string {
  if (error instanceof Error && 'response' in error) {
    const apiError = (error as any).response?.data;

    if (typeof apiError?.detail === 'string') {
      return apiError.detail;
    }

    if (Array.isArray(apiError?.detail)) {
      return apiError.detail.map((e: any) => e.msg).join(', ');
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred';
}

// Usage
catch (error) {
  setError(extractApiError(error));
}
```

### Form Error Display

**Show errors clearly to users:**

```typescript
<form onSubmit={handleSubmit}>
  {error && (
    <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md mb-4">
      {error}
    </div>
  )}

  {/* form fields */}
</form>
```

### Error Response Status Codes

| Status | Meaning | Frontend Action |
|--------|---------|-----------------|
| 400 | Bad Request | Show error message |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "Access denied" |
| 404 | Not Found | Show "Not found" page |
| 409 | Conflict | Show error (e.g., "Email already exists") |
| 422 | Validation Error | Show specific validation message |
| 500 | Server Error | Show generic error, log details |

### Checklist for API Calls

- [ ] Try/catch wraps all API calls
- [ ] Error response `detail` is extracted and displayed
- [ ] Both string and array `detail` formats are handled
- [ ] User sees meaningful error messages, not generic ones
- [ ] 401 errors trigger logout/redirect
- [ ] Loading states shown during API calls

---

## Performance Optimization

### Use React.memo for Expensive Components

```typescript
// GOOD: Memoize expensive list items
export const QuestionCard = React.memo<QuestionCardProps>(({ question, onResponse }) => {
  return (
    <Card>
      {/* expensive rendering */}
    </Card>
  );
});
```

---

### Optimize Context Re-renders

```typescript
// GOOD: Split contexts by update frequency
// Frequently updated
export const AssessmentResponsesContext = createContext<ResponsesData | null>(null);

// Rarely updated
export const OrganizationConfigContext = createContext<OrgConfig | null>(null);
```

---

### Lazy Load Routes

```typescript
// GOOD: Code-splitting with lazy loading
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AssessmentWizard = lazy(() => import('./pages/AssessmentWizard'));
const Reports = lazy(() => import('./pages/Reports'));

<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/assessments/:id/wizard" element={<AssessmentWizard />} />
    <Route path="/reports" element={<Reports />} />
  </Routes>
</Suspense>
```

---

### Debounce Expensive Operations

```typescript
// GOOD: Debounce search input
const [searchTerm, setSearchTerm] = useState('');
const searchTimeoutRef = useRef<number | null>(null);

const handleSearchChange = (value: string) => {
  setSearchTerm(value);

  if (searchTimeoutRef.current) {
    clearTimeout(searchTimeoutRef.current);
  }

  searchTimeoutRef.current = window.setTimeout(() => {
    performSearch(value);
  }, 500);
};
```

---

## Code Organization

### Consistent File Naming

```
// Components: PascalCase
QuestionCard.tsx
DomainSelector.tsx
ScoreGauge.tsx

// Hooks: camelCase with 'use' prefix
useAssessment.ts
useAuth.ts
useFrameworkScores.ts

// Types: camelCase with '.types' suffix
assessment.types.ts
framework.types.ts
domain.types.ts

// Constants: camelCase with '.constants' suffix
api.constants.ts
domains.constants.ts
```

---

### Component File Structure

**Organize complex components in folders:**

```
AssessmentWizard/
├── AssessmentWizard.tsx     # Main component
├── DomainNavigation.tsx     # Sub-component
├── QuestionList.tsx         # Sub-component
├── ProgressBar.tsx          # Sub-component
├── WizardActions.tsx        # Sub-component
└── index.ts                 # Export barrel
```

---

### Clear Import Order

**Group imports logically:**

```typescript
// GOOD: Clear import organization
// 1. React and external libraries
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// 2. UI components
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 3. Local components
import { QuestionCard } from '../QuestionCard';

// 4. Hooks and contexts
import { useAuth } from '../../contexts/AuthContext';
import { useAssessment } from '../../hooks/useAssessment';

// 5. Types and constants
import type { Question, Response } from '../../types/assessment.types';
import { DOMAINS } from '../../constants/domains.constants';

// 6. Utilities
import { calculateDomainScore } from '../../utils/scoring.utils';
```

---

## Summary Checklist

When writing code, ensure you:

- [ ] Create custom hooks for context consumption
- [ ] Use `useCallback` and `useMemo` to prevent unnecessary re-renders
- [ ] Show loading states instead of returning `null`
- [ ] Handle errors with proper type checking
- [ ] **Extract and display API error messages (don't ignore `detail`)**
- [ ] **Handle both string and array error formats from API**
- [ ] Define strong TypeScript types for all data structures
- [ ] Avoid using `any` type
- [ ] **Check for existing components/hooks before creating new ones**
- [ ] **Reuse business logic - avoid duplicating the same functionality**
- [ ] Use shadcn/ui components with proper composition
- [ ] Follow utility-first approach with Tailwind CSS
- [ ] Use semantic color tokens
- [ ] Separate concerns (API, business logic, UI)
- [ ] NEVER store sensitive data in localStorage
- [ ] Optimize performance with memoization and lazy loading
- [ ] Follow consistent file naming conventions
- [ ] Organize imports logically

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Technical Architecture](./TECHNICAL_ARCHITECTURE.md)
- [Component Library](./COMPONENT_LIBRARY.md)
