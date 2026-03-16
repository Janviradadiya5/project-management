from rest_framework import status
from rest_framework.exceptions import APIException


class AppException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "APP_ERROR"
    default_detail = "An application error occurred."

    def __init__(self, detail=None, code=None, status_code=None, extra_details=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail or self.default_detail, code=code or self.default_code)
        self.extra_details = extra_details or {}


class AuthTokenMissingException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "AUTH_TOKEN_MISSING"
    default_detail = "Authentication credentials were not provided."


class AuthTokenInvalidOrExpiredException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "AUTH_TOKEN_INVALID_OR_EXPIRED"
    default_detail = "Invalid or expired token."


class AuthInvalidCredentialsException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "AUTH_INVALID_CREDENTIALS"
    default_detail = "Invalid credentials."


class AuthRefreshRevokedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "AUTH_REFRESH_REVOKED"
    default_detail = "Refresh token revoked."


class AuthEmailNotVerifiedException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "AUTH_EMAIL_NOT_VERIFIED"
    default_detail = "Email address not verified."


class PermissionDeniedException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "PERMISSION_DENIED"
    default_detail = "You do not have permission to perform this action."


class OrgAccessDeniedException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "ORG_ACCESS_DENIED"
    default_detail = "Permission denied."


class ResourceNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "RESOURCE_NOT_FOUND"
    default_detail = "Resource not found."


class OrgNotFoundOrDeletedException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "ORG_NOT_FOUND_OR_DELETED"
    default_detail = "Organization not found."


class ResourceConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "RESOURCE_CONFLICT"
    default_detail = "Resource conflict."


class BusinessRuleViolationException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "BUSINESS_RULE_VIOLATION"
    default_detail = "Business rule violated."


class InviteInvalidOrExpiredException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "INVITE_INVALID_OR_EXPIRED"
    default_detail = "Invite token is invalid or expired."


class ProjectStatusInvalidException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "PROJECT_STATUS_INVALID"
    default_detail = "Project status is invalid."


class ProjectDeadlineInvalidException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "PROJECT_DEADLINE_INVALID"
    default_detail = "Project deadline is invalid."


class TaskStatusInvalidException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "TASK_STATUS_INVALID"
    default_detail = "Task status is invalid."


class TaskAssigneeNotMemberException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "TASK_ASSIGNEE_NOT_MEMBER"
    default_detail = "Assignee must be an active member."


class TaskUpdateForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "TASK_UPDATE_FORBIDDEN"
    default_detail = "Task update is forbidden by role policy."


class CommentParentMismatchException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "COMMENT_PARENT_MISMATCH"
    default_detail = "Parent comment must belong to the same task."


class TokenInvalidOrExpiredException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "TOKEN_INVALID_OR_EXPIRED"
    default_detail = "Token is invalid or expired."


class OrgContextRequiredException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "ORG_CONTEXT_REQUIRED"
    default_detail = "Organization context required."


class AttachmentTypeForbiddenException(AppException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_code = "ATTACHMENT_TYPE_NOT_ALLOWED"
    default_detail = "Attachment type not allowed."


class AttachmentSizeExceededException(AppException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_code = "ATTACHMENT_SIZE_EXCEEDED"
    default_detail = "Attachment exceeds size limit."


class AttachmentAccessForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "ATTACHMENT_ACCESS_FORBIDDEN"
    default_detail = "Attachment access denied."

