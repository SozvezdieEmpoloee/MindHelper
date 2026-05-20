import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def get_csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


SECRET_KEY = get_env("DJANGO_SECRET_KEY", "change-this-secret-key")
DEBUG = get_env("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = get_csv_env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.common",
    "apps.accounts",
    "apps.chat",
    "apps.neural_engine",
    "apps.assessments",
    "apps.directory",
    "apps.platform_ops",
    "apps.telegram_bot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env("POSTGRES_DB", "mindhelper_db"),
        "USER": get_env("POSTGRES_USER", "mindhelper_app"),
        "PASSWORD": get_env("POSTGRES_PASSWORD", "MindHelper_2026!"),
        "HOST": get_env("POSTGRES_HOST", "127.0.0.1"),
        "PORT": get_env("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": get_env("POSTGRES_TEST_DB", "test_mindhelper_db"),
        },
    }
}

AUTH_USER_MODEL = "accounts.UserAccount"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

LLM_PROVIDER = get_env("LLM_PROVIDER", "rule_based").lower()
LLM_OLLAMA_BASE_URL = get_env("LLM_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
LLM_OLLAMA_MODEL = get_env("LLM_OLLAMA_MODEL", "qwen3:8b")
LLM_OLLAMA_TIMEOUT_SECONDS = float(get_env("LLM_OLLAMA_TIMEOUT_SECONDS", "120"))
LLM_HISTORY_MESSAGES = int(get_env("LLM_HISTORY_MESSAGES", "16"))
LLM_TEMPERATURE = float(get_env("LLM_TEMPERATURE", "0.4"))
LLM_MAX_OUTPUT_TOKENS = int(get_env("LLM_MAX_OUTPUT_TOKENS", "640"))

LLM_MODEL_VERSION_TAG = get_env("LLM_MODEL_VERSION_TAG", "ollama-qwen3-8b-local")
LLM_MODEL_DISPLAY_NAME = get_env("LLM_MODEL_DISPLAY_NAME", "Qwen3-8B")
LLM_PROVIDER_LABEL = get_env("LLM_PROVIDER_LABEL", "ollama-local")
LLM_SAFETY_PROFILE = get_env("LLM_SAFETY_PROFILE", "strict-v2")
LLM_ADMIN_EMAIL = get_env("LLM_ADMIN_EMAIL", "admin@mindhelper.local")

TELEGRAM_BOT_TOKEN = get_env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_API_BASE_URL = get_env("TELEGRAM_BOT_API_BASE_URL", "https://api.telegram.org")
TELEGRAM_BOT_TIMEOUT_SECONDS = float(get_env("TELEGRAM_BOT_TIMEOUT_SECONDS", "30"))
TELEGRAM_BOT_POLL_TIMEOUT_SECONDS = int(get_env("TELEGRAM_BOT_POLL_TIMEOUT_SECONDS", "30"))

CORS_ALLOWED_ORIGINS = get_csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173",
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = get_csv_env(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "apps.chat": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.neural_engine": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.telegram_bot": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.directory": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
