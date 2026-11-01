"""Google sign-in (OAuth 2.0 / OpenID Connect) using only the standard library."""

import base64
import json
import secrets
import urllib.parse
import urllib.request

from django.conf import settings
from django.urls import reverse

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def enabled():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def redirect_uri():
    # reverse() already includes SCRIPT_NAME, so this is the exact URL to register with Google.
    return settings.SITE_URL + reverse("accounts:google_callback")


def authorization_url(session):
    state = secrets.token_urlsafe(24)
    session["google_state"] = state
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"


def exchange_code(code):
    """Trade the authorization code for the ID token's claims (email, email_verified, name, ...)."""
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri(),
        "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen(TOKEN_ENDPOINT, data=data, timeout=10) as response:
        token = json.load(response)
    # The ID token comes straight from Google's token endpoint over HTTPS, so its payload can be trusted as is.
    payload = token["id_token"].split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
