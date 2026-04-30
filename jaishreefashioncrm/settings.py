import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-jaishreefashion-secret")
DEBUG = os.environ.get("DEBUG", "False").lower() in {"1", "true", "yes", "on"}

def _parse_csv(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _merge_unique(*groups):
    merged = []
    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


default_allowed_hosts = [
    "jaishreefashioncrm.onrender.com",
    "25caratcrm.onrender.com",
    "two5caratcrm.onrender.com",
    "crm.jaishreefashions.com",
    "jaishreefashions.com",
    "www.jaishreefashions.com",
]
env_allowed_hosts = _parse_csv(os.environ.get("ALLOWED_HOSTS", ""))
ALLOWED_HOSTS = _merge_unique(default_allowed_hosts, env_allowed_hosts)
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
RUNNING_LOCALHOST = any(host in LOCAL_HOSTS for host in ALLOWED_HOSTS)
IS_LOCAL_ENV = DEBUG or RUNNING_LOCALHOST

default_csrf_trusted_origins = [
    f"https://{host}"
    for host in ALLOWED_HOSTS
    if host and host != "*"
]
env_csrf_trusted_origins = _parse_csv(os.environ.get("CSRF_TRUSTED_ORIGINS", ""))
CSRF_TRUSTED_ORIGINS = _merge_unique(default_csrf_trusted_origins, env_csrf_trusted_origins)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "crm.middleware.ExceptionLoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "jaishreefashioncrm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "crm" / "templates"],
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

WSGI_APPLICATION = "jaishreefashioncrm.wsgi.application"

database_url = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
database_config = {
    "default": database_url,
    "conn_max_age": 600,
}
if not database_url.startswith("sqlite:///"):
    database_config["ssl_require"] = not DEBUG

DATABASES = {
    "default": dj_database_url.config(**database_config)
}
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

AUTH_PASSWORD_VALIDATORS = []

AUTHENTICATION_BACKENDS = [
    "crm.auth_backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "crm" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not IS_LOCAL_ENV
SESSION_COOKIE_SECURE = not IS_LOCAL_ENV
CSRF_COOKIE_SECURE = not IS_LOCAL_ENV
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000 if not IS_LOCAL_ENV else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not IS_LOCAL_ENV
SECURE_HSTS_PRELOAD = not IS_LOCAL_ENV
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "crm": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
