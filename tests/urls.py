"""URL configuration for tests."""

from __future__ import annotations

from django.urls import path

from webbugger import trigger

from .models import Product

urlpatterns = [
    path(
        "track/<int:target_id>/",
        trigger,
        {"target_url": "https://example.com/"},
        name="track",
    ),
    path(
        "pixel/",
        trigger,
        {"target_url": "", "pixel": True},
        name="pixel",
    ),
]
