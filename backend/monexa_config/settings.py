"""
Django settings for MoneXa — Fintech Treasury Platform.

Configuration MoneXa — plateforme de trésorerie (D3BUG 0R DI3).
Production : PostgreSQL 16. Tests locaux : SQLite fallback automatique.
"""
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path
from decouple import Config, RepositoryEnv, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
# Lire UNIQUEMENT le .env du backend (ignore les .env globaux du sandbox)
_env_file = BASE_DIR / ".env"
config = Config(RepositoryEnv(str(_env_file))) if _env_file.exists() else Config(os.environ)

# ──────────────────────────────────────────────────────────────────────────
# Sécurité
# ──────────────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="dev-insecure-key-change-me-in-prod")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
_INSECURE_KEYS = {
    "dev-insecure-key-change-me-in-prod",
    "change-me-in-production-please-use-a-long-random-string",
}
if not DEBUG and SECRET_KEY in _INSECURE_KEYS:
    raise ImproperlyConfigured("SECRET_KEY de production invalide. Définissez un secret long et unique.")
if not DEBUG and ALLOWED_HOSTS == ["*"]:
    raise ImproperlyConfigured("ALLOWED_HOSTS=* est interdit hors DEBUG.")

BEHIND_PROXY = config("BEHIND_PROXY", default=False, cast=bool)
if BEHIND_PROXY:
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_csrf = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
CSRF_TRUSTED_ORIGINS = [o for o in (list(_csrf) if _csrf else []) if o]
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        f"http://{h}" for h in ALLOWED_HOSTS if h not in ("*", "")
    ] + [
        f"https://{h}" for h in ALLOWED_HOSTS if h not in ("*", "")
    ]
if DEBUG:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS)
    if "*" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append("*")
    for origin in (
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.trycloudflare.com",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
    ):
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)
    import socket
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127."):
                continue
            for origin in (f"http://{ip}", f"http://{ip}:80", f"http://{ip}:8000"):
                if origin not in CSRF_TRUSTED_ORIGINS:
                    CSRF_TRUSTED_ORIGINS.append(origin)
    except OSError:
        pass

# ──────────────────────────────────────────────────────────────────────────
# Applications
# ──────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    "django_otp",
    "django_otp.plugins.otp_totp",

    # Local
    "accounts",
    "finance.apps.FinanceConfig",
    "auditing",
    "reporting",
    "assistant",
    "website",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "monexa_config.middleware.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "monexa_config.urls"
WSGI_APPLICATION = "monexa_config.wsgi.application"
ASGI_APPLICATION = "monexa_config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "website.context_processors.monexa_ui",
            ],
        },
    },
]

# ──────────────────────────────────────────────────────────────────────────
# Base de données — PostgreSQL 16 en prod, SQLite en tests
# ──────────────────────────────────────────────────────────────────────────
DATABASE_URL = config("DATABASE_URL", default="").strip()
if DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://", "postgres://", "sqlite:")):
    # Production PostgreSQL (ou sqlite explicite)
    import dj_database_url  # type: ignore
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    # Tests locaux SQLite — fallback automatique
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ──────────────────────────────────────────────────────────────────────────
# Authentification — Custom User MoneXa
# ──────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ──────────────────────────────────────────────────────────────────────────
# Internationalisation — FR + Ewé + Kabyé
# ──────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = config("LANGUAGE_CODE", default="fr")
TIME_ZONE = config("TIME_ZONE", default="Africa/Lome")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", "Français"),
    ("ee", "Ewé"),
    ("kab", "Kabyé"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ──────────────────────────────────────────────────────────────────────────
# Fichiers statiques & médias
# ──────────────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/connexion/"
LOGIN_REDIRECT_URL = "/tableau-de-bord/"
LOGOUT_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────────────────────────────────
# Django REST Framework
# ──────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # pour Django Admin
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": "60/min",
        "anon": "20/min",
        "assistant": "10/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MoneXa API",
    "DESCRIPTION": (
        "Plateforme intelligente de trésorerie pour PME ouest-africaines. "
        "Extraction IA multimodale des reçus Mobile Money, réconciliation "
        "automatique, audit immuable SHA-256, chatbot TresorIA.\n\n"
        "D3BUG 0R DI3."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ──────────────────────────────────────────────────────────────────────────
# SimpleJWT
# ──────────────────────────────────────────────────────────────────────────
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_MINUTES", default=15, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ──────────────────────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────────────────────
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = config(
        "CORS_ALLOWED_ORIGINS",
        default="http://localhost:8080,http://127.0.0.1:8080",
        cast=Csv(),
    )

# IA — GPT-4o-mini Vision / Gemini Flash (requis pour photos de reçus)
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
MONEXA_AI_FALLBACK_MOCK = config("MONEXA_AI_FALLBACK_MOCK", default=False, cast=bool)

# ──────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "monexa": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
    CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
    X_FRAME_OPTIONS = "DENY"

RUN_SEED_DEMO = config("RUN_SEED_DEMO", default=False, cast=bool)
REDIS_URL = config("REDIS_URL", default="")
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
