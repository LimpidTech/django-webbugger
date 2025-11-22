"""Views for django-webbugger tracking system."""

from __future__ import annotations

import base64
from typing import Any, Protocol, runtime_checkable

from django.conf import settings
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import resolve

from .models import Beacon


# Base64-encoded 1x1 transparent GIF (43 bytes)
CLEAR_GIF_CONTENTS: str = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


@runtime_checkable
class HasBeaconUpdate(Protocol):
    """Protocol for entities that can be updated during beacon processing."""

    def beacon_update(self, request: HttpRequest) -> None:
        """Update entity with request data."""
        ...


@runtime_checkable
class HasGetAbsoluteUrl(Protocol):
    """Protocol for objects that provide a URL."""

    def get_absolute_url(self) -> str:
        """Return the absolute URL."""
        ...


@runtime_checkable
class HasGetBeaconUrl(Protocol):
    """Protocol for objects that provide a custom beacon URL."""

    def get_beacon_url(self) -> str:
        """Return the beacon URL."""
        ...


def _get_target_url(target: models.Model) -> str | None:
    """Get the redirect URL from a target object."""
    if isinstance(target, HasGetBeaconUrl):
        return target.get_beacon_url()
    if isinstance(target, HasGetAbsoluteUrl):
        return target.get_absolute_url()
    # Fallback for duck typing
    if hasattr(target, "get_beacon_url") and callable(target.get_beacon_url):
        return target.get_beacon_url()
    if hasattr(target, "get_absolute_url") and callable(target.get_absolute_url):
        return target.get_absolute_url()
    return None


def trigger(
    request: HttpRequest,
    target_url: str | None = None,
    target: models.Model | None = None,
    entity: models.Model | None = None,
    entity_class: type[models.Model] | None = None,
    entity_id: int | str | None = None,
    pixel: bool = False,
) -> HttpResponse:
    """Create a tracking beacon and redirect or return a tracking pixel.

    The beacon is created and can be linked to related models via their
    ManyToManyField (added by @trackable decorator).

    Args:
        request: The HTTP request object.
        target_url: URL to redirect to. If not provided, extracted from target.
        target: Optional model instance to extract URL from and link to beacon.
        entity: Optional entity instance to link to the beacon.
        entity_class: Optional entity class to create/fetch an entity.
        entity_id: Optional ID to fetch existing entity of entity_class.
        pixel: If True, return a 1x1 transparent GIF instead of redirecting.

    Returns:
        HttpResponse: Either a redirect to the target URL or a transparent GIF.

    Raises:
        Http404: If no valid target URL can be determined (in redirect mode).

    Example URL configuration:
        # Simple redirect tracking
        path(
            "track/",
            trigger,
            {"target_url": "https://example.com/"},
            name="track",
        )

        # Pixel tracking with entity
        path(
            "pixel/<int:entity_id>/",
            trigger,
            {"entity_class": IPEntity, "pixel": True},
            name="pixel",
        )
    """
    # Resolve target URL
    final_url = target_url
    if final_url is None and target is not None:
        final_url = _get_target_url(target)

    # In redirect mode, we need a URL
    if not pixel and not final_url:
        raise Http404("No target URL provided for redirect.")

    # Handle entity creation/retrieval
    if entity is None and entity_class is not None:
        if entity_id is not None:
            entity, _ = entity_class.objects.get_or_create(pk=entity_id)
        else:
            entity = entity_class()

    # Call beacon_update if entity supports it
    if entity is not None:
        if isinstance(entity, HasBeaconUpdate):
            entity.beacon_update(request)
        elif hasattr(entity, "beacon_update") and callable(entity.beacon_update):
            entity.beacon_update(request)
        entity.save()

    # Create the beacon
    beacon = Beacon(target_url=final_url or "")
    beacon.save()

    # Link beacon to target if it has a beacons field
    if target is not None and hasattr(target, "beacons"):
        target.beacons.add(beacon)

    # Link beacon to entity if it has a beacons field
    if entity is not None and hasattr(entity, "beacons"):
        entity.beacons.add(beacon)

    # Return pixel response
    if pixel:
        gif_data = base64.b64decode(CLEAR_GIF_CONTENTS)
        return HttpResponse(gif_data, content_type="image/gif")

    # Redirect response
    assert final_url is not None  # Already checked above

    # Optionally resolve local URLs and call the view directly
    if getattr(settings, "WEBBUGGER_RESOLVE_LOCAL", False):
        try:
            resolve_match = resolve(final_url)
            if resolve_match:
                return resolve_match.func(
                    request, *resolve_match.args, **resolve_match.kwargs
                )
        except Exception:
            pass  # Fall through to redirect

    return HttpResponseRedirect(final_url)


def create_beacon(
    request: HttpRequest | None = None,
    target_url: str = "",
    *,
    links: list[models.Model] | None = None,
) -> Beacon:
    """Create a beacon and optionally link it to models.

    This is a lower-level function for creating beacons programmatically
    when you need more control than the trigger view provides.

    Args:
        request: Optional HTTP request for entity updates.
        target_url: URL to store in the beacon.
        links: List of model instances to link to the beacon.
            Each must have a 'beacons' ManyToManyField (via @trackable).

    Returns:
        The created Beacon instance.

    Example:
        from webbugger.views import create_beacon

        beacon = create_beacon(
            target_url="https://example.com/product/1/",
            links=[product, campaign, visitor],
        )
        # Now you can query:
        # product.beacons.filter(pk=beacon.pk).exists()
        # Beacon.objects.filter(products=product, campaigns=campaign)
    """
    beacon = Beacon(target_url=target_url)
    beacon.save()

    if links:
        for obj in links:
            # Call beacon_update if supported and request provided
            if request is not None:
                if isinstance(obj, HasBeaconUpdate):
                    obj.beacon_update(request)
                    obj.save()
                elif hasattr(obj, "beacon_update") and callable(obj.beacon_update):
                    obj.beacon_update(request)
                    obj.save()

            # Link to beacon
            if hasattr(obj, "beacons"):
                obj.beacons.add(beacon)

    return beacon
