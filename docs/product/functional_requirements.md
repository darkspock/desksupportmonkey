# DeskSupportMonkey - Functional Requirements

## Overview

Internal web application for IT asset management and service requests. Employees submit requests to the IT department (hardware issues, new equipment, onboarding) and track their status in real time. IT technicians manage a prioritized queue of requests and maintain an inventory of all company equipment.

---

## Roles

| Role | Scope | Description |
|---|---|---|
| **Super Admin** | Platform | Creates and manages companies. Platform-level access |
| **Admin** | Company | Manages users, departments, and configuration for their company |
| **Technician** | Company | Processes requests, manages inventory, updates request status |
| **Employee** | Company | Submits requests, views their equipment and request status |

---

## Module 0: Company Management (Super Admin)

### 0.1 Company Registry
- Super admin creates companies with: name, allowed email domain(s), contact person
- Each company has isolated data (assets, requests, users)
- Company statuses: `active`, `suspended`, `deactivated`

### 0.2 Company User Management
- Super admin can assign the initial admin for each company
- From there, the company admin manages their own users

---

## Authentication

- Magic link via email (no passwords)
- User enters their email address; if the domain matches the configured company domain(s), the system sends a login link
- The link is valid for 24 hours and single-use
- If the email domain does not match, access is denied with a message: "Only corporate email addresses are allowed"
- On first login, the user is automatically created with the `employee` role within the company that owns that email domain; a company admin can later promote them to `technician` or `admin`
- Allowed email domains are configured per company (set by super admin when creating the company)
- For demos: a fake SMTP / console log mode so magic links can be tested without a real mail server

---

## Module 1: Asset Inventory

### 1.1 Asset Registry
- Register assets with: type (laptop, monitor, keyboard, mouse, headset, docking station, other), brand, model, serial number, purchase date, warranty expiration date, status
- Asset statuses: `in_stock`, `assigned`, `in_repair`, `decommissioned`
- Each asset optionally assigned to an employee and department

### 1.2 Asset History
- Every change on an asset is logged: assignment, unassignment, status change, repair, notes
- Full audit trail viewable per asset

### 1.3 Asset Search and Filters
- Search by serial number, model, type, status, assigned employee
- Filter by department, status, type

---

## Module 2: Employee Portal

### 2.1 My Equipment
- Employee sees all assets currently assigned to them

### 2.2 Submit Request
- Request types:
  - **Incident**: "Something is broken" (select affected asset, describe issue)
  - **New equipment**: "I need a monitor/keyboard/etc." (select type, justify)
  - **Onboarding**: "New hire starting on [date], needs full setup" (employee name, start date, department, role)
- Priority is set by the system based on type (incidents > onboarding > new equipment) but can be overridden by technicians

### 2.3 My Requests
- List of all submitted requests with current status
- Real-time status updates (WebSocket)
- Employee can add comments to open requests

---

## Module 3: Technician Panel

### 3.1 Request Queue
- Prioritized queue of all open requests (not a flat list - backed by a real message queue)
- Technician claims a request from the queue (self-assignment)
- Request state machine: `submitted` -> `in_review` -> `in_progress` -> `resolved` / `rejected`
- Technician adds internal notes and resolution comments
- On state change, employee is notified in real time

### 3.2 Inventory Management
- Full CRUD on assets
- Assign/unassign assets to employees
- Register new assets (individually or bulk import via CSV)
- Mark assets for repair or decommission

---

## Module 4: Admin Dashboard

### 4.1 Metrics
- Open requests count and breakdown by type and priority
- Average resolution time (overall and per technician)
- Assets by status (pie/bar chart)
- Requests over time (line chart)

### 4.2 Alerts
- Warranties expiring in the next 30/60/90 days
- Assets older than X years (configurable)
- Requests open longer than SLA threshold

### 4.3 User Management (Company Admin)
- View all users in the company
- Promote/demote roles (employee, technician, admin)
- Deactivate users (revoke access without deleting data)
- Assign users to departments

---

## Out of Scope (v1)

- Email/Slack notifications (only in-app)
- Mobile native app
- File attachments on requests
- SLA configuration UI (hardcoded thresholds)
- i18n (English only for v1)

---

See also: [Technical Requirements](technical_requirements.md)
