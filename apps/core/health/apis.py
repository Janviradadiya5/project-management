from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthApi(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="health_check",
        summary="Health check",
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={"status": serializers.CharField()},
            )
        },
    )
    def get(self, request):
        return Response({"status": "ok"})
