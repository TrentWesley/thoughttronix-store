"""Product image rules: validation, normalization, and the model field.

One optional image per product. ``validate_product_image`` is attached to
the field itself, so the back-office ``ProductForm`` and the Django admin
enforce the same rules with the same messages. ``normalize_product_image``
runs from ``Product.save()`` for newly uploaded files only.
"""

import math
import secrets
from io import BytesIO

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.db import models
from django.db.models.fields.files import FieldFile
from PIL import Image, ImageOps, UnidentifiedImageError

MEGABYTE = 1024 * 1024
MAX_PRODUCT_IMAGE_BYTES = 5 * MEGABYTE
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MIN_SHORTEST_SIDE = 600
MAX_SIDE = 6000
NORMALIZED_LONGEST_SIDE = 1200

FORMAT_MESSAGE = "Please upload a JPEG, PNG, or WebP image."
UNUSABLE_MESSAGE = (
    "This file couldn't be read as an image — it may be damaged, or not an "
    "image at all. " + FORMAT_MESSAGE
)


def validate_product_image(file: File) -> None:
    """Reject an uploaded product image that is too heavy, the wrong format,
    unreadable, or out of the allowed dimensions.

    Checks run cheapest first: byte size (before any decoding), the format
    Pillow detects (never the file extension), minimum then maximum
    dimensions (read from the header), and finally a full decode to catch
    truncated or corrupt data. Files already in storage were validated when
    they were uploaded and are skipped, so editing other product fields
    never re-checks — or reopens — an existing image.
    """
    if isinstance(file, FieldFile) and file._committed:
        return

    if file.size > MAX_PRODUCT_IMAGE_BYTES:
        size_mb = math.ceil(file.size * 10 / MEGABYTE) / 10
        raise ValidationError(
            f"This image is {size_mb} MB. Please upload an image of "
            f"{MAX_PRODUCT_IMAGE_BYTES // MEGABYTE} MB or smaller.",
            code="file_too_large",
        )

    try:
        file.seek(0)
        with Image.open(file) as image:
            if image.format not in ALLOWED_FORMATS:
                raise ValidationError(FORMAT_MESSAGE, code="invalid_format")
            width, height = image.size
            if min(width, height) < MIN_SHORTEST_SIDE:
                raise ValidationError(
                    f"This image is {width} × {height} pixels. Please upload an "
                    f"image at least {MIN_SHORTEST_SIDE} pixels on its "
                    "shortest side.",
                    code="image_too_small",
                )
            if max(width, height) > MAX_SIDE:
                raise ValidationError(
                    f"This image is {width} × {height} pixels. Please upload an "
                    f"image no more than {MAX_SIDE} pixels on either side.",
                    code="image_too_large",
                )
            image.load()
    except Image.DecompressionBombError as error:
        raise ValidationError(
            f"This image is far too large to process. Please upload an image "
            f"no more than {MAX_SIDE} pixels on either side.",
            code="image_too_large",
        ) from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise ValidationError(UNUSABLE_MESSAGE, code="invalid_image") from error
    finally:
        file.seek(0)


def normalize_product_image(file: File, slug: str) -> ContentFile:
    """Return a web-ready WebP copy of a validated upload.

    Applies the EXIF orientation, shrinks the image so its longest side is
    at most 1200 px (never enlarging), and re-encodes it as WebP, which also
    drops its metadata. The new name is the product slug plus a short
    random suffix, so a replaced image always gets a fresh URL.
    """
    file.seek(0)
    with Image.open(file) as original:
        image = ImageOps.exif_transpose(original)
    image.thumbnail((NORMALIZED_LONGEST_SIDE, NORMALIZED_LONGEST_SIDE))
    image = image.convert("RGBA" if image.has_transparency_data else "RGB")
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=85)
    return ContentFile(buffer.getvalue(), name=f"{slug}-{secrets.token_hex(3)}.webp")


class ProductImageField(models.ImageField):
    """An ``ImageField`` whose only rules are ``validate_product_image``.

    Django's stock ``ImageField`` adds a file-extension validator, and its
    form field decodes the upload before model validators run. Both are
    dropped here so the format is judged by its content and the size
    limit is checked before any decoding.
    """

    default_validators = []

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": forms.FileField, **kwargs})
