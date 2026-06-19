"""
© Ocado Group
Created on 20/01/2024 at 11:28:19(+00:00).
"""

from rest_framework import serializers

from ...serializers import ModelSerializer
from ..models import School
from ..models import User as RequestUser

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class SchoolSerializer(ModelSerializer[RequestUser, School]):
    # TODO: add to model validators in new schema.
    name = serializers.CharField(
        validators=School.name_validators,
        max_length=200,
        read_only=True,
    )

    uk_county = serializers.CharField(source="county", read_only=True)

    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "country",
            "uk_county",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "name": {"read_only": True},
            "country": {"read_only": True},
        }
