"""Models for django-webbugger tracking system."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from django.db import models
from django.http import HttpRequest
from django.utils import timezone


M = TypeVar("M", bound=models.Model)


def trackable(
    cls: type[M] | None = None,
    *,
    field_name: str = "beacons",
    related_name: str | None = None,
) -> type[M] | Callable[[type[M]], type[M]]:
    """Decorator that adds a ManyToManyField to Beacon on a model.

    This creates a real database relationship that can be queried with
    standard Django ORM joins - no contenttypes framework needed.

    Usage:
        @trackable
        class Product(models.Model):
            name = models.CharField(max_length=255)

        # Now you can use:
        product.beacons.all()
        Beacon.objects.filter(products=product)

    Args:
        cls: The model class to decorate.
        field_name: Name of the field on the decorated model (default: "beacons").
        related_name: Name for the reverse relation on Beacon. Defaults to
            the model's lowercase name + 's' (e.g., "products" for Product).

    Returns:
        The decorated model class with a ManyToManyField to Beacon.
    """

    def decorator(model_cls: type[M]) -> type[M]:
        # Determine the related_name for reverse lookups from Beacon
        reverse_name = related_name
        if reverse_name is None:
            reverse_name = f"{model_cls.__name__.lower()}s"

        # Create the ManyToManyField
        field = models.ManyToManyField(
            "webbugger.Beacon",
            related_name=reverse_name,
            blank=True,
        )

        # Add it to the model
        field.contribute_to_class(model_cls, field_name)

        return model_cls

    # Handle both @beacon_trackable and @beacon_trackable(...) syntax
    if cls is not None:
        return decorator(cls)

    return decorator


class Beacon(models.Model):
    """A tracking beacon that records visits.

    This model stores the essential tracking data. Related models connect
    to Beacon via ManyToManyField using the @trackable decorator,
    providing real database foreign keys with efficient JOIN queries.
    """

    target_url = models.URLField(
        max_length=2000,
        blank=True,
        default="",
        help_text="URL to redirect to after tracking (for redirect mode).",
    )
    time_created = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = "Beacon"
        verbose_name_plural = "Beacons"
        ordering = ["-time_created"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the beacon, setting time_created on first save."""
        if not self.pk:
            self.time_created = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return the target URL for this beacon."""
        return self.target_url

    def __str__(self) -> str:
        return f"Beacon #{self.pk}"


class IP(models.Model):
    """Stores an IP address and the time it was recorded.

    Supports both IPv4 and IPv6 addresses.
    """

    address = models.CharField(max_length=72)
    owned_time = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = "IP"
        verbose_name_plural = "IPs"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the IP, setting owned_time on first save."""
        if not self.pk:
            self.owned_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.address


@trackable(related_name="ip_entities")
class IPEntity(models.Model):
    """A tracking entity that stores IP addresses.

    This entity can track multiple IP addresses when the same entity
    visits multiple times. Implements beacon_update to capture the
    visitor's IP address from the request.

    Example usage with the trigger view:
        # In your urls.py
        path(
            "track/<int:target_id>/",
            trigger,
            {"entity_class": IPEntity},
            name="track",
        )
    """

    ip_addresses = models.ManyToManyField(IP, related_name="entities", blank=True)

    class Meta:
        verbose_name = "IP entity"
        verbose_name_plural = "IP entities"

    def beacon_update(self, request: HttpRequest) -> None:
        """Update this entity with the IP address from the request."""
        self.save()

        ip_address: str = request.META.get("REMOTE_ADDR", "")
        if ip_address:
            next_ip, _ = IP.objects.get_or_create(address=ip_address)
            self.ip_addresses.add(next_ip)

    def __str__(self) -> str:
        return f"{self.ip_addresses.count()} IP addresses"
