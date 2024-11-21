import requests
from django.conf import settings
from django.db.models import DurationField, ExpressionWrapper, F, Max, Q
from django.utils import timezone
from django_q.tasks import async_task

from core.models import Service, ServiceStatus
from statushen.utils import get_statushen_logger

logger = get_statushen_logger(__name__)


def add_email_to_buttondown(email, tag):
    data = {
        "email_address": str(email),
        "metadata": {"source": tag},
        "tags": [tag],
        "referrer_url": "https://statushen.com",
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

    services_to_check = (
        Service.objects.filter(is_active=True)
        .annotate(
            last_checked=Max("statuses__checked_at"),
            check_interval_duration=ExpressionWrapper(
                F("check_interval") * timezone.timedelta(minutes=1), output_field=DurationField()
            ),
        )
        .filter(Q(last_checked__isnull=True) | Q(last_checked__lte=now - F("check_interval_duration")))
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

    status = "UNKNOWN"

    logger.info("Initiating check", service_id=service.id, service_type=service.type)

    try:
        if service.type == Service.ServiceType.API:
            status, response_time, status_code, error_message = check_api_service(service)
        else:
            status, response_time, status_code, error_message = check_website_service(service)

        ServiceStatus.objects.create(
            service=service,
            status=status,
            response_time=response_time,
            status_code=status_code,
            error_message=error_message,
        )
    except Exception as e:
        logger.error("[Check Service] Failed", service_id=service.id, error=str(e))
        ServiceStatus.objects.create(service=service, status=ServiceStatus.StatusChoices.DOWN, error_message=str(e))

    return f"Check complete. Status: {status}"


def check_website_service(service):
    """
    Check a website service.
    """
    response = requests.get(service.url, timeout=10)

    if response.ok:
        status = ServiceStatus.StatusChoices.UP
    else:
        status = ServiceStatus.StatusChoices.DOWN

    return status, response.elapsed.total_seconds() * 1000, response.status_code, None


def check_api_service(service):
    """
    Check an API service.
    """
    method = service.http_method or "GET"
    headers = service.request_headers
    data = service.request_body

    try:
        response = requests.request(method, service.url, headers=headers, data=data, timeout=10)

        status = ServiceStatus.StatusChoices.UP
        error_message = None

        # Check expected status code
        if service.expected_status_code and response.status_code != service.expected_status_code:
            status = ServiceStatus.StatusChoices.DOWN
            error_message = f"Unexpected status code: {response.status_code}"

        # Check expected response content
        if service.expected_response_content and service.expected_response_content not in response.text:
            status = ServiceStatus.StatusChoices.DOWN
            error_message = "Expected content not found in response"

        logger.info(
            "API Status Check Successfull",
            status=status,
            time=response.elapsed.total_seconds() * 1000,
            status_code=response.status_code,
            error_message=error_message,
        )

        return status, response.elapsed.total_seconds() * 1000, response.status_code, error_message

    except requests.RequestException as e:
        return ServiceStatus.StatusChoices.DOWN, None, None, str(e)
