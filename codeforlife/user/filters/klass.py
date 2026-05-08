"""
© Ocado Group
Created on 24/07/2024 at 13:19:57(+01:00).
"""

from django.db.models.query import QuerySet  # isort: skip
from django_filters import (  # type: ignore[import-untyped] # isort: skip
    rest_framework as filters,
)

from ...filters import FilterSet  # isort: skip
from ..models import Class  # isort: skip


# pylint: disable-next=missing-class-docstring
class ClassFilterSet(FilterSet):
    _id = filters.CharFilter(method="_id__method")
    _id__method = FilterSet.make_exclude_field_list_method(
        "_access_code_hash", "sha256_in"
    )

    id_or_name = filters.CharFilter(method="id_or_name__method")

    def id_or_name__method(self, queryset: QuerySet[Class], _: str, value: str):
        """Get classes where the id or the name contain a substring."""
        value = value.lower()
        pks = [
            klass.pk
            for klass in queryset.select_related("teacher__school").only(
                "_access_code_enc", "_name_enc", "teacher__school__dek"
            )
            if value in klass.name.lower() or value in klass.access_code.lower()
        ]

        return queryset.filter(pk__in=pks)

    class Meta:
        model = Class
        fields = ["_id", "teacher", "id_or_name"]
