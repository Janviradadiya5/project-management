from pathlib import Path
from datetime import timedelta

from config.env import env, env_bool, env_int, env_required

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = env("SECRET_KEY", "change-me")
DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in env("ALLOWED_HOSTS", "").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "apps.users",
    "apps.organizations",
    "apps.projects",
    "apps.tasks",
    "apps.comments",
    "apps.attachments",
    "apps.notifications",
    "apps.activity_logs",
    "apps.webhooks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_required("DB_NAME"),
        "USER": env_required("DB_USER"),
        "PASSWORD": env_required("DB_PASSWORD"),
        "HOST": env_required("DB_HOST"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        "ATOMIC_REQUESTS": env_bool("DB_ATOMIC_REQUESTS", True),
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", "prefer"),
            "connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10),
        },
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# ============================================================================
# Django REST Framework Configuration
# ============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_SCHEMA_CLASS": "apps.core.schema.ModuleTaggedAutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/min",
        "user": "100/min",
        "login": "10/min",
        "register": "5/min",
        "password_reset": "5/15min",
        "email_verification": "5/15min",
        "authenticated_write": "120/min",
        "authenticated_read": "300/min",
    },
    "EXCEPTION_HANDLER": "apps.core.exception_handler.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "MAX_PAGE_SIZE": 100,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Project Management API",
    "DESCRIPTION": "OpenAPI schema and interactive API documentation.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "OrganizationStatusEnum": [
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("archived", "Archived"),
        ],
        "ProjectStatusEnum": [
            ("active", "Active"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        "TaskStatusEnum": [
            ("todo", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
    },
    "TAGS": [
        {"name": "Authentication", "description": "Login, registration, token, and account recovery APIs."},
        {"name": "Users", "description": "User profile and account management APIs."},
        {"name": "Organizations", "description": "Organization and member management APIs."},
        {"name": "Invites", "description": "Organization invitation acceptance APIs."},
        {"name": "Projects", "description": "Project and project membership APIs."},
        {"name": "Tasks", "description": "Task lifecycle and assignment APIs."},
        {"name": "Comments", "description": "Task comment APIs."},
        {"name": "Attachments", "description": "File attachment APIs."},
        {"name": "Notifications", "description": "Notification listing and state APIs."},
        {"name": "Activity Logs", "description": "Audit and activity history APIs."},
        {"name": "Webhooks", "description": "Webhook integration endpoints."},
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}

# ============================================================================
# CORS Configuration
# ============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-organization-id",
    "x-request-id",
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PATCH",
    "PUT",
    "DELETE",
    "OPTIONS",
]
CORS_MAX_AGE = 86400  # 24 hours

# ============================================================================
# JWT Configuration
# ============================================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": env("JWT_ALGORITHM", "HS256"),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": (env("JWT_AUTH_HEADER_PREFIX", "Bearer"),),
}

# ============================================================================
# Email Configuration
# ============================================================================
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", env("EMAIL_FROM", "noreply@example.com"))
SERVER_EMAIL = env("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
