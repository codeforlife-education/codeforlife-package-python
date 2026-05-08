"""
© Ocado Group
Created on 12/02/2025 at 16:49:05(+00:00).

This file contains all the settings Django supports out of the box.
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os

from django.utils.translation import gettext_lazy as _

from .. import TEMPLATES_DIR
from ._secrets import get_secret
from .custom import (
    ENV,
    LOG_LEVEL,
    SERVICE_BASE_DIR,
    SERVICE_BASE_URL,
    SERVICE_DOMAIN,
    SERVICE_EXTERNAL_DOMAIN,
    SERVICE_NAME,
    SERVICE_SITE_URL,
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.getenv("DEBUG", "1")))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret("SECRET_KEY", "replace-me")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_secret("DB_NAME", SERVICE_NAME),
        "USER": get_secret("DB_USER", "root"),
        "PASSWORD": get_secret("DB_PASSWORD", "password"),
        "HOST": get_secret("DB_HOST", "db"),
        "PORT": int(get_secret("DB_PORT", "5432")),
        "ATOMIC_REQUESTS": True,
    }
}

# Application definition

MIDDLEWARE = [
    "codeforlife.middlewares.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Required to use the admin app.
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Auth
# https://docs.djangoproject.com/en/5.1/topics/auth/default/

LOGIN_URL = f"{SERVICE_BASE_URL}/session/expired/"

# Authentication backends
# https://docs.djangoproject.com/en/5.1/ref/settings/#authentication-backends

AUTHENTICATION_BACKENDS = [
    "codeforlife.user.auth.backends.EmailBackend",
    "codeforlife.user.auth.backends.OtpBackend",
    "codeforlife.user.auth.backends.OtpBypassTokenBackend",
    "codeforlife.user.auth.backends.StudentBackend",
    "codeforlife.user.auth.backends.StudentAutoBackend",
    "codeforlife.user.auth.backends.GoogleBackend",
]

# Sessions
# https://docs.djangoproject.com/en/5.1/topics/http/sessions/

SESSION_ENGINE = "codeforlife.user.models.session"
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_NAME = "session_key"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = SERVICE_DOMAIN

# Security
# https://docs.djangoproject.com/en/5.1/topics/security/

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-gb"
LANGUAGES = [("en-gb", _("English"))]
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# CSRF
# https://docs.djangoproject.com/en/5.1/ref/csrf/

CSRF_COOKIE_NAME = f"{SERVICE_NAME}_csrftoken"
CSRF_COOKIE_DOMAIN = SERVICE_EXTERNAL_DOMAIN
CSRF_TRUSTED_ORIGINS = [SERVICE_SITE_URL]
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SECURE = True

# Logging
# https://docs.djangoproject.com/en/5.1/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            **(
                {"format": "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"}
                if ENV == "local"
                else {"class": "codeforlife.logging.JsonFormatter"}
            ),
            "style": "%",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
}

# URLs
# https://docs.djangoproject.com/en/5.1/ref/settings/#root-urlconf

ROOT_URLCONF = "src.urls"

# App
# https://docs.djangoproject.com/en/5.1/ref/settings/#wsgi-application

WSGI_APPLICATION = "application.django_wsgi"

# Custom user model
# https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#auth-custom-user

AUTH_USER_MODEL = "user.User"

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

# TODO: compare Django's default common password validator with our own and
#  decide which to keep
# NOTE: Django's common password validator, while similar to ours,
# seems based on a deprecated list of passwords.
# codeforlife.user.auth.password_validators.CommonPasswordValidator
# pylint: disable=line-too-long
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "codeforlife.user.auth.password_validators.TeacherPasswordValidator",
    },
    {
        "NAME": "codeforlife.user.auth.password_validators.StudentPasswordValidator",
    },
    {
        "NAME": "codeforlife.user.auth.password_validators.IndependentPasswordValidator",
    },
]
# pylint: enable=line-too-long

# Installed Apps
# https://docs.djangoproject.com/en/5.1/ref/settings/#installed-apps

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "src",
    "codeforlife.user",
    "corsheaders",
    "rest_framework",
    "django_filters",
]

# Templates
# https://docs.djangoproject.com/en/5.1/ref/templates/

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Generate relative path to "codeforlife/templates".
            os.path.relpath(TEMPLATES_DIR, SERVICE_BASE_DIR)
        ],
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
