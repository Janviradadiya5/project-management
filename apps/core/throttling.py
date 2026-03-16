from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"
    rate = "10/min"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"
    rate = "5/min"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"
    rate = "5/15min"


class EmailVerificationRateThrottle(AnonRateThrottle):
    scope = "email_verification"
    rate = "5/15min"


class AuthWriteRateThrottle(UserRateThrottle):
    scope = "authenticated_write"
    rate = "120/min"


class AuthReadRateThrottle(UserRateThrottle):
    scope = "authenticated_read"
    rate = "300/min"


class AttachmentUploadRateThrottle(UserRateThrottle):
    scope = "attachment_upload"
    rate = "30/min"

