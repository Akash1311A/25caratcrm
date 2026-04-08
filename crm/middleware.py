import os
from threading import Lock

from django.core.management import call_command


class EnsureMigrationsMiddleware:
    _ran = False
    _lock = Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        run_on_request = os.environ.get("RUN_MIGRATIONS_ON_REQUEST")
        if run_on_request is None:
            run_on_request = "true" if os.environ.get("RENDER") == "true" else "false"

        if run_on_request.lower() not in {"1", "true", "yes", "on"}:
            return self.get_response(request)

        if not self.__class__._ran:
            with self.__class__._lock:
                if not self.__class__._ran:
                    call_command("migrate", interactive=False, verbosity=0)
                    self.__class__._ran = True

        return self.get_response(request)
