from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.templatetags.static import static
from django.urls import reverse

from .images import (
    ProductImageField,
    normalize_product_image,
    validate_product_image,
)

# Categories with a dedicated placeholder illustration; anything else
# falls back to default.svg. A product without an uploaded image shows its
# category's placeholder, a static file chosen here.
PLACEHOLDER_CATEGORIES = {
    "home-assistants",
    "neural-implants",
    "neural-wearables",
    "accessories",
    "defense",
    "legacy-products",
}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category", kwargs={"slug": self.slug})

    @property
    def placeholder_image(self):
        """Static path of the placeholder image shown for this category's products."""
        if self.slug in PLACEHOLDER_CATEGORIES:
            return f"images/placeholders/{self.slug}.svg"
        return "images/placeholders/default.svg"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.filter(is_available=True)

    def search(self, text):
        """Simple icontains search over name and description."""
        return self.filter(
            models.Q(name__icontains=text) | models.Q(description__icontains=text)
        )


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    image = ProductImageField(
        upload_to="products/",
        max_length=255,
        blank=True,
        validators=[validate_product_image],
        help_text=(
            "Optional. A JPEG, PNG, or WebP image, up to 5 MB and at least "
            "600 pixels on its shortest side."
        ),
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Normalize a newly uploaded image; remove a replaced or cleared one.

        Only a fresh upload — a file not yet committed to storage — is
        normalized, so editing price, tags, or any other field never
        reprocesses an existing image. The old file is deleted only after
        the transaction commits, so a failed save never loses it.
        """
        if self.image and not self.image._committed:
            self.image = normalize_product_image(self.image, self.slug)

        update_fields = kwargs.get("update_fields")
        stored_name = ""
        if not self._state.adding and (
            update_fields is None or "image" in update_fields
        ):
            stored_name = (
                type(self)
                ._default_manager.filter(pk=self.pk)
                .values_list("image", flat=True)
                .first()
                or ""
            )

        super().save(*args, **kwargs)

        if stored_name and stored_name != self.image.name:
            delete_image_file_on_commit(self.image.storage, stored_name)

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})

    @property
    def image_url(self):
        """The uploaded image's URL, or the category placeholder's when there is none."""
        if self.image:
            return self.image.url
        return static(self.category.placeholder_image)


def delete_image_file_on_commit(storage, name):
    """Delete a stored image once the surrounding transaction commits."""
    transaction.on_commit(lambda: storage.delete(name))


@receiver(post_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    """Remove a deleted product's image file.

    A signal rather than a ``delete()`` override, because bulk queryset
    deletes (such as the seed command's) skip ``Model.delete()`` but still
    send ``post_delete``.
    """
    if instance.image:
        delete_image_file_on_commit(instance.image.storage, instance.image.name)
