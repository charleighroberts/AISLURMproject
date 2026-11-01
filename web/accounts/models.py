import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class AllowedDomain(models.Model):
    """An email domain allowed to sign in. Matching is exact: dsu.edu does not allow notdsu.edu or sub.dsu.edu."""

    domain = models.CharField(max_length=253, unique=True, help_text="For example: dsu.edu")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["domain"]

    def __str__(self):
        return self.domain

    def save(self, *args, **kwargs):
        self.domain = self.domain.strip().lower().lstrip("@")
        super().save(*args, **kwargs)

    @classmethod
    def allows(cls, email):
        if "@" not in email:
            return False
        domain = email.rsplit("@", 1)[1].strip().lower()
        return cls.objects.filter(domain=domain).exists()


def hash_token(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


class LoginToken(models.Model):
    """A single-use magic-link token. Only its SHA-256 hash is stored, never the token itself."""

    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, email):
        """Create a token for this email and return the raw value to put in the link."""
        raw = secrets.token_urlsafe(32)
        cls.objects.create(
            email=email,
            token_hash=hash_token(raw),
            expires_at=timezone.now() + timedelta(minutes=settings.MAGIC_LINK_MINUTES),
        )
        return raw

    @classmethod
    def recent_count(cls, email):
        since = timezone.now() - timedelta(minutes=settings.MAGIC_LINK_MINUTES)
        return cls.objects.filter(email=email, created_at__gte=since).count()

    @classmethod
    def redeem(cls, raw):
        """Use up the token and return its email, or None if it is unknown, expired or already used."""
        token = cls.objects.filter(token_hash=hash_token(raw)).first()
        if token is None:
            return None
        now = timezone.now()
        # Conditional update so two simultaneous clicks can't both succeed.
        used = cls.objects.filter(pk=token.pk, used_at__isnull=True, expires_at__gt=now).update(used_at=now)
        return token.email if used else None
