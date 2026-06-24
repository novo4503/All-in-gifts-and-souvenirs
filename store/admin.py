from django.contrib import admin
from django.utils.html import format_html
from .models import SiteImage, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "image_preview", "show_on_home")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image uploaded"

    image_preview.short_description = "Image Preview"


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = ("name", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image uploaded"

    image_preview.short_description = "Image Preview"

