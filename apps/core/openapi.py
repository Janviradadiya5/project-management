from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers


class PaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    limit = serializers.IntegerField()
    total_items = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_prev = serializers.BooleanField()


def _serializer_instance(serializer, *, many: bool = False):
    if isinstance(serializer, serializers.BaseSerializer):
        return serializer
    if isinstance(serializer, type) and issubclass(serializer, serializers.BaseSerializer):
        return serializer(many=many)
    return serializer


def success_response_serializer(name: str, data_serializer):
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(),
            "data": _serializer_instance(data_serializer),
            "message": serializers.CharField(),
        },
    )


def paginated_response_serializer(name: str, item_serializer):
    data_serializer = inline_serializer(
        name=f"{name}Data",
        fields={
            "items": _serializer_instance(item_serializer, many=True),
            "pagination": PaginationSerializer(),
        },
    )
    return success_response_serializer(name, data_serializer)


ORG_HEADER_PARAMETER = OpenApiParameter(
    name="X-Organization-ID",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Organization UUID used to scope the request.",
)


PAGE_PARAMETER = OpenApiParameter(
    name="page",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="1-based page number.",
)


LIMIT_PARAMETER = OpenApiParameter(
    name="limit",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Items per page. Allowed range: 1-100.",
)


FIELDS_PARAMETER = OpenApiParameter(
    name="fields",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Comma-separated list of response fields to include, or 'all'.",
)


SEARCH_PARAMETER = OpenApiParameter(
    name="search",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Case-insensitive search term.",
)


ORDER_PARAMETER = OpenApiParameter(
    name="order",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=["asc", "desc"],
    description="Sort direction.",
)


def sort_parameter(*values: str):
    return OpenApiParameter(
        name="sort_by",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        enum=list(values),
        description="Field used for sorting.",
    )


def uuid_path_parameter(name: str, description: str):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.PATH,
        required=True,
        description=description,
    )