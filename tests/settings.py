"""Django settings for running tests with in-memory SQLite."""

from __future__ import annotations

SECRET_KEY = "test-secret-key-not-for-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "webbugger",
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True

ROOT_URLCONF = "tests.urls"

# Webbugger settings
WEBBUGGER_RESOLVE_LOCAL = False
