import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import google, handoff
from .models import AllowedDomain, LoginToken

logger = logging.getLogger(__name__)

DOMAIN_ERROR = "Only approved university email addresses can sign in."


def email_allowed(email):
    return settings.ALLOW_ANY_DOMAIN or AllowedDomain.allows(email)


def login_page(request, error=None, email="", status=200):
    return render(request, "accounts/login.html", {
        "error": error,
        "email": email,
        "magic_links": settings.MAGIC_LINKS_ENABLED,
        "google": google.enabled(),
        "site_launch_url": settings.SITE_LAUNCH_URL,
    }, status=status)


def sign_in(request, email):
    """Log in (creating the account on first visit) and go to the scenario list."""
    User = get_user_model()
    user = User.objects.filter(username=email).first()
    if user is None:
        user = User.objects.create_user(username=email, email=email)  # no usable password
    if email in settings.ADMIN_EMAILS and not user.is_superuser:
        user.is_staff = user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])
    login(request, user)
    return redirect(settings.LOGIN_REDIRECT_URL)


def request_link(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if request.method != "POST" or not settings.MAGIC_LINKS_ENABLED:
        return login_page(request)

    email = request.POST.get("email", "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return login_page(request, "Enter a valid email address.", email)
    if not email_allowed(email):
        return login_page(request, DOMAIN_ERROR, email)
    if LoginToken.recent_count(email) >= settings.MAGIC_LINK_MAX_PER_WINDOW:
        return login_page(request, "Too many sign-in requests. Please wait a few minutes and try again.", email)

    raw = LoginToken.issue(email)
    link = f"{settings.SITE_URL}{reverse('accounts:verify')}?token={raw}"
    send_mail(
        subject="Your DSU Policy Lab sign-in link",
        message=(
            "Click the link below to sign in to the DSU Policy Lab.\n\n"
            f"{link}\n\n"
            f"It expires in {settings.MAGIC_LINK_MINUTES} minutes and works once. "
            "If you didn't ask for it, you can ignore this email.\n"
        ),
        from_email=None,
        recipient_list=[email],
    )
    return redirect("accounts:sent")


def sent(request):
    return render(request, "accounts/sent.html", {"show_dev_inbox": settings.DEBUG})


def verify(request):
    # GET only shows a "Sign in" button. Email security scanners open links with GET,
    # which would otherwise use up the single-use token before the user clicks it.
    if request.method != "POST":
        return render(request, "accounts/verify.html", {"token": request.GET.get("token", "")})

    email = LoginToken.redeem(request.POST.get("token", ""))
    if email is None:
        return render(request, "accounts/expired.html", status=400)
    return sign_in(request, email)


def google_start(request):
    if not google.enabled():
        raise Http404
    return redirect(google.authorization_url(request.session))


def google_callback(request):
    if not google.enabled():
        raise Http404
    expected_state = request.session.pop("google_state", None)
    code = request.GET.get("code")
    if request.GET.get("error") or not code or not expected_state or request.GET.get("state") != expected_state:
        return login_page(request, "Google sign-in was cancelled or couldn't be verified. Please try again.", status=400)

    try:
        claims = google.exchange_code(code)
    except Exception:
        logger.exception("Google token exchange failed")
        return login_page(request, "Google sign-in failed. Please try again.", status=502)

    email = str(claims.get("email", "")).strip().lower()
    if not email or claims.get("email_verified") not in (True, "true", "True"):
        return login_page(request, "Your Google account didn't provide a verified email address.", status=400)
    if not email_allowed(email):
        return login_page(request, DOMAIN_ERROR, status=403)
    return sign_in(request, email)


def site_handoff(request):
    email = handoff.redeem(request.GET.get("token", ""))
    if email is None or not email_allowed(email):
        return login_page(request, "That sign-in link has expired. Please sign in again.", status=400)
    return sign_in(request, email)


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")
