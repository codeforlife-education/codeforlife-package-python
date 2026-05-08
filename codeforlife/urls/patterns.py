"""
© Ocado Group
Created on 12/04/2024 at 14:42:20(+01:00).
"""

import typing as t

from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from ..views import CsrfCookieView, LogoutView, session_expired_view

UrlPatterns = t.List[t.Union[URLResolver, URLPattern]]


def get_urlpatterns(
    api_url_patterns: UrlPatterns,
    include_user_urls: bool = True,
) -> UrlPatterns:
    """Generate standard url patterns for each service.

    Args:
        api_urls_path: The path to the api's urls.
        include_user_urls: Whether or not to include the CFL's user urls.

    Returns:
        The standard url patterns for each service.
    """

    urlpatterns: UrlPatterns = [
        # https://www.django-rest-framework.org/topics/browsable-api/#authentication
        path(
            "/",
            include("rest_framework.urls", namespace="rest_framework"),
        ),
        path(
            "admin/",
            admin.site.urls,
            name="admin",
        ),
        path(
            "csrf/cookie/",
            CsrfCookieView.as_view(),
            name="get-csrf-cookie",
        ),
        path(
            "session/logout/",
            LogoutView.as_view(),
            name="logout",
        ),
        path(
            "session/expired/",
            session_expired_view,
            name="session-expired",
        ),
        *api_url_patterns,
    ]

    if include_user_urls:
        urlpatterns.append(
            path(
                "",
                include("codeforlife.user.urls"),
                name="user",
            )
        )

    return urlpatterns
