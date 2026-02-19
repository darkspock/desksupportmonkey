# Tasks: F4 — Frontend: Calendar & Appointment UX

**Created:** 2026-02-18
**Total Tasks:** 8
**Estimated Complexity:** H

---

## Phase 1: TypeScript Types

### 1. Add appointment types
- [x] Edit `web/app/src/types/index.ts`
  - Add `Appointment` interface: id, company_id, request_id, technician_id, employee_id, status, scheduled_start, scheduled_end, duration_minutes, location, notes, cancellation_reason, cancelled_by, rescheduled_from_id, completed_at, created_by, created_at, updated_at, technician_email, employee_email
  - Add `AppointmentStatus` type: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'
  - Add `AvailabilityWindow` interface: id, day_of_week, start_time, end_time
  - Add `AvailabilityOverride` interface: id, date, is_available, start_time, end_time, reason, created_at, updated_at
  - Add `TimeSlot` interface: start, end

---

## Phase 2: Calendar Page (Technician)

### 2. Create CalendarPage
- [x] Create `web/app/src/pages/technician/CalendarPage.tsx`
  - Week view with 7 columns (Mon-Sun) and time rows (8:00-18:00)
  - Fetches appointments for the selected week via `GET /api/v1/appointments?date_from=...&date_to=...`
  - Shows appointment blocks with employee name, time, status badge
  - Week navigation (previous/next week)
  - Click on appointment to navigate to request detail
  - Uses Tailwind grid layout

---

## Phase 3: Availability Settings Page (Technician)

### 3. Create AvailabilitySettingsPage
- [x] Create `web/app/src/pages/technician/AvailabilitySettingsPage.tsx`
  - Recurring schedule form: 7 day checkboxes, start/end time per day
  - Loads existing schedule via `GET /api/v1/availability/technicians/{id}`
  - Saves via `PUT /api/v1/availability/technicians/{id}`
  - Override section: list of date-specific overrides
  - Add override form (date, is_available, times, reason)
  - Delete override button

---

## Phase 4: My Appointments Page (Employee)

### 4. Create MyAppointmentsPage
- [x] Create `web/app/src/pages/employee/MyAppointmentsPage.tsx`
  - Lists employee's appointments via `GET /api/v1/my/appointments`
  - Shows date, time, technician, status badge
  - Cancel button for PENDING/CONFIRMED appointments
  - Paginated list

---

## Phase 5: Request Detail Integration

### 5. Add appointment section to RequestDetailPage
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
  - Add "Appointments" card section showing linked appointments
  - Fetches via `GET /api/v1/appointments?request_id={id}`
  - Shows list with status badges
  - "Schedule Appointment" button for technicians (opens booking form)
  - Booking form: date picker, time slot selector (fetched from `/availability/technicians/{id}/slots`), duration

---

## Phase 6: Routing & Sidebar

### 6. Add routes and navigation
- [x] Edit `web/app/src/router.tsx`
  - Add lazy imports: CalendarPage, AvailabilitySettingsPage, MyAppointmentsPage
  - Add routes:
    - `calendar` → technician+ (RequireRole)
    - `settings/availability` → technician+ (RequireRole)
    - `my/appointments` → employee (no role restriction needed since my/ endpoints handle it)
- [x] Edit `web/app/src/components/layout/Sidebar.tsx`
  - Add "Calendar" to technician+ section
  - Add "My Appointments" to employee/general section
  - Add "Availability" to settings section for technician+

---

## Phase 7: i18n

### 7. Add translation keys
- [x] Edit `web/app/src/locales/en.ts`
- [x] Edit `web/app/src/locales/es.ts`
  - ~60 keys covering:
    - `nav.calendar`, `nav.my_appointments`, `nav.availability_settings`
    - `page.calendar.*` — week view, navigation
    - `page.availability.*` — settings form
    - `page.my_appointments.*` — list view, actions
    - `page.request_detail.appointments.*` — section title, schedule button
    - `enum.appointment_status.*` — PENDING, CONFIRMED, etc.

---

## Phase 8: Verification

### 8. Verify
- [x] TypeScript compilation: `cd web/app && npx tsc --noEmit`
- [x] Build succeeds: `cd web/app && npm run build`

---

## Final Checklist

- [x] 3 new pages created
- [x] 1 existing page edited (RequestDetailPage)
- [x] 3 routes added
- [x] 3 nav items added
- [x] ~60 i18n keys per language
- [x] TypeScript compiles
- [x] Build succeeds
