import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных из .env
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Переменная окружения SECRET_KEY не задана. "
        "Скопируйте .env.example в .env и укажите SECRET_KEY."
    )

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(
        ","
    )
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "users",
    "files",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "users.context_processors.admin_access",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Настройки перенаправления при входе/выходе
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# Настройки файлового менеджера и хранилища (Local / S3)
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local").strip().lower()
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TOTAL_STORAGE_MB = int(os.environ.get("MAX_TOTAL_STORAGE_MB", "100"))
MAX_TOTAL_STORAGE_BYTES = MAX_TOTAL_STORAGE_MB * 1024 * 1024

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media" / "storage"

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-central-1").strip()
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "").strip() or None
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip() or None
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "").strip() or None
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

if STORAGE_BACKEND == "s3":
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "region_name": AWS_S3_REGION_NAME,
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "endpoint_url": AWS_S3_ENDPOINT_URL,
                "file_overwrite": False,
                "default_acl": None,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": MEDIA_ROOT,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"


# --- Keycloak SSO Configuration ---
import os

INSTALLED_APPS += ["mozilla_django_oidc"]

AUTHENTICATION_BACKENDS = (
    "users.oidc.KeycloakOIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)

OIDC_RP_CLIENT_ID = os.getenv("OIDC_RP_CLIENT_ID", "django-client")
OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_RP_CLIENT_SECRET", "django-client-secret-12345")

KEYCLOAK_PUBLIC_URL = os.getenv(
    "KEYCLOAK_PUBLIC_URL",
    "http://54.211.123.237:8080/realms/django-realm/protocol/openid-connect",
)
KEYCLOAK_INTERNAL_URL = os.getenv(
    "KEYCLOAK_INTERNAL_URL",
    "http://keycloak:8080/realms/django-realm/protocol/openid-connect",
)

OIDC_OP_AUTHORIZATION_ENDPOINT = f"{KEYCLOAK_PUBLIC_URL}/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/token"
OIDC_OP_USER_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/certs"

OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = "openid profile email"
OIDC_VERIFY_SSL = False

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
