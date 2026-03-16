import uuid
from datetime import datetime, timezone

from rest_framework.response import Response


def _build_meta() -> dict:
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def success_response(data, message: str = "Operation completed.", status_code: int = 200) -> Response:
    return Response(
        {"success": True, "message": message, "data": data, "meta": _build_meta()},
        status=status_code,
    )


def created_response(data, message: str = "Created successfully.") -> Response:
    return success_response(data, message=message, status_code=201)


def deleted_response(message: str = "Deleted successfully.") -> Response:
    return Response(
        {"success": True, "message": message, "data": None, "meta": _build_meta()},
        status=204,
    )

