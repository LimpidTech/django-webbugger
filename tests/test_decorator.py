"""Tests for the @trackable decorator."""

from __future__ import annotations

import pytest
from django.db import models

from webbugger import Beacon, trackable

from .models import Campaign, Product, UntrackableModel


@pytest.mark.django_db
class TestTrackableDecorator:
    """Tests for the @trackable decorator."""

    def test_adds_beacons_field(self) -> None:
        """Test that @trackable adds a beacons field."""
        product = Product(name="Test")
        product.save()

        assert hasattr(product, "beacons")

    def test_beacons_field_is_many_to_many(self) -> None:
        """Test that the beacons field is a ManyToManyField."""
        field = Product._meta.get_field("beacons")
        assert isinstance(field, models.ManyToManyField)

    def test_default_related_name(self) -> None:
        """Test that default related_name is model name + 's'."""
        product = Product(name="Test")
        product.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        product.beacons.add(beacon)

        # Should be able to query via 'products'
        found = Beacon.objects.filter(products=product)
        assert beacon in found

    def test_custom_field_name(self) -> None:
        """Test @trackable with custom field_name."""
        campaign = Campaign(name="Test")
        campaign.save()

        # Campaign uses field_name="tracking"
        assert hasattr(campaign, "tracking")
        assert not hasattr(campaign, "beacons")

    def test_custom_related_name(self) -> None:
        """Test @trackable with custom related_name."""
        campaign = Campaign(name="Test")
        campaign.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        campaign.tracking.add(beacon)

        # Should be able to query via 'campaigns'
        found = Beacon.objects.filter(campaigns=campaign)
        assert beacon in found

    def test_untracked_model_no_beacons_field(self) -> None:
        """Test that models without @trackable don't have beacons field."""
        model = UntrackableModel(name="Test")
        model.save()

        assert not hasattr(model, "beacons")

    def test_add_beacon_to_model(self) -> None:
        """Test adding a beacon to a tracked model."""
        product = Product(name="Test")
        product.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        product.beacons.add(beacon)

        assert product.beacons.count() == 1
        assert beacon in product.beacons.all()

    def test_remove_beacon_from_model(self) -> None:
        """Test removing a beacon from a tracked model."""
        product = Product(name="Test")
        product.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        product.beacons.add(beacon)
        product.beacons.remove(beacon)

        assert product.beacons.count() == 0

    def test_multiple_beacons_per_model(self) -> None:
        """Test adding multiple beacons to a model."""
        product = Product(name="Test")
        product.save()

        beacon1 = Beacon(target_url="https://example.com/1/")
        beacon1.save()

        beacon2 = Beacon(target_url="https://example.com/2/")
        beacon2.save()

        product.beacons.add(beacon1, beacon2)

        assert product.beacons.count() == 2

    def test_beacon_linked_to_multiple_models(self) -> None:
        """Test that a beacon can be linked to multiple models."""
        product = Product(name="Product")
        product.save()

        campaign = Campaign(name="Campaign")
        campaign.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        product.beacons.add(beacon)
        campaign.tracking.add(beacon)

        # Query beacon's related models
        assert Beacon.objects.filter(products=product).exists()
        assert Beacon.objects.filter(campaigns=campaign).exists()

    def test_query_with_join(self) -> None:
        """Test efficient JOIN query."""
        product = Product(name="Test")
        product.save()

        beacon = Beacon(target_url="https://example.com/")
        beacon.save()

        product.beacons.add(beacon)

        # This should be a single JOIN query
        beacons = Beacon.objects.filter(products=product)
        assert list(beacons) == [beacon]

    def test_complex_query(self) -> None:
        """Test complex query with multiple filters."""
        product = Product(name="Product")
        product.save()

        campaign = Campaign(name="Campaign")
        campaign.save()

        # Beacon linked to both
        beacon1 = Beacon(target_url="https://example.com/1/")
        beacon1.save()
        product.beacons.add(beacon1)
        campaign.tracking.add(beacon1)

        # Beacon linked only to product
        beacon2 = Beacon(target_url="https://example.com/2/")
        beacon2.save()
        product.beacons.add(beacon2)

        # Query beacons linked to both product AND campaign
        found = Beacon.objects.filter(products=product, campaigns=campaign)
        assert list(found) == [beacon1]


@pytest.mark.django_db
class TestDecoratorSyntax:
    """Tests for different decorator syntax options."""

    def test_bare_decorator(self) -> None:
        """Test @trackable without parentheses works."""
        # Product uses bare @trackable
        product = Product(name="Test")
        product.save()

        assert hasattr(product, "beacons")

    def test_decorator_with_args(self) -> None:
        """Test @trackable(...) with arguments works."""
        # Campaign uses @trackable(field_name="tracking", related_name="campaigns")
        campaign = Campaign(name="Test")
        campaign.save()

        assert hasattr(campaign, "tracking")
