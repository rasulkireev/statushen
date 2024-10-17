import requests
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Max, F, ExpressionWrapper, DurationField
from django_q.tasks import async_task

from core.models import Service, ServiceStatus
from statushen.utils import get_statushen_logger

logger = get_statushen_logger(__name__)

def add_email_to_buttondown(email, tag):
    data = {
        "email_address": str(email),
        "metadata": {"source": tag},
        "tags": [tag],
        "referrer_url": "https://statushen.app",
        "subscriber_type": "regular",
    }

    r = requests.post(
        "https://api.buttondown.email/v1/subscribers",
        headers={"Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"},
        json=data,
    )

    return r.json()


def schedule_service_checks():
    """
    Schedule service checks for services that need to be checked.
    This function should be run periodically (e.g., every minute) to ensure timely checks.
    """
    now = timezone.now()

    services_to_check = Service.objects.filter(is_active=True).annotate(
        last_checked=Max('statuses__checked_at'),
        check_interval_duration=ExpressionWrapper(
            F('check_interval') * timezone.timedelta(minutes=1),
            output_field=DurationField()
        )
    ).filter(
        Q(last_checked__isnull=True) |
        Q(last_checked__lte=now - F('check_interval_duration'))
    )

    count = 0
    for service in services_to_check:
        async_task(check_service, service.id, group=f"{service.project.name} - {service.name}")
        count += 1

    return f"Scheduled {count} checks out of {services_to_check.count()} required."


def check_service(service_id):
    """
    Perform a check on a specific service and record the status.
    """
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return

    try:
        response = requests.get(service.url, timeout=10)

        if response.ok:
            status = ServiceStatus.StatusChoices.UP
        else:
            status = ServiceStatus.StatusChoices.DOWN

        ServiceStatus.objects.create(
            service=service,
            status=status,
            response_time=response.elapsed.total_seconds() * 1000,
            status_code=response.status_code
        )
    except requests.RequestException as e:
        # Handle network errors, timeouts, etc.
        ServiceStatus.objects.create(
            service=service,
            status=ServiceStatus.StatusChoices.DOWN,
            error_message=str(e)
        )

    return f"Check complete. Status: {status}"
