"""
Django settings for statushen project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path
import environ
import structlog
import sentry_sdk



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

ENVIRONMENT = env("ENVIRONMENT")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "webpack_boilerplate",
    "widget_tweaks",
    "anymail",
    "djstripe",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",

    "django_q",
    "django_extensions",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "statushen.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR.joinpath("frontend", "templates"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "statushen.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": env.db_url(),
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR.joinpath("static/")

STATICFILES_DIRS = [
    BASE_DIR.joinpath("frontend/build"),
]

bucket_name = f"statushen-{ENVIRONMENT}"

STORAGES = {
    "default": {
        "BACKEND": "statushen.storages.CustomS3Boto3Storage",
        "OPTIONS": {
          "bucket_name": bucket_name,
          "default_acl": "public-read",
          "region_name": "eu-east-1",
          "endpoint_url": env("AWS_S3_ENDPOINT_URL"),
          "access_key": env("AWS_ACCESS_KEY_ID"),
          "secret_key": env("AWS_SECRET_ACCESS_KEY"),
          "querystring_auth": False,
          "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = f"{env('AWS_S3_ENDPOINT_URL')}/{bucket_name}/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

WEBPACK_LOADER = {
    "MANIFEST_FILE": BASE_DIR.joinpath("frontend/build/manifest.json"),
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
SITE_ID = 1

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGOUT_REDIRECT_URL = "home"

ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_FORMS = {
    "signup": "core.forms.CustomSignUpForm",
    "login": "core.forms.CustomLoginForm",
}
if ENVIRONMENT == "prod":
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "VERIFIED_EMAIL": True,
        "EMAIL_AUTHENTICATION": True,
        "AUTO_SIGNUP": True,
        "APP": {
            "client_id": env("GITHUB_CLIENT_ID"),
            "secret": env("GITHUB_CLIENT_SECRET"),
        },
    },

}

ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": "mg.statushen.app",
}
DEFAULT_FROM_EMAIL = "Rasul from StatusHen <hello@statushen.app>"
SERVER_EMAIL = "StatusHen Errors <error@statushen.app>"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "mailhog"  # Use the service name from docker-compose
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
else:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

Q_CLUSTER = {
    "name": "statushen-q",
    "timeout": 90,
    "retry": 120,
    "workers": 4,
    "max_attempts": 2,
    "redis": env("REDIS_URL"),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(key_order=["timestamp", "level", "event", "logger"]),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
            "level": "DEBUG",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "statushen": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

if ENVIRONMENT == "prod":
    LOGGING["loggers"]["statushen"]["level"] = env("DJANGO_LOG_LEVEL", default="INFO")
    LOGGING["loggers"]["statushen"]["handlers"] = ["json_console"]
    LOGGING["loggers"]["django_structlog"]["handlers"] = ["json_console"]

SENTRY_DSN = env("SENTRY_DSN")
if ENVIRONMENT == "prod" and SENTRY_DSN:
    sentry_sdk.init(dsn=env("SENTRY_DSN"))

BUTTONDOWN_API_KEY=env("BUTTONDOWN_API_KEY")

STRIPE_LIVE_SECRET_KEY = env("STRIPE_LIVE_SECRET_KEY")
STRIPE_TEST_SECRET_KEY = env("STRIPE_TEST_SECRET_KEY")

STRIPE_LIVE_MODE = False
STRIPE_SECRET_KEY = STRIPE_TEST_SECRET_KEY
if ENVIRONMENT == "prod":
    STRIPE_LIVE_MODE = True
    STRIPE_SECRET_KEY = STRIPE_LIVE_SECRET_KEY

DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_WEBHOOK_SECRET")
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
