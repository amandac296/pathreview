"""Integration test reproducing issue #92.

The profile-creation form had no server-side guard against duplicate
submissions: core/services/profile_service.py's create_profile() inserted
unconditionally, with no uniqueness check or idempotency key. If two
requests for the same user overlapped (slow network, double-click, retry),
both succeeded and two rows got created.

Fixed via a DB-level unique constraint on profiles.user_id
(alembic/versions/003_add_unique_constraint_on_profiles_user_id.py). This
test now asserts that of two concurrent submissions, exactly one succeeds
and the other raises IntegrityError, leaving exactly one row behind.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.schemas.profile import ProfileCreate
from core.database import AsyncSessionLocal
from core.models.profile import Profile
from core.models.user import User
from core.services.profile_service import create_profile


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_submissions_do_not_create_duplicate_profiles() -> None:
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"repro-{uuid.uuid4()}@example.com",
            hashed_password="not-a-real-hash",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user_id = user.id

    data = ProfileCreate(github_username="octocat", portfolio_url=None)

    async def submit() -> Profile:
        async with AsyncSessionLocal() as db:
            return await create_profile(db=db, user_id=user_id, data=data)

    try:
        results = await asyncio.gather(submit(), submit(), return_exceptions=True)

        successes = [r for r in results if isinstance(r, Profile)]
        failures = [r for r in results if isinstance(r, IntegrityError)]

        assert (
            len(successes) == 1
        ), f"Expected exactly 1 successful submission, got {len(successes)}"
        assert (
            len(failures) == 1
        ), f"Expected exactly 1 submission to fail with IntegrityError, got {len(failures)}"

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Profile).where(Profile.user_id == user_id))
            profiles = result.scalars().all()

        assert len(profiles) == 1, (
            f"Expected exactly 1 profile for the user, found {len(profiles)} — "
            "two concurrent submissions were not deduplicated (issue #92)"
        )
    finally:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Profile).where(Profile.user_id == user_id))
            for profile in result.scalars().all():
                await db.delete(profile)
            db_user = await db.get(User, user_id)
            if db_user:
                await db.delete(db_user)
            await db.commit()
