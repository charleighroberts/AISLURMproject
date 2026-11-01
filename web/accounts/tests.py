import time
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import handoff
from .models import LoginToken


class MagicLinkTests(TestCase):
    # dsu.edu and trojans.dsu.edu come from the seed migration.

    def request_link(self, email):
        return self.client.post(reverse("accounts:login"), {"email": email})

    def token_from_email(self):
        return mail.outbox[-1].body.split("token=")[1].split()[0]

    def redeem(self, token):
        return self.client.post(reverse("accounts:verify"), {"token": token})

    def test_allowed_domain_gets_link(self):
        response = self.request_link("First.Last@Trojans.DSU.edu")
        self.assertRedirects(response, reverse("accounts:sent"))
        self.assertEqual(mail.outbox[0].to, ["first.last@trojans.dsu.edu"])

    def test_lookalike_domains_rejected(self):
        for email in ["a@notdsu.edu", "a@dsu.edu.evil.com", "a@sub.dsu.edu", "a@gmail.com", "not-an-email"]:
            self.request_link(email)
        self.assertEqual(len(mail.outbox), 0)

    def test_scanner_get_does_not_use_up_token(self):
        self.request_link("a@dsu.edu")
        token = self.token_from_email()
        self.client.get(reverse("accounts:verify"), {"token": token})
        self.assertRedirects(self.redeem(token), reverse("sims:scenario_list"))

    def test_token_works_once(self):
        self.request_link("a@dsu.edu")
        token = self.token_from_email()
        self.redeem(token)
        self.client.logout()
        self.assertEqual(self.redeem(token).status_code, 400)

    def test_expired_token_rejected(self):
        self.request_link("a@dsu.edu")
        token = self.token_from_email()
        LoginToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.redeem(token).status_code, 400)

    def test_rate_limit(self):
        for _ in range(6):
            self.request_link("a@dsu.edu")
        self.assertEqual(len(mail.outbox), 5)

    @override_settings(ADMIN_EMAILS=["eric.holm@dsu.edu"])
    def test_admin_email_becomes_admin(self):
        self.request_link("Eric.Holm@dsu.edu")
        self.redeem(self.token_from_email())
        user = get_user_model().objects.get(username="eric.holm@dsu.edu")
        self.assertTrue(user.is_staff and user.is_superuser)
        self.assertFalse(user.has_usable_password())


@override_settings(GOOGLE_CLIENT_ID="client-id", GOOGLE_CLIENT_SECRET="client-secret")
class GoogleSignInTests(TestCase):
    def start(self):
        response = self.client.get(reverse("accounts:google_start"))
        self.assertTrue(response["Location"].startswith("https://accounts.google.com/"))
        return self.client.session["google_state"]

    def callback(self, state, claims):
        with mock.patch("accounts.google.exchange_code", return_value=claims):
            return self.client.get(reverse("accounts:google_callback"), {"code": "abc", "state": state})

    def test_dsu_google_account_signs_in(self):
        response = self.callback(self.start(), {"email": "A@trojans.dsu.edu", "email_verified": True})
        self.assertRedirects(response, reverse("sims:scenario_list"))

    def test_other_domains_blocked_by_default(self):
        response = self.callback(self.start(), {"email": "someone@gmail.com", "email_verified": True})
        self.assertEqual(response.status_code, 403)

    @override_settings(ALLOW_ANY_DOMAIN=True)
    def test_any_google_account_when_open(self):
        response = self.callback(self.start(), {"email": "someone@gmail.com", "email_verified": True})
        self.assertRedirects(response, reverse("sims:scenario_list"))

    def test_wrong_state_rejected(self):
        self.start()
        response = self.callback("forged", {"email": "a@dsu.edu", "email_verified": True})
        self.assertEqual(response.status_code, 400)

    def test_unverified_email_rejected(self):
        response = self.callback(self.start(), {"email": "a@dsu.edu", "email_verified": False})
        self.assertEqual(response.status_code, 400)


@override_settings(SSO_SHARED_SECRET="shared-secret", ALLOW_ANY_DOMAIN=True)
class SiteHandoffTests(TestCase):
    def handoff(self, token):
        return self.client.get(reverse("accounts:site_handoff"), {"token": token})

    def token(self, email="visitor@gmail.com", lifetime=60, secret="shared-secret"):
        return handoff.sign({"email": email, "exp": int(time.time()) + lifetime}, secret)

    def test_valid_token_signs_in(self):
        self.assertRedirects(self.handoff(self.token()), reverse("sims:scenario_list"))
        self.assertTrue(get_user_model().objects.filter(username="visitor@gmail.com").exists())

    def test_wrong_secret_rejected(self):
        self.assertEqual(self.handoff(self.token(secret="guess")).status_code, 400)

    def test_expired_token_rejected(self):
        self.assertEqual(self.handoff(self.token(lifetime=-1)).status_code, 400)

    def test_long_lived_token_rejected(self):
        self.assertEqual(self.handoff(self.token(lifetime=3600)).status_code, 400)

    def test_token_works_once(self):
        token = self.token()
        self.handoff(token)
        self.client.logout()
        self.assertEqual(self.handoff(token).status_code, 400)

    def test_tampered_email_rejected(self):
        _, signature = self.token().split(".")
        forged = handoff.sign({"email": "eric.holm@dsu.edu", "exp": int(time.time()) + 60}, "x").split(".")[0]
        self.assertEqual(self.handoff(forged + "." + signature).status_code, 400)
