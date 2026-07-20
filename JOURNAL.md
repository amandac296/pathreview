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

**Reproduction commit link:** [paste link here once pushed]

**Reproduction summary:** When trying to see what happens on the normal UI, it doesn't really fire more than one POST /profiles request. (apparently react can disable the button faster than a human can click). So, I decided to fire 2 POST /profiles requests from the browser console with the same github username and the results showed that they both returned 200 OK with 2 diff profile ids even though they have the same user_id.

**PLAN.md link:** [paste link here]

**Walkthrough video (recommended):** [link here, or leave blank]

**Blockers or open questions:**
[anything uncertain going into Week 9, or leave blank]