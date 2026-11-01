from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Admins sign in with a magic link like everyone else, not the admin password form.
    path("admin/login/", RedirectView.as_view(pattern_name="accounts:login")),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("sims.urls")),
]
