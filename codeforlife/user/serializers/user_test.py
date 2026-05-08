"""
© Ocado Group
Created on 18/04/2024 at 17:26:59(+01:00).
"""

from ...tests import ModelSerializerTestCase
from ..models import IndependentUser, StudentUser, TeacherUser, User
from .user import UserSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class TestUserSerializer(ModelSerializerTestCase[User, User]):
    fixtures = ["school_1", "independent"]
    model_serializer_class = UserSerializer  # type: ignore[assignment,override]

    # test: to representation

    def test_to_representation__teacher(self):
        """Serialize teacher user to representation."""
        user = TeacherUser.objects.first()
        assert user

        self.assert_to_representation(
            user,
            new_data={
                "requesting_to_join_class": None,
                "teacher": {
                    "id": user.teacher.id,
                    # pylint: disable-next=line-too-long
                    "school": user.teacher.school.id,  # type: ignore[union-attr]
                    "is_admin": user.teacher.is_admin,
                },
                "student": None,
            },
            # TODO: remove in new schema.
            non_model_fields={
                "requesting_to_join_class",
                "teacher",
                "student",
                # TODO: remove once plain fields are removed.
                "first_name",
                "last_name",
                "email",
            },
        )

    def test_to_representation__student(self):
        """Serialize student user to representation."""
        user = StudentUser.objects.first()
        assert user

        self.assert_to_representation(
            user,
            new_data={
                "requesting_to_join_class": None,
                "teacher": None,
                "student": {
                    "id": user.student.id,
                    # pylint: disable-next=line-too-long
                    "klass": user.student.class_field.access_code,  # type: ignore[union-attr]
                    # pylint: disable-next=line-too-long
                    "school": user.student.class_field.teacher.school.id,  # type: ignore[union-attr]
                },
            },
            # TODO: remove in new schema.
            non_model_fields={
                "requesting_to_join_class",
                "teacher",
                "student",
                # TODO: remove once plain fields are removed.
                "first_name",
                "last_name",
                "email",
            },
        )

    def test_to_representation__indy(self):
        """Serialize independent user to representation."""
        user = IndependentUser.objects.filter(
            new_student__pending_class_request__isnull=True
        ).first()
        assert user

        self.assert_to_representation(
            user,
            new_data={
                "requesting_to_join_class": None,
                "teacher": None,
                "student": None,
            },
            # TODO: remove in new schema.
            non_model_fields={
                "requesting_to_join_class",
                "teacher",
                "student",
                # TODO: remove once plain fields are removed.
                "first_name",
                "last_name",
                "email",
            },
        )
