"""
© Ocado Group
Created on 16/03/2026 at 11:34:42(+00:00).
"""

import typing as t

from django.db.models import Model


def is_real_model_class(cls: t.Type[Model]):
    """Determine if the class is a real model class that should be validated."""
    return (
        cls.__module__ != "__fake__"  # used for migrations
        and not cls._meta.abstract
        and not cls._meta.proxy
    )
