"""Integration test reproducing issue #92.

The profile-creation form has no server-side guard against duplicate
submissions: core/services/profile_service.py's create_profile() inserts
unconditionally, with no uniqueness check or idempotency key. If two
requests for the same user overlap (slow network, double-click, retry),
both succeed and two rows get created.

This test currently FAILS on purpose: it documents the bug by asserting
the behavior a fix should guarantee (only one profile per submission),
which the current implementation does not provide. Once a fix lands, this
test should pass without modification.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import select

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
        await asyncio.gather(submit(), submit())

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
