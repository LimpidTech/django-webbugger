"""URL configuration for webbugger.

Example URL patterns for setting up beacon tracking.

Usage:
    1. Import the trigger view
    2. Create URL patterns with your desired configuration
    3. Include these patterns in your main urls.py

Example:
    from django.urls import path
    from webbugger.views import trigger
    from webbugger.models import IPEntity

    urlpatterns = [
        # Simple redirect tracking
        path(
            "go/<path:target_url>/",
            trigger,
            name="webbugger_redirect",
        ),

        # Pixel tracking with IP entity
        path(
            "pixel/<int:entity_id>/",
            trigger,
            {"entity_class": IPEntity, "pixel": True},
            name="webbugger_pixel",
        ),
    ]
"""

from __future__ import annotations

from typing import Any

from django.urls import path

app_name = "webbugger"

# Empty urlpatterns - users should define their own patterns
# See module docstring for examples
urlpatterns: list[Any] = []
