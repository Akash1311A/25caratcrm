import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "25caratcrm.settings")


def _should_run_migrations():
    value = os.environ.get("RUN_MIGRATIONS_ON_STARTUP")
    if value is None:
        value = "true" if os.environ.get("RENDER") == "true" else "false"
    return value.lower() in {"1", "true", "yes", "on"}


if _should_run_migrations():
    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

application = get_wsgi_application()
