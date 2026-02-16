# Tasks: F0 - Invite User by Email

**Feature:** Invite User by Email
**Date:** 2026-02-16

---

## Summary

Admin can invite new users to the company by entering their email on the Users page. The system sends a magic link; when the invitee clicks it, they are auto-created as an employee in the company.

Reuses the existing `CreateMagicLinkCommandHandler` and `send_magic_link_email` flow.

---

## Phase 1: Backend

### T1.1: Add invite endpoint to users router
- **File:** `adapters/http/api/users/routers.py`
- New `POST /api/v1/users/invite` endpoint
- Requires admin role (`require_role(UserRole.ADMIN)`)
- Request body: `{ "email": "user@example.com" }`
- Validates email is not already registered (optional: return friendly message if exists)
- Uses `CreateMagicLinkCommandHandler` with `user_repo` to send magic link
- Returns `201` with success message

### T1.2: Add invite request schema
- **File:** `adapters/http/api/users/schemas.py`
- Add `InviteUserRequest` Pydantic model with `email: EmailStr`

## Phase 2: Frontend

### T2.1: Add invite button and modal to UsersPage
- **File:** `web/app/src/pages/admin/UsersPage.tsx`
- Add "Invite User" button next to filters
- On click: show inline form or simple modal with email input
- On submit: `POST /api/v1/users/invite` with the email
- Show success/error feedback
- On success: invalidate users query to refresh list

## Phase 3: Verification

### T3.1: Manual E2E test
- [ ] Admin clicks "Invite User", enters email, submits
- [ ] Backend sends magic link email (check Mailpit)
- [ ] Invitee clicks link, lands on verify page, gets auto-created as employee
- [ ] New user appears in Users list
