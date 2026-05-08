"""
© Ocado Group
Created on 26/07/2024 at 11:26:14(+01:00).
"""

from django.db.models.query import QuerySet

# pylint: disable-next=line-too-long
from django_filters.rest_framework import (  # type: ignore[import-untyped] # isort: skip
    FilterSet as _FilterSet,
)


class FilterSet(_FilterSet):
    """Base filter set all other filter sets must inherit."""

    @staticmethod
    def make_exclude_field_list_method(field: str, lookup="in"):
        """Make a class-method that excludes a list of values for a field.

        Args:
            field: The field to exclude a list of values for.
            lookup: The lookup type to use for exclusion.

        Returns:
            A class-method.
        """

        def method(self: FilterSet, queryset: QuerySet, name: str, *args):
            return queryset.exclude(
                **{f"{field}__{lookup}": self.request.GET.getlist(name)}
            )

        return method
