"""Tests for webbugger models."""

from __future__ import annotations

import pytest
from django.utils import timezone

from webbugger import Beacon, IP, IPEntity


@pytest.mark.django_db
class TestBeacon:
    """Tests for the Beacon model."""

    def test_create_beacon(self) -> None:
        """Test creating a beacon."""
        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        assert beacon.pk is not None
        assert beacon.target_url == "https://example.com/"
        assert beacon.time_created is not None

    def test_beacon_time_created_auto_set(self) -> None:
        """Test that time_created is automatically set on first save."""
        before = timezone.now()
        beacon = Beacon(target_url="https://example.com/")
        beacon.save()
        after = timezone.now()

        assert before <= beacon.time_created <= after

    def test_beacon_time_created_not_updated_on_save(self) -> None:
        """Test that time_created is not updated on subsequent saves."""
        beacon = Beacon(target_url="https://example.com/")
        beacon.save()
        original_time = beacon.time_created

        beacon.target_url = "https://example.org/"
        beacon.save()

        assert beacon.time_created == original_time

    def test_beacon_get_absolute_url(self) -> None:
        """Test that get_absolute_url returns the target URL."""
        beacon = Beacon(target_url="https://example.com/page/")
        beacon.save()

        assert beacon.get_absolute_url() == "https://example.com/page/"

    def test_beacon_str(self) -> None:
        """Test beacon string representation."""
        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        assert str(beacon) == f"Beacon #{beacon.pk}"

    def test_beacon_ordering(self) -> None:
        """Test that beacons are ordered by time_created descending."""
        beacon1 = Beacon(target_url="https://example.com/1/")
        beacon1.save()

        beacon2 = Beacon(target_url="https://example.com/2/")
        beacon2.save()

        beacons = list(Beacon.objects.all())
        assert beacons[0] == beacon2  # Most recent first
        assert beacons[1] == beacon1


@pytest.mark.django_db
class TestIP:
    """Tests for the IP model."""

    def test_create_ip(self) -> None:
        """Test creating an IP."""
        ip = IP(address="192.168.1.1")
        ip.save()

        assert ip.pk is not None
        assert ip.address == "192.168.1.1"
        assert ip.owned_time is not None

    def test_ip_ipv6(self) -> None:
        """Test creating an IPv6 address."""
        ip = IP(address="2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        ip.save()

        assert ip.address == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"

    def test_ip_str(self) -> None:
        """Test IP string representation."""
        ip = IP(address="10.0.0.1")
        ip.save()

        assert str(ip) == "10.0.0.1"


@pytest.mark.django_db
class TestIPEntity:
    """Tests for the IPEntity model."""

    def test_create_ip_entity(self) -> None:
        """Test creating an IP entity."""
        entity = IPEntity()
        entity.save()

        assert entity.pk is not None

    def test_ip_entity_has_beacons_field(self) -> None:
        """Test that IPEntity has a beacons field from @trackable."""
        entity = IPEntity()
        entity.save()

        assert hasattr(entity, "beacons")
        assert entity.beacons.count() == 0

    def test_ip_entity_beacon_update(self, mock_request) -> None:
        """Test that beacon_update captures IP from request."""
        entity = IPEntity()
        entity.beacon_update(mock_request)

        assert entity.ip_addresses.count() == 1
        ip = entity.ip_addresses.first()
        assert ip is not None
        assert ip.address == "192.168.1.1"

    def test_ip_entity_beacon_update_multiple_ips(self, mock_request) -> None:
        """Test that an entity can track multiple IPs."""
        entity = IPEntity()
        entity.save()

        # First request
        mock_request.META["REMOTE_ADDR"] = "192.168.1.1"
        entity.beacon_update(mock_request)

        # Second request from different IP
        mock_request.META["REMOTE_ADDR"] = "192.168.1.2"
        entity.beacon_update(mock_request)

        assert entity.ip_addresses.count() == 2

    def test_ip_entity_str(self) -> None:
        """Test IP entity string representation."""
        entity = IPEntity()
        entity.save()

        assert str(entity) == "0 IP addresses"

    def test_ip_entity_link_to_beacon(self) -> None:
        """Test linking an IPEntity to a Beacon."""
        entity = IPEntity()
        entity.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        entity.beacons.add(beacon)

        assert entity.beacons.count() == 1
        assert beacon in entity.beacons.all()

    def test_beacon_reverse_relation_to_ip_entity(self) -> None:
        """Test querying beacons by IPEntity."""
        entity = IPEntity()
        entity.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        entity.beacons.add(beacon)

        # Query from Beacon side
        found = Beacon.objects.filter(ip_entities=entity)
        assert beacon in found
