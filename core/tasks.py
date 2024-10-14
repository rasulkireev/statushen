import requests
from django.conf import settings

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

