# Tasks: F22 - Real-Time Notifications Hardening

**Feature:** WebSocket-Driven Notification UX
**Date:** 2026-02-16

---

## Summary

Notification unread count currently relies on periodic polling. Integrate existing WebSocket hook so UI updates in near real time, with polling fallback for resilience.

---

## Phase 1: Integration Design

### T1.1: Define event handling contract
- Identify relevant event types from `/ws`.
- Define how unread counter and notifications list cache should update on message.

### T1.2: Decide fallback behavior
- Keep polling as fallback when socket is disconnected.
- Ensure no duplicate increments on reconnect.

## Phase 2: Wire WebSocket to State

### T2.1: Integrate hook usage in top-level layout/provider
- **Files:** `web/app/src/hooks/useWebSocket.ts`, `web/app/src/components/layout/Header.tsx` and/or shared provider.
- Update React Query caches (`notifications`, `notifications-unread`) on incoming events.

### T2.2: Handle reconnect and stale state
- Re-sync unread data after reconnect or focus regain.

## Phase 3: Verification

### T3.1: Manual checks
- [ ] New notification updates unread badge without 30s wait
- [ ] Notifications page reflects new item shortly after event
- [ ] Socket reconnect does not duplicate or lose count
- [ ] Fallback polling still works when WebSocket unavailable

