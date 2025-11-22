"""Tests for webbugger views."""

from __future__ import annotations

import pytest
from django.http import Http404
from django.test import RequestFactory

from webbugger import Beacon, IPEntity, create_beacon, trigger

from .models import Product, Visitor


@pytest.mark.django_db
class TestTriggerView:
    """Tests for the trigger view."""

    def test_trigger_redirect_with_target_url(self, mock_request) -> None:
        """Test trigger with explicit target_url."""
        response = trigger(mock_request, target_url="https://example.com/")

        assert response.status_code == 302
        assert response["Location"] == "https://example.com/"
        assert Beacon.objects.count() == 1

    def test_trigger_redirect_creates_beacon(self, mock_request) -> None:
        """Test that trigger creates a beacon."""
        trigger(mock_request, target_url="https://example.com/page/")

        beacon = Beacon.objects.first()
        assert beacon is not None
        assert beacon.target_url == "https://example.com/page/"

    def test_trigger_pixel_mode(self, mock_request) -> None:
        """Test trigger in pixel mode returns GIF."""
        response = trigger(mock_request, pixel=True)

        assert response.status_code == 200
        assert response["Content-Type"] == "image/gif"
        assert Beacon.objects.count() == 1

    def test_trigger_pixel_mode_no_url_required(self, mock_request) -> None:
        """Test that pixel mode doesn't require a target URL."""
        response = trigger(mock_request, pixel=True)

        assert response.status_code == 200
        beacon = Beacon.objects.first()
        assert beacon is not None
        assert beacon.target_url == ""

    def test_trigger_with_target_model(self, mock_request) -> None:
        """Test trigger with a target model instance."""
        product = Product(name="Test", url="https://example.com/product/")
        product.save()

        response = trigger(mock_request, target=product)

        assert response.status_code == 302
        assert response["Location"] == "https://example.com/product/"

    def test_trigger_links_beacon_to_target(self, mock_request) -> None:
        """Test that beacon is linked to target model."""
        product = Product(name="Test", url="https://example.com/")
        product.save()

        trigger(mock_request, target=product)

        assert product.beacons.count() == 1

    def test_trigger_with_entity_class(self, mock_request) -> None:
        """Test trigger creates entity from class."""
        trigger(
            mock_request,
            target_url="https://example.com/",
            entity_class=IPEntity,
        )

        assert IPEntity.objects.count() == 1

    def test_trigger_with_entity_id(self, mock_request) -> None:
        """Test trigger fetches existing entity."""
        entity = IPEntity()
        entity.save()

        trigger(
            mock_request,
            target_url="https://example.com/",
            entity_class=IPEntity,
            entity_id=entity.pk,
        )

        # Should not create a new entity
        assert IPEntity.objects.count() == 1

    def test_trigger_calls_beacon_update(self, mock_request) -> None:
        """Test that trigger calls beacon_update on entity."""
        trigger(
            mock_request,
            target_url="https://example.com/",
            entity_class=Visitor,
        )

        visitor = Visitor.objects.first()
        assert visitor is not None
        assert visitor.user_agent == "Test Agent/1.0"
        assert visitor.ip_address == "192.168.1.1"

    def test_trigger_links_beacon_to_entity(self, mock_request) -> None:
        """Test that beacon is linked to entity."""
        trigger(
            mock_request,
            target_url="https://example.com/",
            entity_class=Visitor,
        )

        visitor = Visitor.objects.first()
        assert visitor is not None
        assert visitor.beacons.count() == 1

    def test_trigger_no_url_raises_404(self, mock_request) -> None:
        """Test that trigger raises 404 without URL in redirect mode."""
        with pytest.raises(Http404):
            trigger(mock_request)

    def test_trigger_with_entity_instance(self, mock_request) -> None:
        """Test trigger with pre-created entity instance."""
        visitor = Visitor()
        visitor.save()

        trigger(
            mock_request,
            target_url="https://example.com/",
            entity=visitor,
        )

        visitor.refresh_from_db()
        assert visitor.user_agent == "Test Agent/1.0"


@pytest.mark.django_db
class TestCreateBeacon:
    """Tests for the create_beacon function."""

    def test_create_beacon_simple(self) -> None:
        """Test creating a beacon without links."""
        beacon = create_beacon(target_url="https://example.com/")

        assert beacon.pk is not None
        assert beacon.target_url == "https://example.com/"

    def test_create_beacon_with_links(self) -> None:
        """Test creating a beacon with linked models."""
        product = Product(name="Test", url="https://example.com/")
        product.save()

        beacon = create_beacon(
            target_url="https://example.com/",
            links=[product],
        )

        assert product.beacons.count() == 1
        assert beacon in product.beacons.all()

    def test_create_beacon_with_multiple_links(self) -> None:
        """Test creating a beacon linked to multiple models."""
        product = Product(name="Test", url="https://example.com/")
        product.save()

        visitor = Visitor()
        visitor.save()

        beacon = create_beacon(
            target_url="https://example.com/",
            links=[product, visitor],
        )

        assert product.beacons.count() == 1
        assert visitor.beacons.count() == 1
        assert beacon in product.beacons.all()
        assert beacon in visitor.beacons.all()

    def test_create_beacon_calls_beacon_update(self, mock_request) -> None:
        """Test that create_beacon calls beacon_update when request provided."""
        visitor = Visitor()
        visitor.save()

        create_beacon(
            request=mock_request,
            target_url="https://example.com/",
            links=[visitor],
        )

        visitor.refresh_from_db()
        assert visitor.user_agent == "Test Agent/1.0"

    def test_create_beacon_without_request_no_update(self) -> None:
        """Test that create_beacon doesn't call beacon_update without request."""
        visitor = Visitor()
        visitor.save()

        create_beacon(
            target_url="https://example.com/",
            links=[visitor],
        )

        visitor.refresh_from_db()
        assert visitor.user_agent == ""

    def test_create_beacon_query_by_related(self) -> None:
        """Test querying beacons by related models."""
        product1 = Product(name="Product 1")
        product1.save()

        product2 = Product(name="Product 2")
        product2.save()

        beacon1 = create_beacon(target_url="https://example.com/1/", links=[product1])
        beacon2 = create_beacon(target_url="https://example.com/2/", links=[product2])

        # Query beacons for product1
        found = Beacon.objects.filter(products=product1)
        assert list(found) == [beacon1]

        # Query beacons for product2
        found = Beacon.objects.filter(products=product2)
        assert list(found) == [beacon2]
