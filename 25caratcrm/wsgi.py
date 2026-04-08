import os

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "25caratcrm.settings")


def _run_startup_migrations():
    run_on_startup = os.environ.get("RUN_MIGRATIONS_ON_STARTUP")
    if run_on_startup is None:
        run_on_startup = "true" if os.environ.get("RENDER") == "true" else "false"

    if run_on_startup.lower() not in {"1", "true", "yes", "on"}:
        return

    call_command("migrate", interactive=False, verbosity=0)


_run_startup_migrations()
application = get_wsgi_application()
