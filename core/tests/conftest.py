import shutil
import tempfile

import pytest
from django.contrib.auth import get_user_model

from core.models import Profile, Project

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")


@pytest.fixture
def profile(user):
    return Profile.objects.create(
        user=user,
    )


@pytest.fixture
def project(profile):
    return Project.objects.create(
        profile=profile, name="Test Project", slug="test-project", url="https://example.com", public=True
    )


@pytest.fixture(scope="session")
def temp_media_root():
    """Create a temporary directory for media files during testing."""
    media_root = tempfile.mkdtemp()
    yield media_root
    shutil.rmtree(media_root)


@pytest.fixture
def settings(settings, temp_media_root):
    """Override settings for testing."""
    settings.MEDIA_ROOT = temp_media_root
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    return settings
