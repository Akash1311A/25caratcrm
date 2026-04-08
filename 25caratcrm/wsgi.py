import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "25caratcrm.settings")


django.setup()
call_command("migrate", interactive=False, verbosity=0)

application = get_wsgi_application()
