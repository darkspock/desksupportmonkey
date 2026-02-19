# E17 - Scheduled Maintenance

## Goal
Implement recurring and one-off maintenance for assets, including templates, plans, technician lifecycle, reminders, and overdue alerts.

## Scope
- New bounded context `maintenance_bc`
- Maintenance records lifecycle (scheduled, in progress, completed, cancelled, skipped)
- Template and recurring plan management
- Celery reminder and overdue processing
- Backend API and frontend UX

## Feature Slices
- F0: Domain & Infrastructure
- F1: Maintenance Lifecycle
- F2: Templates & Recurring Plans
- F3: Frontend

## Acceptance Criteria
- Maintenance data model supports one-off and recurring flows.
- Lifecycle transitions are enforced in domain methods.
- Reminders/overdue processing is available via Celery jobs.
- UI supports listing, detail actions, and template/plan management.
