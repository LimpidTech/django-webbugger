"""Test models for django-webbugger tests."""

from __future__ import annotations

from django.db import models
from django.http import HttpRequest

from webbugger import trackable


@trackable
class Product(models.Model):
    """A test product model with tracking."""

    name = models.CharField(max_length=255)
    url = models.URLField(default="https://example.com/")

    class Meta:
        app_label = "tests"

    def get_absolute_url(self) -> str:
        return self.url

    def __str__(self) -> str:
        return self.name


@trackable(field_name="tracking", related_name="campaigns")
class Campaign(models.Model):
    """A test campaign model with custom field name."""

    name = models.CharField(max_length=255)

    class Meta:
        app_label = "tests"

    def __str__(self) -> str:
        return self.name


@trackable(related_name="visitors")
class Visitor(models.Model):
    """A test visitor entity with beacon_update support."""

    user_agent = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        app_label = "tests"

    def beacon_update(self, request: HttpRequest) -> None:
        """Capture request data."""
        self.user_agent = request.META.get("HTTP_USER_AGENT", "")
        self.ip_address = request.META.get("REMOTE_ADDR")

    def __str__(self) -> str:
        return f"Visitor {self.pk}"


class UntrackableModel(models.Model):
    """A model without @trackable for testing."""

    name = models.CharField(max_length=255)

    class Meta:
        app_label = "tests"
