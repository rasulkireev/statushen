import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static


@pytest.mark.django_db
class TestProject:
    def test_project_creation(self, project):
        """Test that a project can be created with basic attributes"""
        assert project.name == "Test Project"
        assert project.slug == "test-project"
        assert project.url == "https://example.com"
        assert project.public is True
        assert project.icon == ""  # Empty by default

    def test_project_string_representation(self, project):
        """Test the string representation of a project"""
        assert str(project) == "Test Project"

    def test_project_absolute_url(self, project):
        """Test the get_absolute_url method"""
        expected_url = f"/status/{project.slug}/"  # adjust this based on your actual URL pattern
        assert project.get_absolute_url() == expected_url

    def test_icon_url_with_no_icon(self, project):
        """Test that icon_url returns default image when no icon is set"""
        assert project.icon_url == static("vendors/images/logo.png")

    def test_icon_url_with_icon(self, project):
        """Test that icon_url returns the correct URL when an icon is set"""
        # Create a simple image file
        image_content = (
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        image = SimpleUploadedFile(name="test_image.gif", content=image_content, content_type="image/gif")

        # Assign the image to the project
        project.icon = image
        project.save()

        # The URL should now point to the uploaded image
        assert project.icon_url == project.icon.url

    def test_icon_url_with_invalid_image(self, project):
        """Test that icon_url handles invalid image gracefully"""
        project.icon = "invalid_path"
        project.save()
        assert project.icon_url == static("vendors/images/logo.png")

    def test_project_profile_relationship(self, project, profile):
        """Test the relationship between Project and Profile"""
        assert project.profile == profile
        assert project in profile.projects.all()

    def test_project_timestamps(self, project):
        """Test that timestamps are automatically set"""
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.uuid is not None
