# Manual Test Plan: E33 — Change Management

**Epic:** Change Management (ITIL)
**Features:** F0 (CRUD + State Machine), F1 (Asset Linking), F2 (PIR), F3 (Dashboard)
**Date:** 2026-02-28

## Prerequisites

```bash
make start-docker    # PostgreSQL, Redis, Mailpit, MinIO
make db-upgrade      # Apply migrations
make seed            # Load demo data
make start           # Backend + Frontend + Celery
```

Login as **Admin**: `alice.smith@techcorp.com` (magic link → Mailpit http://localhost:8028)

---

## F0: Change Request CRUD + State Machine

### T01 — Create a Standard Change

1. Navigate to **Changes** in sidebar
2. Click **"New Change Request"**
3. Fill in:
   - Title: "Install Windows security patch KB5034441"
   - Description: "Monthly security patch for all Windows workstations"
   - Type: **Standard**
   - Priority: **Medium**
   - Risk Level: **Low**
   - Planned date: tomorrow's date
   - Rollback plan: "Uninstall patch via DISM"
4. Submit

**Expected:** Change created in **Draft** status, appears in list, timeline shows "created" event.

### T02 — Create an Emergency Change

1. Create another change:
   - Title: "Emergency DNS fix — production outage"
   - Type: **Emergency**
   - Priority: **Critical**
   - Risk Level: **High**
   - Rollback plan: "Revert DNS to backup config"
2. Submit

**Expected:** Change created in Draft status with Emergency type badge.

### T03 — Full Lifecycle (Draft → Closed)

1. Open the Standard change from T01
2. Click **"Submit for Approval"** → status becomes **Pending Approval**
3. Click **"Approve"** → status becomes **Scheduled**
4. Click **"Start Implementation"** → status becomes **In Progress**
5. Click **"Mark Implemented"** → status becomes **Implemented**
6. Click **"Close"** → status becomes **Closed**

**Expected:** Each transition updates the status badge, adds a timeline event with timestamp and actor. All 6 transitions work in sequence.

### T04 — Rejection Flow

1. Create a new change (any type)
2. Submit for approval
3. Click **"Reject"** → enter rejection reason

**Expected:** Status becomes **Rejected**. Rejection reason shown in timeline. No further transitions available.

### T05 — Rollback Flow

1. Create a change, advance to **In Progress**
2. Click **"Rollback"** → enter rollback reason

**Expected:** Status becomes **Rolled Back**. Rollback reason and timestamp in timeline.

### T06 — Edit Change Request

1. Open a change in **Draft** status
2. Edit title, description, priority, risk level, planned date
3. Save

**Expected:** Changes saved, timeline shows "updated" event with old/new values.

### T07 — List Page Filtering

1. Go to Changes list
2. Filter by status (e.g., only "Closed")
3. Filter by type (e.g., only "Emergency")
4. Search by title text

**Expected:** List filters correctly. Pagination works if >10 items.

### T08 — Non-admin Access Denied

1. Login as **Technician**: `bob.johnson@techcorp.com`
2. Try to access `/changes` URL directly

**Expected:** 403 or redirect — changes are admin-only.

---

## F1: Asset Linking

### T09 — Link Assets to Change

1. Login as admin, open a change request
2. Find the **"Affected Assets"** section
3. Click **"Link Asset"**
4. Search and select 2-3 assets
5. Confirm

**Expected:** Assets appear in the affected assets list with name, type, and serial number. Timeline shows "assets linked" event.

### T10 — Unlink Asset

1. In the affected assets section, click remove/unlink on one asset

**Expected:** Asset removed from list. Timeline shows "asset unlinked" event.

### T11 — View Asset Detail from Change

1. Click on an asset name in the affected assets list

**Expected:** Navigates to asset detail page.

---

## F2: Post-Implementation Review (PIR)

### T12 — Create PIR on Implemented Change

1. Open a change in **Implemented** status (use the one from T03 or create a new one and advance it)
2. Find the **"Post-Implementation Review"** section
3. Click **"Add Review"**
4. Fill in:
   - Outcome: **Successful**
   - Issues found: "Minor delay in deployment"
   - Lessons learned: "Need better rollout schedule"
   - Follow-up actions: "Update deployment checklist"
5. Submit

**Expected:** PIR card appears showing outcome (green "Successful" badge), issues, lessons, follow-up. Created by name and date shown.

### T13 — Emergency Change Cannot Close Without PIR

1. Open the Emergency change from T02
2. Advance it: Submit → Approve → Start → Mark Implemented
3. Try to click **"Close"**

**Expected:** Error — emergency changes require a PIR before closing.

4. Add a PIR (any outcome)
5. Now click **"Close"**

**Expected:** Change closes successfully.

### T14 — Standard Change Closes Without PIR

1. Create a standard change, advance to Implemented
2. Click **"Close"** without adding a PIR

**Expected:** Closes successfully — PIR is only mandatory for emergency type.

---

## F3: Change Dashboard

### T15 — Dashboard Overview

1. Navigate to **Changes > Dashboard** in sidebar

**Expected:** Dashboard page loads with:
- **5 stat cards:** Total Open, Pending Approval, In Progress, Implemented, Scheduled This Week
- **Status distribution** bar chart (8 statuses)
- **Type distribution** bar chart (3 types: standard, emergency, normal)
- **Upcoming Scheduled** table (changes with planned dates in next 30 days)
- **Recently Implemented** table (changes implemented in last 30 days with PIR outcome)

### T16 — Dashboard Reflects Real Data

1. Verify the stat cards match the actual changes you created in T01-T14
2. Check that counts are consistent (e.g., if you closed 2 changes, closed count = 2)

**Expected:** All numbers match the actual state of changes in the system.

### T17 — Rolled Back Alert

1. If you performed a rollback in T05, check the dashboard

**Expected:** A red "Rolled Back" alert card shows count of rollbacks in last 90 days.

### T18 — Dashboard Non-admin Access

1. Login as technician
2. Try to access `/changes/dashboard` directly

**Expected:** 403 or redirect.

---

## Cross-Feature Checks

### T19 — Timeline Completeness

1. Open a change that went through the full lifecycle (T03)
2. Scroll to the timeline section

**Expected:** Complete audit trail showing: created → submitted → approved → started → implemented → (PIR created if applicable) → closed. Each entry has actor name, timestamp, and relevant data.

### T20 — i18n

1. Switch language to Spanish (language toggle)
2. Navigate through Changes list, detail, and dashboard

**Expected:** All labels, status names, buttons, and dashboard headings in Spanish.

---

## Quick Smoke Test (5 minutes)

If you only have 5 minutes, do this:

1. Login as admin
2. Create a standard change (T01)
3. Walk it through the full lifecycle (T03)
4. Link an asset (T09)
5. Add a PIR (T12)
6. Check the dashboard (T15)

This covers all 4 features end-to-end.
