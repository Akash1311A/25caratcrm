import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jaishreefashioncrm.settings")

if os.environ.get("RUN_STARTUP_TASKS", "true").lower() in {"1", "true", "yes", "on"}:
    django.setup()
    call_command("collectstatic", interactive=False, verbosity=0, clear=False)

application = get_wsgi_application()
