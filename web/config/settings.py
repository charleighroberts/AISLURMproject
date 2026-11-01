"""Settings come from environment variables (see .env.example) so the same code runs locally and on the VM."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "sims",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

if DEBUG:
    # Re-read templates on every request; the cached loader misses edits made through Docker bind mounts.
    TEMPLATES[0]["APP_DIRS"] = False
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

WSGI_APPLICATION = "config.wsgi.application"

# Postgres in Docker; SQLite if you run manage.py directly without POSTGRES_HOST.
if os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "NAME": os.environ.get("POSTGRES_DB", "policylab"),
            "USER": os.environ.get("POSTGRES_USER", "policylab"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# Users sign in with magic links only, so there are no passwords to validate.
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

# Serving under a path prefix, e.g. /AISLURMproject/app on mountainbluebells.com, where Caddy strips the
# prefix before forwarding. Django adds it back to every link it builds.
# (Not named SCRIPT_NAME: gunicorn reads that environment variable itself and rejects the stripped paths.)
SCRIPT_NAME = os.environ.get("URL_PREFIX", "").rstrip("/")

STATIC_URL = f"{SCRIPT_NAME}/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_STATIC_PREFIX = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "sims:scenario_list"
SESSION_COOKIE_AGE = 60 * 60 * 12
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

if SCRIPT_NAME:
    FORCE_SCRIPT_NAME = SCRIPT_NAME
    # Keep the app's cookies apart from the rest of the host site's.
    SESSION_COOKIE_PATH = CSRF_COOKIE_PATH = f"{SCRIPT_NAME}/"
    SESSION_COOKIE_NAME = "aislurm_session"
    CSRF_COOKIE_NAME = "aislurm_csrftoken"

if os.environ.get("BEHIND_PROXY") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "0") == "1"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@dsu.edu")

# Magic links
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000").rstrip("/")
MAGIC_LINK_MINUTES = int(os.environ.get("MAGIC_LINK_MINUTES", "15"))
MAGIC_LINK_MAX_PER_WINDOW = 5
ADMIN_EMAILS = [email.lower() for email in env_list("ADMIN_EMAILS")]
MAGIC_LINKS_ENABLED = os.environ.get("MAGIC_LINKS_ENABLED", "1") == "1"

# Sign-in from anywhere other than an AllowedDomain address. On for the public demo, off for DSU.
ALLOW_ANY_DOMAIN = os.environ.get("ALLOW_ANY_DOMAIN", "0") == "1"

# Google sign-in. The redirect URI to register is SITE_URL + URL_PREFIX + /login/google/callback/.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Sign-in handed over from a host site (mountainbluebells.com's launch.ashx) with an HMAC-signed token.
SSO_SHARED_SECRET = os.environ.get("SSO_SHARED_SECRET", "")
SITE_LAUNCH_URL = os.environ.get("SITE_LAUNCH_URL", "")

# LLM backend: "mock" until the Ollama / SLURM backends exist.
LLM_BACKEND = os.environ.get("LLM_BACKEND", "mock")
MOCK_DELAY_SECONDS = int(os.environ.get("MOCK_DELAY_SECONDS", "8"))
