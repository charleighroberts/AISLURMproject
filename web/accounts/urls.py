from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.request_link, name="login"),
    path("login/sent/", views.sent, name="sent"),
    path("login/verify/", views.verify, name="verify"),
    path("login/google/", views.google_start, name="google_start"),
    path("login/google/callback/", views.google_callback, name="google_callback"),
    path("login/site/", views.site_handoff, name="site_handoff"),
    path("logout/", views.logout_view, name="logout"),
]
