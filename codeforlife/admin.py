"""
© Ocado Group
Created on 26/05/2026 at 16:02:37(+01:00).
"""

from django.contrib.admin import ModelAdmin
from django.db.models import Q


class HashSearchModelAdmin(ModelAdmin):
    """
    Apply hash lookups to the full search term instead of `smart_split()` bits.
    """

    def get_search_results(self, request, queryset, search_term):
        # Get the search fields and split them into hash and non-hash fields.
        hash_fields: list[str] = []
        non_hash_fields: list[str] = []
        for field in self.get_search_fields(request):
            (hash_fields if "__sha256" in field else non_hash_fields).append(
                field
            )

        # Keep Django's default behavior for non-hash fields.
        non_hash_queryset = queryset.none()
        may_have_duplicates = False
        if non_hash_fields:
            original_search_fields = self.search_fields
            self.search_fields = tuple(non_hash_fields)  # type: ignore[misc]
            try:
                non_hash_queryset, may_have_duplicates = (
                    super().get_search_results(request, queryset, search_term)
                )
            finally:
                self.search_fields = (  # type: ignore[misc]
                    original_search_fields
                )

        # Hash transforms should use the whole input, not `smart_split()` bits.
        hash_queryset = queryset.none()
        if hash_fields and search_term:
            hash_query = Q.create(
                [(lookup, search_term) for lookup in hash_fields],
                connector=Q.OR,
            )
            hash_queryset = queryset.filter(hash_query)

        # Combine the hash and non-hash querysets.
        if non_hash_fields and hash_fields:
            queryset = hash_queryset | non_hash_queryset
            may_have_duplicates = True
        else:
            queryset = hash_queryset if hash_fields else non_hash_queryset

        return queryset, may_have_duplicates
