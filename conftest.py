"""Project-wide pytest fixtures.

Shared test data lives here as plain fixtures — no factories. The suite
grows with the project; tests never invoke the seed command.
"""

from decimal import Decimal
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from coupons.models import Coupon
from orders.models import Cart, CartItem
from products.models import Category, Product, Tag


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Every test writes uploads to a throwaway MEDIA_ROOT, never ./media."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


@pytest.fixture
def image_upload():
    """Build an in-memory image upload with Pillow.

    ``image_upload(size=(800, 1000), fmt="PNG", orientation=6)`` returns a
    ``SimpleUploadedFile``; ``orientation`` writes an EXIF orientation tag.
    """

    def build(size=(800, 1000), fmt="PNG", name=None, orientation=None):
        image = Image.new("RGB", size, "#7c3aed")
        exif = Image.Exif()
        if orientation is not None:
            exif[0x0112] = orientation
        buffer = BytesIO()
        image.save(buffer, format=fmt, exif=exif.tobytes())
        name = name or f"upload.{fmt.lower()}"
        return SimpleUploadedFile(name, buffer.getvalue())

    return build


@pytest.fixture
def customer(db):
    return get_user_model().objects.create_user(
        username="customer", password="customer123"
    )


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="employee",
        password="employee123",
        is_staff=True,
        job_title="Junior Thought Curator",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Home Assistants", slug="home-assistants")


@pytest.fixture
def product(category):
    return Product.objects.create(
        name="Seraphine Home Hub",
        slug="seraphine-home-hub",
        tagline="She's always listening. In a good way.",
        description="The flagship Seraphine hub with a seven-microphone array.",
        price=Decimal("349.99"),
        category=category,
    )


@pytest.fixture
def other_product(category):
    return Product.objects.create(
        name="Charging Pillow",
        slug="charging-pillow",
        price=Decimal("69.00"),
        category=category,
    )


@pytest.fixture
def unavailable_product(category):
    return Product.objects.create(
        name="EchoPatch",
        slug="echopatch",
        tagline="Never miss a word. Anyone's.",
        price=Decimal("139.00"),
        is_available=False,
        category=category,
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="bestseller", slug="bestseller")


@pytest.fixture
def cart(customer):
    return Cart.for_user(customer)


@pytest.fixture
def cart_item(cart, product):
    return CartItem.objects.create(cart=cart, product=product, quantity=2)


@pytest.fixture
def coupon(db):
    """An order-wide 10%-off coupon that never expires."""
    return Coupon.objects.create(code="THOUGHTS10", percent_off=10)


@pytest.fixture
def product_coupon(product):
    """20% off the Seraphine Home Hub only."""
    coupon = Coupon.objects.create(code="HUB20", percent_off=20)
    coupon.products.add(product)
    return coupon
