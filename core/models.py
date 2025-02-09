from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from core.base_models import BaseModel
from core.model_utils import generate_random_key
from statushen.utils import get_statushen_logger

logger = get_statushen_logger(__name__)


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=10, unique=True, default=generate_random_key)

    subscription = models.ForeignKey(
        "djstripe.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profile",
        help_text="The user's Stripe Subscription object, if it exists",
    )
    customer = models.ForeignKey(
        "djstripe.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profile",
        help_text="The user's Stripe Customer object, if it exists",
    )

    def track_state_change(self, to_state, metadata=None):
        from_state = self.current_state

        if from_state != to_state:
            logger.info(
                "Tracking State Change", from_state=from_state, to_state=to_state, profile_id=self.id, metadata=metadata
            )
            ProfileStateTransition.objects.create(
                profile=self, from_state=from_state, to_state=to_state, backup_profile_id=self.id, metadata=metadata
            )

    @property
    def current_state(self):
        if not self.state_transitions.all().exists():
            return ProfileStates.STRANGER
        latest_transition = self.state_transitions.latest("created_at")
        return latest_transition.to_state


class ProfileStates(models.TextChoices):
    STRANGER = "stranger"
    SIGNED_UP = "signed_up"
    SUBSCRIBED = "subscribed"
    CANCELLED = "cancelled"
    CHURNED = "churned"
    ACCOUNT_DELETED = "account_deleted"


class ProfileStateTransition(BaseModel):
    profile = models.ForeignKey(
        Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name="state_transitions"
    )
    from_state = models.CharField(max_length=255, choices=ProfileStates.choices)
    to_state = models.CharField(max_length=255, choices=ProfileStates.choices)
    backup_profile_id = models.IntegerField()
    metadata = models.JSONField(null=True, blank=True)


class BlogPost(BaseModel):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=250)
    tags = models.TextField()
    content = models.TextField()
    icon = models.ImageField(upload_to="blog_post_icons/", blank=True)
    image = models.ImageField(upload_to="blog_post_images/", blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post", kwargs={"slug": self.slug})


class Project(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    url = models.URLField(blank=True)
    public = models.BooleanField(default=False)
    icon = models.ImageField(upload_to="project_icons/", blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project-status-page", kwargs={"slug": self.slug})

    @property
    def icon_url(self):
        if self.icon and hasattr(self.icon, "url"):
            return self.icon.url
        return static("vendors/images/logo.png")


class Service(BaseModel):
    class ServiceType(models.TextChoices):
        WEBSITE = "WEBSITE", "Website"
        API = "API", "API"

    class HttpMethod(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"

    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=250)
    type = models.CharField(max_length=20, choices=ServiceType.choices, default=ServiceType.WEBSITE)
    url = models.URLField(max_length=500, blank=True)
    check_interval = models.PositiveIntegerField(default=5, help_text="Check interval in minutes")

    # API-specific fields
    http_method = models.CharField(max_length=10, choices=HttpMethod.choices, default=HttpMethod.GET)
    request_headers = models.JSONField(blank=True, null=True, help_text="Headers to be sent with the API request")
    request_body = models.TextField(blank=True, null=True, help_text="Body of the API request")
    expected_status_code = models.PositiveIntegerField(blank=True, null=True, help_text="Expected HTTP status code")
    expected_response_content = models.TextField(
        blank=True, null=True, help_text="Expected content in the API response"
    )

    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["project", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def clean(self):
        super().clean()
        if self.type == self.ServiceType.API:
            if not self.url:
                raise ValidationError("URL is required for API services")
            URLValidator()(self.url)

    def get_check_params(self):
        if self.type == self.ServiceType.API:
            return {
                "url": self.url,
                "method": self.http_method,
                "headers": self.request_headers or {},
                "body": self.request_body,
                "expected_status_code": self.expected_status_code,
                "expected_response_content": self.expected_response_content,
            }
        # Add logic for other service types if needed
        return {}


class ServiceStatus(BaseModel):
    class StatusChoices(models.TextChoices):
        UP = "UP", "Up"
        DOWN = "DOWN", "Down"
        DEGRADED = "DEGRADED", "Degraded"
        UNKNOWN = "UNKNOWN", "Unknown"

    service = models.ForeignKey("Service", on_delete=models.CASCADE, related_name="statuses")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.UNKNOWN)
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    status_code = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-checked_at"]
        get_latest_by = "checked_at"

    def __str__(self):
        return f"{self.service.name} - {self.status} at {self.checked_at}"

    @property
    def is_up(self):
        return self.status == self.StatusChoices.UP

    @property
    def is_down(self):
        return self.status == self.StatusChoices.DOWN

    @property
    def is_degraded(self):
        return self.status == self.StatusChoices.DEGRADED
