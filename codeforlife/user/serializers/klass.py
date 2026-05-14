"""
© Ocado Group
Created on 20/01/2024 at 11:28:29(+00:00).
"""

from rest_framework import serializers

from ...serializers import ModelSerializer
from ..models import Class
from ..models import User as RequestUser

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class ClassSerializer(ModelSerializer[RequestUser, Class]):
    id = serializers.CharField(
        source="access_code",
        read_only=True,
    )

    # TODO: add to model validators in new schema.
    name = serializers.CharField(
        validators=Class.name_validators,
        max_length=200,
        read_only=True,
    )

    read_classmates_data = serializers.BooleanField(
        source="classmates_data_viewable",
        read_only=True,
    )

    receive_requests_until = serializers.DateTimeField(
        source="accept_requests_until",
        read_only=True,
    )

    school = serializers.IntegerField(
        source="teacher.school.id",
        read_only=True,
    )

    class Meta:
        model = Class
        fields = [
            "name",
            "id",
            "teacher",
            "school",
            "read_classmates_data",
            "receive_requests_until",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "teacher": {"read_only": True},
        }
