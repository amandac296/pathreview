## Solution plan

**Issue:** #92 - Profile creation form doesn't show a loading state while the resume is being uploaded 

### Understand
The front end already kind of disables the submit button and shows a spinner while `isLoading` is true (ProfileForm.tsx, useProfileSubmit.ts). The real issue can be seen from the reproduction test which is on the back end and it shows that when the user submit two forms with the same github name, it creates two different profile ids but it has the same username_id. 

The expected behavior: send an error so that the application knows its the same user with the same form and it should not go through with different user_id.

### Map
Files to touch:
- `core/models/profile.py` — add the unique constraint on `user_id` to the model
- `alembic/versions/` — new migration file applying that constraint (see `002_add_error_message_to_reviews.py` for the convention: revision id, `upgrade()`/`downgrade()`)
- `api/routes/profiles.py` — `create_profile_endpoint`, add the `IntegrityError` → 409 handling
- `tests/integration/test_profile_duplicate_submission.py` — update assertions to match the fixed behavior

Read for context, not modified:
- `frontend/src/components/ProfileForm.tsx` / `frontend/src/hooks/useProfileSubmit.ts` — already handle
  loading state and error display correctly; no frontend change needed for this fix
- `core/services/profile_service.py` — `create_profile()` itself doesn't need code changes, just the new
  constraint underneath it

### Plan
1. Add an Alembic migration that adds a unique constraint on `profiles.user_id` — one profile per user, enforced at the DB level.
2. Update `create_profile_endpoint` in `api/routes/profiles.py` to catch
   duplicate profiles specifically  and return `409 Conflict` with ("You already have a profile") instead of a generic 500.
3. Update the integration test file to run the two concurrent `create_profile()` calls to check that exactly one succeeds and the other raises `IntegrityError`, and assert only 1 row exists in `profiles`.
4. Confirm the test now passes and nothing else regresses.
5. `make check` before opening the PR.

### Inputs & outputs
Input: `user_id` + `ProfileCreate` data (`github_username`, `portfolio_url`) passed to `create_profile()` — signature unchanged.
New DB behavior: insert now raises `IntegrityError` if a profile already exists for that `user_id`, instead of silently succeeding.
Output change: `create_profile_endpoint` returns `409 Conflict` with a clear message on duplicate, instead of a 200 with a second profile ID.

### Risks & unknowns
- Scope decision made: hard-reject (409) rather than upsert. This is simpler and matches "one profile per user," but means a user who already has a profile has no way to update it through the UI at all right now (in edge case).
- 409 vs 422: went with 409 since this is a conflict with existing state, not a validation error on the submitted data.

### Edge cases
- A user's first submission fails validation (bad file type) → no row was created → their retry should succeed normally, since the constraint only blocks a second *successful* insert.
- Users with no `github_username` (nullable field) aren't affected, since the constraint is on `user_id` alone rather than including `github_username`.
- No UI path for them to actually edit their existing profile (`PUT /profiles/{id}` exists in the backend but nothing calls it from the frontend). 
