"""Product images: validation, normalization, cleanup, display, and upload paths."""

import re
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static
from django.urls import reverse
from PIL import Image

from .images import MEGABYTE, validate_product_image
from .models import Product

pytestmark = pytest.mark.django_db


def rejection(upload):
    """The message ``validate_product_image`` rejects an upload with."""
    with pytest.raises(ValidationError) as caught:
        validate_product_image(upload)
    return caught.value.messages[0]


def stored_image(product):
    """Open a product's stored image file: (format, size, has EXIF)."""
    with product.image.open("rb") as file, Image.open(file) as image:
        return image.format, image.size, bool(image.getexif())


def with_image(product, upload):
    product.image = upload
    product.save()
    return product


def product_data(product, **overrides):
    """The back-office form's POST data for an existing product."""
    data = {
        "name": product.name,
        "slug": product.slug,
        "tagline": product.tagline,
        "description": product.description,
        "price": str(product.price),
        "category": str(product.category.pk),
        "is_available": "on",
    }
    data.update(overrides)
    return data


# --- Validation ---------------------------------------------------------------


def test_accepts_jpeg_png_and_webp(image_upload):
    for fmt in ("JPEG", "PNG", "WEBP"):
        validate_product_image(image_upload(fmt=fmt))


def test_rejects_oversized_file_before_reading_it():
    # Not an image at all — the size check runs first, before any decoding.
    upload = SimpleUploadedFile("huge.png", b"0" * int(7.3 * MEGABYTE))

    assert rejection(upload) == (
        "This image is 7.3 MB. Please upload an image of 5 MB or smaller."
    )


def test_rejects_formats_other_than_jpeg_png_webp(image_upload):
    for fmt in ("GIF", "BMP", "TIFF"):
        assert rejection(image_upload(fmt=fmt)) == (
            "Please upload a JPEG, PNG, or WebP image."
        ), fmt


def test_format_is_judged_by_content_not_extension(image_upload):
    validate_product_image(image_upload(fmt="JPEG", name="photo.txt"))

    gif = image_upload(fmt="GIF", name="sneaky.png")
    assert rejection(gif) == "Please upload a JPEG, PNG, or WebP image."


def test_rejects_non_image_files():
    upload = SimpleUploadedFile("notes.png", b"definitely not an image")

    assert "couldn't be read as an image" in rejection(upload)


def test_rejects_truncated_images(image_upload):
    data = image_upload(size=(800, 1000), fmt="JPEG").read()
    upload = SimpleUploadedFile("cut.jpg", data[: len(data) // 2])

    assert "couldn't be read as an image" in rejection(upload)


def test_rejects_images_too_small(image_upload):
    assert rejection(image_upload(size=(320, 240))) == (
        "This image is 320 × 240 pixels. Please upload an image at least "
        "600 pixels on its shortest side."
    )


def test_rejects_images_too_large(image_upload):
    assert rejection(image_upload(size=(6001, 700))) == (
        "This image is 6001 × 700 pixels. Please upload an image no more "
        "than 6000 pixels on either side."
    )


def test_accepts_the_boundary_dimensions(image_upload):
    validate_product_image(image_upload(size=(600, 6000)))


# --- Normalization ------------------------------------------------------------


def test_upload_is_stored_as_webp_named_for_the_slug(product, image_upload):
    with_image(product, image_upload(fmt="PNG"))

    assert re.fullmatch(
        r"products/seraphine-home-hub-[0-9a-f]{6}\.webp", product.image.name
    )
    assert stored_image(product)[0] == "WEBP"


def test_large_upload_is_shrunk_to_1200_on_its_longest_side(product, image_upload):
    with_image(product, image_upload(size=(1600, 2000)))

    assert stored_image(product)[1] == (960, 1200)


def test_small_upload_is_never_enlarged(product, image_upload):
    with_image(product, image_upload(size=(800, 1000)))

    assert stored_image(product)[1] == (800, 1000)


def test_exif_orientation_is_applied_and_metadata_stripped(product, image_upload):
    # Orientation 6: stored 800 wide x 1000 tall, displayed rotated 90°.
    with_image(product, image_upload(size=(800, 1000), fmt="JPEG", orientation=6))

    fmt, size, has_exif = stored_image(product)
    assert size == (1000, 800)
    assert not has_exif


def test_editing_other_fields_does_not_reprocess_the_image(
    product, image_upload, monkeypatch, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    name = product.image.name

    def fail(*args, **kwargs):
        raise AssertionError("existing image was reprocessed")

    monkeypatch.setattr("products.models.normalize_product_image", fail)
    with django_capture_on_commit_callbacks(execute=True):
        product.price = Decimal("1.00")
        product.save()

    product.refresh_from_db()
    assert product.image.name == name
    assert product.image.storage.exists(name)


def test_back_office_edit_keeps_the_existing_image(
    client, staff_user, product, image_upload, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    name = product.image.name
    client.force_login(staff_user)

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("products:manage_product_update", kwargs={"pk": product.pk}),
            product_data(product, price="10.00"),
        )

    assert response.status_code == HTTPStatus.FOUND
    product.refresh_from_db()
    assert product.price == Decimal("10.00")
    assert product.image.name == name
    assert product.image.storage.exists(name)


# --- Cleanup of old files -----------------------------------------------------


def test_replacing_an_image_deletes_the_old_file(
    product, image_upload, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    old_name = product.image.name

    with django_capture_on_commit_callbacks(execute=True):
        with_image(product, image_upload())

    storage = product.image.storage
    assert product.image.name != old_name
    assert storage.exists(product.image.name)
    assert not storage.exists(old_name)


def test_old_file_survives_until_commit(product, image_upload):
    with_image(product, image_upload())
    old_name = product.image.name

    # Inside the test transaction, nothing has committed yet.
    with_image(product, image_upload())

    assert product.image.storage.exists(old_name)


def test_clearing_an_image_deletes_the_file(
    client, staff_user, product, image_upload, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    old_name = product.image.name
    client.force_login(staff_user)

    with django_capture_on_commit_callbacks(execute=True):
        client.post(
            reverse("products:manage_product_update", kwargs={"pk": product.pk}),
            product_data(product, **{"image-clear": "on"}),
        )

    product.refresh_from_db()
    assert not product.image
    assert not product.image.storage.exists(old_name)


def test_deleting_a_product_deletes_its_file(
    product, image_upload, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    name, storage = product.image.name, product.image.storage

    with django_capture_on_commit_callbacks(execute=True):
        product.delete()

    assert not storage.exists(name)


def test_bulk_deleting_products_deletes_their_files(
    product, image_upload, django_capture_on_commit_callbacks
):
    with_image(product, image_upload())
    name, storage = product.image.name, product.image.storage

    with django_capture_on_commit_callbacks(execute=True):
        Product.objects.all().delete()

    assert not storage.exists(name)


# --- Display ------------------------------------------------------------------


def test_image_url_falls_back_to_category_placeholder(product):
    assert product.image_url == static("images/placeholders/home-assistants.svg")


def test_catalog_and_detail_show_the_placeholder_without_an_image(client, product):
    placeholder = static(product.category.placeholder_image)

    for url in (reverse("products:catalog"), product.get_absolute_url()):
        assert placeholder in client.get(url).content.decode(), url


def test_catalog_and_detail_show_the_uploaded_image(client, product, image_upload):
    with_image(product, image_upload())
    placeholder = static(product.category.placeholder_image)

    for url in (reverse("products:catalog"), product.get_absolute_url()):
        html = client.get(url).content.decode()
        assert product.image.url in html, url
        assert placeholder not in html, url


# --- Upload paths: back office and Django admin -------------------------------


def test_back_office_upload_creates_product_with_image(
    client, staff_user, category, image_upload
):
    client.force_login(staff_user)
    data = {
        "name": "MindSync Duo",
        "slug": "mindsync-duo",
        "price": "499.00",
        "category": str(category.pk),
        "image": image_upload(size=(1536, 1024)),
    }

    response = client.post(reverse("products:manage_product_create"), data)

    assert response.status_code == HTTPStatus.FOUND
    product = Product.objects.get(slug="mindsync-duo")
    assert stored_image(product)[:2] == ("WEBP", (1200, 800))


def test_back_office_rejects_bad_upload_with_plain_message(
    client, staff_user, category, image_upload
):
    client.force_login(staff_user)
    data = {
        "name": "MindSync Duo",
        "slug": "mindsync-duo",
        "price": "499.00",
        "category": str(category.pk),
        "image": image_upload(size=(320, 240)),
    }

    response = client.post(reverse("products:manage_product_create"), data)

    assert response.status_code == HTTPStatus.OK
    assert "This image is 320 × 240 pixels." in response.content.decode()
    assert not Product.objects.exists()


def test_back_office_form_shows_preview_and_clear_option(
    client, staff_user, product, image_upload
):
    with_image(product, image_upload())
    client.force_login(staff_user)

    html = client.get(
        reverse("products:manage_product_update", kwargs={"pk": product.pk})
    ).content.decode()

    assert 'enctype="multipart/form-data"' in html
    assert f'<img src="{product.image.url}" alt="Current image"' in html
    assert 'name="image-clear"' in html
    assert "Remove image (show the category placeholder)" in html
    assert "file-input" in html
    # Django's stock ClearableFileInput markup is replaced, not shown alongside.
    assert "Currently:" not in html
    assert "Change:" not in html


def test_back_office_form_without_image_shows_placeholder_box(
    client, staff_user, product
):
    client.force_login(staff_user)

    html = client.get(
        reverse("products:manage_product_update", kwargs={"pk": product.pk})
    ).content.decode()

    assert "Category placeholder" in html
    assert 'name="image"' in html
    assert 'name="image-clear"' not in html
    assert "Currently:" not in html


def test_admin_enforces_the_same_validation(client, category, image_upload):
    admin = get_user_model().objects.create_superuser(
        username="admin", password="admin123"
    )
    client.force_login(admin)
    data = {
        "name": "MindSync Duo",
        "slug": "mindsync-duo",
        "tagline": "",
        "description": "",
        "price": "499.00",
        "category": str(category.pk),
        "is_available": "on",
    }

    response = client.post(
        reverse("admin:products_product_add"),
        {**data, "image": image_upload(fmt="GIF", name="duo.png")},
    )

    assert response.status_code == HTTPStatus.OK
    assert "Please upload a JPEG, PNG, or WebP image." in response.content.decode()
    assert not Product.objects.exists()

    response = client.post(
        reverse("admin:products_product_add"),
        {**data, "image": image_upload(size=(1200, 1500))},
    )

    assert response.status_code == HTTPStatus.FOUND
    assert stored_image(Product.objects.get())[0] == "WEBP"
