"""
© Ocado Group
Created on 14/03/2025 at 15:34:28(+00:00).

The min settings required to manage the `codeforlife.user` Django app-module.
"""

import os

os.environ["SERVICE_NAME"] = "example-service"

# pylint: disable-next=wildcard-import,unused-wildcard-import,wrong-import-position
from codeforlife.settings import *

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "codeforlife.user",
    "codeforlife.legacy",  # TODO: remove this once legacy system is removed
]

MIDDLEWARE = [
    "codeforlife.middlewares.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "codeforlife.user.urls"
