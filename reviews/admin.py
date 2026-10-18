from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at", "edited_at")
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username", "comment")
    date_hierarchy = "created_at"
    list_select_related = ("product", "user")
    readonly_fields = ("updated_at", "edited_at", "edited_by_staff_at")
