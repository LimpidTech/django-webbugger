"""Django admin configuration for webbugger models."""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from .models import Beacon, IP, IPEntity


@admin.register(Beacon)
class BeaconAdmin(admin.ModelAdmin[Beacon]):
    """Admin configuration for Beacon model."""

    list_display: ClassVar[list[str]] = ["id", "target_url", "time_created"]
    list_filter: ClassVar[list[str]] = ["time_created"]
    search_fields: ClassVar[list[str]] = ["target_url"]
    readonly_fields: ClassVar[list[str]] = ["time_created"]
    date_hierarchy = "time_created"


@admin.register(IP)
class IPAdmin(admin.ModelAdmin[IP]):
    """Admin configuration for IP model."""

    list_display: ClassVar[list[str]] = ["id", "address", "owned_time"]
    list_filter: ClassVar[list[str]] = ["owned_time"]
    search_fields: ClassVar[list[str]] = ["address"]
    readonly_fields: ClassVar[list[str]] = ["owned_time"]


@admin.register(IPEntity)
class IPEntityAdmin(admin.ModelAdmin[IPEntity]):
    """Admin configuration for IPEntity model."""

    list_display: ClassVar[list[str]] = ["id", "ip_count", "beacon_count"]
    filter_horizontal: ClassVar[list[str]] = ["ip_addresses", "beacons"]

    @admin.display(description="IP Count")
    def ip_count(self, obj: IPEntity) -> int:
        """Return the count of IP addresses for this entity."""
        return obj.ip_addresses.count()

    @admin.display(description="Beacon Count")
    def beacon_count(self, obj: IPEntity) -> int:
        """Return the count of beacons for this entity."""
        return obj.beacons.count()
