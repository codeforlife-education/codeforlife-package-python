"""
© Ocado Group
Created on 20/01/2024 at 09:48:30(+00:00).
"""

from ...permissions import OR
from ...tests import ModelViewSetTestCase
from ..models import AdminSchoolTeacherUser, Class, StudentUser, User
from ..permissions import IsStudent, IsTeacher
from ..views import ClassViewSet

RequestUser = User


# pylint: disable-next=too-many-ancestors,missing-class-docstring
class TestClassViewSet(ModelViewSetTestCase[RequestUser, Class]):
    basename = "class"
    model_view_set_class = ClassViewSet
    fixtures = ["school_1"]

    def setUp(self):
        self.admin_school_teacher_user = AdminSchoolTeacherUser.objects.get(
            _email_hash__sha256="admin.teacher@school1.com"
        )

    # test: get permissions

    def test_get_permissions__list(self):
        """Only school-teachers can list classes."""
        self.assert_get_permissions(
            permissions=[IsTeacher(in_school=True)],
            action="list",
        )

    def test_get_permissions__retrieve(self):
        """Anyone in a school can retrieve a class."""
        self.assert_get_permissions(
            permissions=[OR(IsStudent(), IsTeacher(in_school=True))],
            action="retrieve",
        )

    # test: get queryset

    def test_get_queryset__student(self):
        """Student-users can only target classes they are in."""
        user = StudentUser.objects.first()
        assert user

        self.assert_get_queryset(
            values=[user.student.class_field],  # type: ignore[list-item]
            request=self.client.request_factory.get(user=user),
        )

    def test_get_queryset__teacher(self):
        """Teacher-users can only target all the classes in their school."""
        user = AdminSchoolTeacherUser.objects.first()
        assert user

        self.assert_get_queryset(
            values=user.teacher.classes,
            request=self.client.request_factory.get(user=user),
        )

    # test: actions

    def test_retrieve(self):
        """Can successfully retrieve a class."""
        user = StudentUser.objects.first()
        assert user

        self.client.login_as(user)
        # pylint: disable-next=line-too-long
        self.client.retrieve(model=user.student.class_field)  # type: ignore[type-var]

    def test_list(self):
        """Can successfully list classes."""
        user = self.admin_school_teacher_user
        # TODO: assert user has classes in new schema.
        assert user.teacher.classes.count() >= 2

        self.client.login_as(user)
        self.client.list(models=user.teacher.classes.all())

    def test_list___id(self):
        """Can successfully list classes in a school, excluding some by ID."""
        user = self.admin_school_teacher_user
        assert user

        classes = user.teacher.classes
        assert classes.count() >= 2

        first_class = classes[0]
        classes = classes[1:]

        self.client.login_as(user)
        self.client.list(
            models=classes,
            filters={"_id": first_class.access_code},
        )

    def test_list__id_or_name(self):
        """
        Can successfully list classes in a school, filtered by their ID or name.
        """
        user = self.admin_school_teacher_user
        assert user

        klass = user.teacher.classes.first()
        assert klass

        partial_access_code = klass.access_code[:-1].lower()
        partial_name = klass.name[:-1].lower()

        klasses = Class.objects.select_related("teacher__school")

        self.client.login_as(user)
        self.client.list(
            models=[
                klass
                for klass in klasses.only(
                    "_access_code_enc", "teacher__school__dek"
                )
                if partial_access_code in klass.access_code.lower()
            ],
            filters={"id_or_name": partial_access_code},
        )
        self.client.list(
            models=[
                klass
                for klass in klasses.only("_name_enc", "teacher__school__dek")
                if partial_name in klass.name.lower()
            ],
            filters={"id_or_name": partial_name},
        )

    def test_list__teacher(self):
        """Can successfully list classes assigned to a teacher."""
        user = self.admin_school_teacher_user
        classes = Class.objects.filter(teacher=user.teacher)
        assert classes.exists()

        self.client.login_as(user)
        self.client.list(
            models=classes,  # type: ignore[arg-type]
            filters={"teacher": str(user.teacher.id)},
        )
