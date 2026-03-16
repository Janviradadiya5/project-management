from config.django.base import *  # noqa: F401,F403

from config.env import env, env_bool, env_int

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS and browser security hardening.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

csrf_trusted_origins = [origin.strip() for origin in env("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
if csrf_trusted_origins:
	CSRF_TRUSTED_ORIGINS = csrf_trusted_origins

# Production-safe DB defaults.
DATABASES["default"]["CONN_MAX_AGE"] = env_int("DB_CONN_MAX_AGE", 300)
DATABASES["default"]["OPTIONS"]["sslmode"] = env("DB_SSLMODE", "require")
DATABASES["default"]["OPTIONS"]["connect_timeout"] = env_int("DB_CONNECT_TIMEOUT", 10)
