"""Tests for profile_service.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from api.schemas.profile import ProfileCreate, ProfileUpdate
from core.services.profile_service import (
    create_profile,
    delete_profile,
    get_profile,
    update_profile,
)


@pytest.mark.unit
class TestProfileService:
    """Test suite for profile_service module."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = None
        return profile

    @pytest.mark.asyncio
    async def test_create_profile_calls_db_add_commit_refresh(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test create_profile persists the new profile."""
        user_id = uuid4()
        data = ProfileCreate(github_username="octocat", portfolio_url=None)

        with patch("core.services.profile_service.Profile"):
            await create_profile(db=mock_db_session, user_id=user_id, data=data)

            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile_passes_resume_fields_through(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test create_profile forwards resume_filename/resume_text to the model."""
        user_id = uuid4()
        data = ProfileCreate(github_username="octocat", portfolio_url=None)

        with patch("core.services.profile_service.Profile") as mock_profile_cls:
            await create_profile(
                db=mock_db_session,
                user_id=user_id,
                data=data,
                resume_filename="resume.pdf",
                resume_text="Some resume text",
            )

            call_kwargs = mock_profile_cls.call_args[1]
            assert call_kwargs["user_id"] == user_id
            assert call_kwargs["github_username"] == "octocat"
            assert call_kwargs["resume_filename"] == "resume.pdf"
            assert call_kwargs["resume_text"] == "Some resume text"

    @pytest.mark.asyncio
    async def test_create_profile_raises_integrity_error_on_duplicate(
        self, mock_db_session: AsyncMock
    ) -> None:
        """A second profile for the same user must surface IntegrityError, not swallow it.

        This is the regression case for issue #92: the unique constraint on
        profiles.user_id causes db.commit() to raise IntegrityError, and
        create_profile must let that propagate so the route layer can turn it
        into a 409 instead of silently creating a duplicate row.
        """
        user_id = uuid4()
        data = ProfileCreate(github_username="octocat", portfolio_url=None)
        mock_db_session.commit = AsyncMock(
            side_effect=IntegrityError("duplicate key", params=None, orig=Exception())
        )

        with patch("core.services.profile_service.Profile"), pytest.raises(IntegrityError):
            await create_profile(db=mock_db_session, user_id=user_id, data=data)

    @pytest.mark.asyncio
    async def test_get_profile_returns_profile_for_correct_owner(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test get_profile returns the profile when id and user_id both match."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_profile(mock_db_session, mock_profile.id, mock_profile.user_id)

        assert result == mock_profile

    @pytest.mark.asyncio
    async def test_get_profile_returns_none_for_wrong_owner(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_profile returns None when the profile isn't owned by user_id."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_profile(mock_db_session, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_update_profile_returns_none_when_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test update_profile returns None instead of raising when profile is missing."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await update_profile(
            mock_db_session,
            profile_id=uuid4(),
            user_id=uuid4(),
            data=ProfileUpdate(github_username="new-name"),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_profile_only_overwrites_provided_fields(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test update_profile leaves fields untouched when not present in the update payload."""
        mock_profile.github_username = "old-name"
        mock_profile.portfolio_url = "https://old.example.com"

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await update_profile(
            mock_db_session,
            profile_id=mock_profile.id,
            user_id=mock_profile.user_id,
            data=ProfileUpdate(github_username="new-name", portfolio_url=None),
        )

        assert result is not None
        assert result.github_username == "new-name"
        assert result.portfolio_url == "https://old.example.com"

    @pytest.mark.asyncio
    async def test_delete_profile_returns_false_when_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test delete_profile returns False instead of raising when profile is missing."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await delete_profile(mock_db_session, profile_id=uuid4(), user_id=uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_profile_deletes_reviews_sources_and_profile(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test delete_profile cascades to reviews and ingested sources before deleting it."""
        get_result = Mock()
        get_result.scalars.return_value.first.return_value = mock_profile

        empty_result = Mock()
        empty_result.scalars.return_value.all.return_value = []

        mock_db_session.execute = AsyncMock(side_effect=[get_result, empty_result, empty_result])

        result = await delete_profile(
            mock_db_session, profile_id=mock_profile.id, user_id=mock_profile.user_id
        )

        assert result is True
        mock_db_session.delete.assert_any_call(mock_profile)
        mock_db_session.commit.assert_called_once()
