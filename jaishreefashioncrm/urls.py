from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("crm.urls")),
    path("favicon.ico", RedirectView.as_view(url="/static/crm/favicon.ico")),
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {"document_root": settings.BASE_DIR / "crm" / "static"},
    ),
]
