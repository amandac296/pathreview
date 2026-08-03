## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/92

**Issue title:** Profile creation form doesn't show a loading state while the resume is being uploaded

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There's an issue with the front-end of the website where when a user submits their profile form, there's no visible indicator while the resume is being uploaded so the user doesn't know if their form went through or not. This can cause the user to continuously press the submit button multiple times which can cause the form to duplicate multiple times. Some relevant files include frontend/src/components/ProfileForm.tsx and 
frontend/src/hooks/useProfileSubmit.ts. A successful fix would be to disable to submit button from being able to be pressed while uploading a current form, maybe give a warning for if it's a duplicate, and also to let the user know that their form is in the loading state of uploading.

**Branch name:** fix/92-profile-form-loading-state

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/amandac296/pathreview/commit/cdf7f98

**Reproduction summary:** When trying to see what happens on the normal UI, it doesn't really fire more than one POST /profiles request. (apparently react can disable the button faster than a human can click). So, I created an integration test that checks if only 1 profile should be created which fails so it confirms there's a bug.

**PLAN.md link:** https://github.com/amandac296/pathreview/blob/fix/92-profile-form-loading-state/PLAN.md

**Walkthrough video (recommended):** [link here, or leave blank]

**Blockers or open questions:**
[anything uncertain going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Added a unique constraint on `profiles.user_id` in `core/models/profile.py`,the Alembic migration (`003_add_unique_constraint_on_profiles_user_id.py`) with a cleanup step that deletes duplicate rows (keeping the newest per user) before adding the constraint, added `IntegrityError` -> `409 Conflict` handling in `create_profile_endpoint`,

**Next steps:**
Check make test unit and the added integration test pass with no new errors. Make sure make check passes with the newly added files. Update `test_profile_duplicate_submission.py` to check that one submission succeeds, the other raises `IntegrityError`, exactly one row remains. 

**Blockers:**
Black can't run locally — Python 3.12.5 hits a known AST-safety-check bug in Black (needs 3.12.6+ or 3.12.4). 

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/92-profile-form-loading-state`

**What you built:**
Added a unique constraint on profiles.user_id so a user can only ever have one profile row. The migration deletes any existing duplicate rows (keeping the newest per user) before adding the constraint, and `create_profile_endpoint` now catches the resulting `IntegrityError` and returns `409 Conflict` instead of silently creating a second row (previously a generic 500).

**Tests added or updated:**
`tests/integration/test_profile_duplicate_submission.py` — updated the Week 8 reproduction test to assert the fixed behavior: of two concurrent submissions for the same user, exactly one succeeds and the other raises `IntegrityError`, leaving exactly one row in the database.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
N/A

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The planning part (week 2) was harder than I expected where I had to reproduce the error and get a good picture of the overall code.

**What did you learn about working in a large codebase?**
The importance of labeling/commenting code and making sure it's consistent throuhgout the codebase as well as making sure if you're working on a large codebase collaboratively, to make sure the commits and pushes are specific and in depth.

**How did AI tools help — and where did they fall short?**
It was useful in helping me understand the codebase quicker than if I were to do it by myself. I also learned about new libraries and new software that I would've needed longer time on for if not for AI. I think it falls short in writing our code as AI is not always consistent and could also midunderstand what we want it to really do.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
My issue got closed so I probably should've started over but I was already committed to the bug. I also think my implmentation could be better and more organized. 

**What are you most proud of from this module?**
I'm most proud of familiarizing myself with new concepts with AI and learning about coding industry standards on a large codebase collaboratively with other people.