import os


env = os.getenv("DJANGO_ENV", "local").strip().lower()

if env in {"production", "prod"}:
    from config.django.production import *  # noqa: F401,F403
elif env in {"local", "development", "dev", "test"}:
    from config.django.local import *  # noqa: F401,F403
else:
    raise RuntimeError(
        "Invalid DJANGO_ENV value. Expected one of: local, development, dev, test, production, prod."
    )
