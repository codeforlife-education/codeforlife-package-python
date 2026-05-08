"""
© Ocado Group
Created on 19/01/2024 at 17:06:45(+00:00).

Base test case for all model view sets.
"""

import typing as t
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.urls import reverse

from ..permissions import Permission
from ..serializers import BaseSerializer
from ..types import DataDict, JsonDict, KwArgs
from ..views import BaseModelViewSet, ModelViewSet
from .api import APITestCase, BaseAPITestCase
from .model_view_set_client import BaseModelViewSetClient, ModelViewSetClient

# pylint: disable=duplicate-code
if t.TYPE_CHECKING:
    from ..user.models import User

    RequestUser = t.TypeVar("RequestUser", bound=User)
else:
    RequestUser = t.TypeVar("RequestUser")

AnyModel = t.TypeVar("AnyModel", bound=Model)
AnyBaseModelViewSetClient = t.TypeVar(
    "AnyBaseModelViewSetClient", bound=BaseModelViewSetClient
)
AnyBaseModelViewSet = t.TypeVar("AnyBaseModelViewSet", bound=BaseModelViewSet)
# pylint: enable=duplicate-code


class BaseModelViewSetTestCase(
    BaseAPITestCase[AnyBaseModelViewSetClient],
    t.Generic[AnyBaseModelViewSet, AnyBaseModelViewSetClient, AnyModel],
):
    """Base for all model view set test cases."""

    basename: str
    model_view_set_class: t.Type[AnyBaseModelViewSet]

    REQUIRED_ATTRS: t.Set[str] = {
        "client_class",
        "basename",
        "model_view_set_class",
    }

    @property
    def model_class(self) -> t.Type[AnyModel]:
        """Shorthand to model class."""
        return self.model_view_set_class.model_class

    @property
    def request_user_class(self):
        """Shorthand to request-user class."""
        return get_user_model()

    def reverse_action(
        self,
        name: str,
        model: t.Optional[AnyModel] = None,
        **kwargs,
    ):
        """Get the reverse URL for the model view set's action.

        Args:
            name: The name of the action.
            model: The model to look up.

        Returns:
            The reversed URL for the model view set's action.
        """

        reverse_kwargs = t.cast(t.Optional[KwArgs], kwargs.pop("kwargs", None))
        reverse_kwargs = reverse_kwargs or {}

        if model is not None:
            lookup_url_kwarg = self.model_view_set_class.lookup_url_kwarg
            lookup_field = self.model_view_set_class.lookup_field
            lookup = lookup_url_kwarg or lookup_field
            reverse_kwargs[lookup] = getattr(model, lookup)

        name = name.replace("_", "-")
        return reverse(
            viewname=kwargs.pop("viewname", f"{self.basename}-{name}"),
            kwargs=reverse_kwargs,
            **kwargs,
        )

    # --------------------------------------------------------------------------
    # Assertion Helpers
    # --------------------------------------------------------------------------

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def assert_serialized_model_equals_json_model(
        self,
        model: AnyModel,
        json_model: JsonDict,
        action: str,
        request_method: str,
        contains_subset: bool = False,
    ):
        """Assert the serialized representation of a model matches its JSON
        representation.

        Args:
            model: The model to serialize.
            json_model: The JSON representation of the model.
            action: The model view set's action.
            request_method: The request's HTTP method.
            contains_subset: Whether the JSON representation is a subset of the
                serialized representation. If set to False, the representations
                must be an exact match.
        """
        # Get the logged-in user.
        try:
            user = self.request_user_class.objects.get(
                session=self.client.session.session_key
            )
        except ObjectDoesNotExist:
            user = None  # NOTE: no user has logged in.

        # Create an instance of the model view set and serializer.
        model_view_set = self.model_view_set_class(
            action=action.replace("-", "_"),
            # pylint: disable-next=no-member
            request=self.client.request_factory.generic(
                request_method, user=user
            ),
            format_kwarg=None,  # NOTE: required by get_serializer_context()
        )
        model_serializer = model_view_set.get_serializer(model)

        # Serialize the model.
        serialized_model = dict(model_serializer.data)

        # Recursively convert all datetimes to strings.
        def datetime_values_to_representation(data: DataDict):
            for key, value in data.copy().items():
                if isinstance(value, dict):
                    datetime_values_to_representation(value)
                elif isinstance(value, datetime):
                    data[key] = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        datetime_values_to_representation(serialized_model)

        # Assert the JSON model provided in the response is an exact match or
        # subset of the serialized model.
        self.assertDictEqual(
            serialized_model | json_model if contains_subset else json_model,
            serialized_model,
        )

    def assert_get_serializer_class(
        self,
        serializer_class: t.Type[BaseSerializer],
        action: str,
        *args,
        **kwargs,
    ):
        """Assert that the expected serializer class is returned.

        Args:
            serializer_class: The expected serializer class.
            action: The model view set's action.
        """
        model_view_set = self.model_view_set_class(
            *args, **kwargs, action=action
        )
        actual_serializer_class = model_view_set.get_serializer_class()
        self.assertEqual(serializer_class, actual_serializer_class)

    def assert_get_permissions(
        self, permissions: t.List[Permission], action: str, *args, **kwargs
    ):
        """Assert that the expected permissions are returned.

        Args:
            permissions: The expected permissions.
            action: The model view set's action.
        """
        kwargs["action"] = action
        model_view_set = self.model_view_set_class(*args, **kwargs)
        actual_permissions = model_view_set.get_permissions()
        self.assertListEqual(permissions, actual_permissions)

    def assert_get_queryset(
        self,
        values: t.Collection[AnyModel],
        *args,
        ordered: bool = True,
        **kwargs,
    ):
        """Assert that the expected queryset is returned.

        Args:
            values: The values we expect the queryset to contain.
            ordered: Whether the queryset provides an implicit ordering.
        """
        model_view_set = self.model_view_set_class(*args, **kwargs)
        queryset = model_view_set.get_queryset()
        if ordered and not queryset.ordered:
            queryset = queryset.order_by("pk")
        self.assertQuerySetEqual(queryset, values, ordered=ordered)

    def assert_get_serializer_context(
        self,
        serializer_context: t.Dict[str, t.Any],
        action: str,
        *args,
        **kwargs,
    ):
        """Assert that the serializer's context contains a subset of values.

        Args:
            serializer_context: The serializer's context.
            action: The model view set's action.
        """
        # pylint: disable-next=no-member
        kwargs.setdefault("request", self.client.request_factory.get())
        kwargs.setdefault("format_kwarg", None)
        model_view_set = self.model_view_set_class(
            *args, **kwargs, action=action
        )
        actual_serializer_context = model_view_set.get_serializer_context()
        self.assertDictEqual(
            actual_serializer_context | serializer_context,
            actual_serializer_context,
        )


# pylint: disable-next=too-many-ancestors
class ModelViewSetTestCase(
    BaseModelViewSetTestCase[
        ModelViewSet[RequestUser, AnyModel],
        ModelViewSetClient[RequestUser, AnyModel],
        AnyModel,
    ],
    APITestCase[RequestUser],
    t.Generic[RequestUser, AnyModel],
):
    """Base for all model view set test cases."""

    client_class = ModelViewSetClient

    REQUIRED_ATTRS: t.Set[str] = {
        "client_class",
        "basename",
        "model_view_set_class",
    }

    @property
    def request_user_class(self):  # type: ignore[override]
        """Shorthand to request-user class."""
        return self.model_view_set_class.request_user_class
