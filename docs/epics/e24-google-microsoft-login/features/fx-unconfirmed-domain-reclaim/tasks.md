# Tasks: Fx - Unconfirmed Domain Reclaim

## Summary
Add `email_verified_at` to User. Mark it on first magic link verification (and later OAuth login). Allow re-registering a company domain if no user of that company has ever confirmed.

---

## Backend Tasks

- [x] **Fx-1** Add `email_verified_at: Optional[datetime]` to `User` dataclass (`src/auth_bc/user/domain/entities.py`)
- [x] **Fx-2** Add `email_verified_at` column to `UserModel` (`src/auth_bc/user/infrastructure/models.py`) — nullable, no default
- [x] **Fx-3** Update `_to_entity()` and `save()` in `UserRepository` to include `email_verified_at`
- [x] **Fx-4** Alembic migration: `ADD COLUMN email_verified_at TIMESTAMP NULL` on `users` table
- [x] **Fx-5** Mark `email_verified_at = datetime.now(utc)` in `VerifyMagicLinkService` on first login (only if currently `None`)
- [x] **Fx-6** Add `has_any_verified_user_in_company(company_id: str) -> bool` and `delete_by_company(company_id: str)` to `UserRepositoryInterface`
- [x] **Fx-7** Implement both methods in `UserRepository`
- [x] **Fx-8** In `CreateCompanyCommandHandler`: when domain taken by unconfirmed company → delete it and proceed with new registration
- [x] **Fx-9** Add `delete(company_id: str)` to `CompanyRepositoryInterface` + `CompanyRepository` (deletes domains + company)

## Tests

- [ ] **Fx-T1** Unit: `VerifyMagicLinkService` sets `email_verified_at` on first login, does not overwrite on subsequent logins
- [ ] **Fx-T2** Unit: `CreateCompanyCommandHandler` — domain taken by unconfirmed company → reclaim succeeds
- [ ] **Fx-T3** Unit: `CreateCompanyCommandHandler` — domain taken by confirmed company → raises `DomainAlreadyTakenError`
- [ ] **Fx-T4** Integration: `POST /api/v1/register` — re-register same domain after no confirmation → 201
- [ ] **Fx-T5** Integration: `POST /api/v1/register` — re-register same domain after confirmation → 409
