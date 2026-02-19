# Tasks: F2 — Profile Matching & Auto-Assignment Engine

## Implementation Tasks

### 1. AI Configuration Domain
- [x] Create `CompanyAssignmentAIConfig` entity in `src/company_bc/assignment_config/domain/entities.py`
  - Fields: `id`, `company_id` (unique), `provider` (AIProvider enum), `prompt_template`, `model`, `created_at`, `updated_at`
- [x] Create `AIProvider` enum (`OPENAI`, `GROQ`) in `src/company_bc/assignment_config/domain/enums.py`
- [x] Create `FallbackReason` enum (6 codes) in same file
- [x] Create repository + migration for `company_assignment_ai_configs` table

### 2. Configuration
- [x] Add `AISettings` to `core/config.py` with `OPENAI_API_KEY` and `GROQ_API_KEY`
- [x] Update `.env.example` with AI key placeholders

### 3. AI Config Commands/Queries
- [x] `SaveCompanyAIConfig(company_id, provider, prompt_template, model?)` — Admin only, upsert
- [x] `GetCompanyAIConfig(company_id)` — Admin only

### 4. AI Config API Endpoints
- [x] `PUT /api/v1/settings/assignment-ai` — save config
- [x] `GET /api/v1/settings/assignment-ai` — get config

### 5. AI Tie-Breaker Port + Adapters
- [x] Create `AITieBreakerPort` abstract class in `src/company_bc/equipment_profile/application/services/ai_tiebreaker.py`
  - `select_best_candidate(candidates, profile_item, prompt) -> asset_id`
- [x] Implement `OpenAIAdapter` — uses `OPENAI_API_KEY`, temperature=0, structured output
- [x] Implement `GroqAdapter` — uses `GROQ_API_KEY`, temperature=0, structured output
- [x] Implement deterministic fallback (oldest `purchase_date` wins)

### 6. Matching Service
- [x] Create `EquipmentProfileMatcher` in `src/company_bc/equipment_profile/application/services/matching.py`
  - Algorithm:
    1. Find active profile for (company, department, role) → `NO_ACTIVE_PROFILE`
    2. For each item: filter in-stock assets by type → `NO_STOCK_FOR_REQUIRED_TYPE`
    3. Apply spec filters (brand, model, ram, storage) → `SPEC_MISMATCH`
    4. Check assignable status → `ASSET_NOT_ASSIGNABLE`
    5. Single candidate → assign; multiple → AI tie-break → `AI_UNAVAILABLE` (fallback: oldest purchase_date)
    6. Any unresolved item → `MANUAL_REVIEW_REQUIRED`
  - Returns: `MatchResult` with matched assets list + fallback reasons list + AI decision metadata

### 7. Auto-Assignment Service
- [x] Create `AutoAssignService` in `src/company_bc/equipment_profile/application/services/auto_assign.py`
  - Orchestrates: load profile → call matcher → store metadata in `request.data`
- [x] Hook into request creation: after `CreateRequestCommand` for `new_equipment`/`onboarding`, call `AutoAssignService.attempt_assignment()`
  - Hooked at router level in `adapters/http/api/requests/routers.py` (not in command handler, to avoid cross-BC imports)

### 8. Unit Tests
- [x] `tests/unit/company_bc/equipment_profile/services/test_matching.py`
  - test_no_stock_fallback
  - test_spec_mismatch_fallback
  - test_single_candidate_deterministic
  - test_multiple_candidates_ai_tiebreak
  - test_ai_unavailable_deterministic_fallback
  - test_no_ai_deterministic
  - test_manual_review_partial_match
  - test_full_match_all_items
  - test_brand_filter_soft
- [x] `tests/unit/company_bc/equipment_profile/services/test_auto_assign.py`
  - test_auto_assign_success_stores_metadata
  - test_auto_assign_fallback_stores_reasons
  - test_auto_assign_skips_no_department
  - test_auto_assign_skips_no_role
- [x] `tests/unit/company_bc/assignment_config/test_commands.py`
  - test_save_config_creates_new
  - test_save_config_updates_existing
  - test_save_config_invalid_provider

### 9. Integration Tests
- [x] `tests/integration/test_auto_assignment.py`
  - test_request_creation_triggers_auto_assign
  - test_request_with_no_profile_stores_fallback
  - test_incident_request_no_auto_assign
- [x] `tests/integration/test_assignment_ai_settings.py`
  - test_save_and_get_config
  - test_update_config
  - test_invalid_provider
  - test_get_config_empty
  - test_employee_forbidden

### 10. Verification
- [x] Lint passes
- [x] New tests pass (16 unit + 8 integration)
- [x] Full unit suite passes (632 passed)
- [x] Full integration suite passes (157 passed, 1 pre-existing failure)

### 11. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F2 status to Done
