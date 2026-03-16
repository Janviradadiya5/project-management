from config.django.base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Local development: disable SSL for local PostgreSQL.
DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"
DATABASES["default"]["CONN_MAX_AGE"] = 0
