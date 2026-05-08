"""
© Ocado Group
Created on 24/01/2024 at 13:47:53(+00:00).
"""

from ...permissions import OR
from ...views import ModelViewSet
from ..filters import ClassFilterSet
from ..models import Class, User
from ..permissions import IsStudent, IsTeacher
from ..serializers import ClassSerializer


# pylint: disable-next=missing-class-docstring,too-many-ancestors
class ClassViewSet(ModelViewSet[User, Class]):
    request_user_class = User
    model_class = Class
    http_method_names = ["get"]
    lookup_field = "_access_code_hash__sha256"
    lookup_url_kwarg = "access_code"
    serializer_class = ClassSerializer
    filterset_class = ClassFilterSet

    # pylint: disable-next=missing-function-docstring
    def get_permissions(self):
        # Only school-teachers can list classes.
        if self.action == "list":
            return [IsTeacher(in_school=True)]

        return [OR(IsStudent(), IsTeacher(in_school=True))]

    # pylint: disable-next=missing-function-docstring
    def get_queryset(self):
        user = self.request.auth_user
        if user.student:
            return Class.objects.filter(students=user.student)

        return self.request.school_teacher_user.teacher.classes
