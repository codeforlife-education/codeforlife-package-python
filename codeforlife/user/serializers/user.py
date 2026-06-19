"""
© Ocado Group
Created on 19/01/2024 at 11:06:00(+00:00).
"""

import typing as t

from rest_framework import serializers

from ...serializers import ModelSerializer
from ..models import AnyUser, Student, Teacher, User
from .student import StudentSerializer
from .teacher import TeacherSerializer

RequestUser = User

# pylint: disable=missing-class-docstring
# pylint: disable=too-many-ancestors


class BaseUserSerializer(
    ModelSerializer[RequestUser, AnyUser], t.Generic[AnyUser]
):
    # TODO: add to model validators in new schema.
    first_name = serializers.CharField(
        validators=User.first_name_validators,
        max_length=150,
        read_only=True,
    )

    # TODO: add to model validators in new schema.
    last_name = serializers.CharField(
        validators=User.last_name_validators,
        max_length=150,
        read_only=True,
    )

    requesting_to_join_class = serializers.CharField(
        source="new_student.pending_class_request",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "date_joined",
            "requesting_to_join_class",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "first_name": {"read_only": True},
            "last_name": {"read_only": True},
            "email": {"read_only": True},
            "is_active": {"read_only": True},
            "date_joined": {"read_only": True},
        }


class UserSerializer(BaseUserSerializer[AnyUser], t.Generic[AnyUser]):
    student = StudentSerializer(
        source="new_student",
        read_only=True,
    )

    teacher = TeacherSerializer[Teacher](
        source="new_teacher",
        read_only=True,
    )

    class Meta(BaseUserSerializer.Meta):
        fields = [*BaseUserSerializer.Meta.fields, "student", "teacher"]

    def to_representation(self, instance):
        try:
            student = (
                dict(StudentSerializer(instance.new_student).data)
                if instance.new_student and instance.new_student.class_field
                else None
            )
        except Student.DoesNotExist:
            student = None

        try:
            requesting_to_join_class = (
                instance.new_student.pending_class_request.access_code
                if instance.new_student
                and instance.new_student.pending_class_request
                else None
            )
        except Student.DoesNotExist:
            requesting_to_join_class = None

        try:
            teacher = (
                dict(TeacherSerializer[Teacher](instance.new_teacher).data)
                if instance.new_teacher
                else None
            )
        except Teacher.DoesNotExist:
            teacher = None

        return {
            "id": instance.id,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "email": instance.email,
            "is_active": instance.is_active,
            "date_joined": instance.date_joined,
            "requesting_to_join_class": requesting_to_join_class,
            "student": student,
            "teacher": teacher,
        }
