# django-webbugger

A tracking beacon library for Django using real database foreign keys.

## Requirements

- Python 3.10+
- Django 4.2+

## Installation

```bash
pip install django-webbugger
```

Add `webbugger` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "webbugger",
]
```

Run migrations:

```bash
python manage.py migrate webbugger
```

## Quick Start

### 1. Make your models trackable

```python
from django.db import models
from webbugger import trackable

@trackable
class Product(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()

    def get_absolute_url(self) -> str:
        return self.url

@trackable
class Campaign(models.Model):
    name = models.CharField(max_length=255)
```

The `@trackable` decorator adds a `beacons` ManyToManyField to your model. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create beacons

```python
from webbugger import create_beacon

product = Product.objects.get(pk=1)
campaign = Campaign.objects.get(pk=1)

beacon = create_beacon(
    target_url=product.get_absolute_url(),
    links=[product, campaign],
)
```

### 3. Query with JOINs

```python
from webbugger import Beacon

# All beacons for a product
product.beacons.all()

# Filter beacons by related models
Beacon.objects.filter(products=product)
Beacon.objects.filter(campaigns=campaign)

# Complex queries
Beacon.objects.filter(
    products=product,
    campaigns=campaign,
    time_created__gte=last_week,
)
```

## The `@trackable` Decorator

```python
from webbugger import trackable

# Basic usage
@trackable
class Product(models.Model):
    pass

# Custom field name and reverse relation
@trackable(field_name="tracking_beacons", related_name="tracked_products")
class Product(models.Model):
    pass
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `field_name` | `"beacons"` | Name of the ManyToManyField on your model |
| `related_name` | model name + `"s"` | Name for reverse lookups from Beacon |

## Views

### Trigger View

Creates a beacon and redirects or returns a tracking pixel.

```python
from django.urls import path
from webbugger import trigger, IPEntity

urlpatterns = [
    # Redirect tracking
    path(
        "go/",
        trigger,
        {"target_url": "https://example.com/"},
        name="track_redirect",
    ),

    # Pixel tracking
    path(
        "pixel/<int:entity_id>/",
        trigger,
        {"entity_class": IPEntity, "pixel": True},
        name="track_pixel",
    ),
]
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `target_url` | URL to redirect to (required for redirect mode) |
| `target` | Model instance to get URL from and link to beacon |
| `entity` | Entity instance to link to beacon |
| `entity_class` | Entity class to create/fetch |
| `entity_id` | ID for fetching existing entity |
| `pixel` | Return 1x1 transparent GIF instead of redirect |

### Programmatic Usage

```python
from webbugger import create_beacon

beacon = create_beacon(
    request=request,
    target_url="https://example.com/",
    links=[product, campaign, visitor],
)
```

## Entity Protocol

Entities can implement `beacon_update(request)` to capture request data:

```python
from django.db import models
from django.http import HttpRequest
from webbugger import trackable

@trackable
class Visitor(models.Model):
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)

    def beacon_update(self, request: HttpRequest) -> None:
        self.user_agent = request.META.get("HTTP_USER_AGENT", "")
        self.ip_address = request.META.get("REMOTE_ADDR")
```

## Built-in Models

### IPEntity

A ready-to-use entity that captures IP addresses:

```python
from webbugger import IPEntity

entity = IPEntity.objects.get(pk=1)
entity.ip_addresses.all()
entity.beacons.all()
```

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `WEBBUGGER_RESOLVE_LOCAL` | `False` | Resolve local URLs and call view directly |

## Why Not Contenttypes?

Django's contenttypes with GenericForeignKey requires multiple queries and Python-side resolution:

```python
# Contenttypes: N+1 queries
beacons = Beacon.objects.filter(...)
for beacon in beacons:
    target = beacon.target  # Query per beacon

# @trackable: Single JOIN
beacons = Beacon.objects.filter(products=product)
```

## License

MIT
