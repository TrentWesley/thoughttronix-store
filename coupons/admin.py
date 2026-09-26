from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "percent_off", "expires_on", "retired_at", "created_at")
    search_fields = ("code",)
    filter_horizontal = ("products",)
    readonly_fields = ("retired_at", "created_at")

    def get_readonly_fields(self, request, obj=None):
        """Terms are fixed once created, here as in the back office."""
        if obj is None:
            return self.readonly_fields
        return ("code", "percent_off", "products", *self.readonly_fields)
