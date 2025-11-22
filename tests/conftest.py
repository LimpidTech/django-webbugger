"""Pytest configuration and fixtures for django-webbugger tests."""

from __future__ import annotations

import pytest
from django.test import RequestFactory


@pytest.fixture
def request_factory() -> RequestFactory:
    """Provide a Django request factory."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory: RequestFactory):
    """Create a mock HTTP request."""
    request = request_factory.get("/")
    request.META["REMOTE_ADDR"] = "192.168.1.1"
    request.META["HTTP_USER_AGENT"] = "Test Agent/1.0"
    return request
