import uuid
from datetime import datetime, timezone

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from apps.core.exceptions import AppException


def _build_meta() -> dict:
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def api_exception_handler(exc, context):
    """Wraps all DRF exceptions in the standard error envelope."""
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", "APP_ERROR")
    message = "An error occurred."
    details = getattr(exc, "extra_details", {})

    if isinstance(exc, ValidationError):
        code = "VALIDATION_FAILED"
        message = "Validation failed."
        raw = exc.detail
        if isinstance(raw, dict):
            details = {
                k: [str(e) for e in v] if isinstance(v, list) else [str(v)]
                for k, v in raw.items()
            }
        elif isinstance(raw, list):
            details = {"non_field_errors": [str(e) for e in raw]}
        else:
            details = {"non_field_errors": [str(raw)]}
    elif isinstance(exc, AppException):
        message = str(exc.detail) if isinstance(exc.detail, str) else exc.default_detail
    else:
        d = getattr(exc, "detail", None)
        if isinstance(d, str):
            message = d
        elif isinstance(d, list) and d:
            message = str(d[0])

    response.data = {
        "success": False,
        "error_code": code,
        "details": details,
        "message": message,
        "meta": _build_meta(),
    }
    return response

