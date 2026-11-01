"""Sign-in handed over from the host site.

mountainbluebells.com's AISLURMproject/launch.ashx signs {"email", "exp"} with HMAC-SHA256 using a secret both
sides share, and redirects here with token = base64url(payload) + "." + base64url(signature).
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.db import IntegrityError

from .models import LoginToken, hash_token

MAX_LIFETIME_SECONDS = 120


def b64url_decode(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(payload, secret):
    """Build a token the same way launch.ashx does. Used by tests."""
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return body + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def redeem(token):
    """Return the email in a valid, unexpired, not-yet-used token, or None."""
    secret = settings.SSO_SHARED_SECRET
    if not secret or token.count(".") != 1:
        return None
    body, signature = token.split(".")
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(expected, b64url_decode(signature)):
            return None
        payload = json.loads(b64url_decode(body))
        email = str(payload["email"]).strip().lower()
        expires = int(payload["exp"])
    except (ValueError, KeyError, TypeError):
        return None

    now = time.time()
    if not email or expires <= now or expires - now > MAX_LIFETIME_SECONDS:
        return None
    try:
        # Recording the token as used makes a replayed link fail on the unique hash.
        LoginToken.objects.create(
            email=email,
            token_hash=hash_token(token),
            expires_at=datetime.fromtimestamp(expires, dt_timezone.utc),
            used_at=datetime.now(dt_timezone.utc),
        )
    except IntegrityError:
        return None
    return email
