# E8: Seed Data & Demo — Requirements

## Goal

Provide a one-command setup that populates the database with realistic demo data, enabling developers and stakeholders to explore all features without manual data entry.

## Requirements

### R1: Seed Script
- Python script that inserts demo data directly via SQLAlchemy models
- Idempotent: running twice does not create duplicates (clears existing demo data first)
- Creates realistic, interconnected data across all tables
- Uses ULID IDs and proper foreign key references

### R2: Demo Data Coverage
- **3 companies** with email domains (TechCorp, FinanceHub, HealthCare Plus)
- **1 super admin** (no company)
- **Per company**: 1 admin, 2 technicians, 5 employees (across departments)
- **Per company**: 3-4 departments (Engineering, Sales, HR, IT, Operations)
- **Per company**: 15-20 assets (mix of types and statuses)
- **Per company**: 10-15 service requests (various statuses, types, priorities)
- **Request extras**: comments, internal notes, request events on some requests
- **Asset events**: creation and assignment events
- **Notifications**: 3-5 per user (mix of read/unread)
- **Reports**: 2-3 per company (completed, pending, failed)

### R3: Makefile Integration
- `make seed` — run the seed script
- `make demo-reset` — drop all data and re-seed (migrations + seed)

### R4: Demo Walkthrough Documentation
- Step-by-step guide for exploring the demo
- Login credentials for each role
- Feature highlights per role

## Dependencies
- All migrations applied (E0-E6)
- Docker Compose services running (PostgreSQL)
