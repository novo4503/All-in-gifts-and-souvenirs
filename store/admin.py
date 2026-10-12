from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SiteImage, Product, ProductImage, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "image_preview", "show_on_home")
    readonly_fields = ("image_preview",)
    inlines = [ProductImageInline]

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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "image_preview")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: contain;" />',
                obj.image.url,
            )
        return "No image uploaded"

    image_preview.short_description = "Image Preview"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "angle_name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product', 'product_reference_id', 'product_name', 'product_image',
        'unit_price', 'quantity', 'selected_options',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'phone', 'total', 'notification_status', 'created_at',
    )
    list_filter = ('notification_status', 'created_at')
    search_fields = ('customer_name', 'phone', 'delivery_address')
    readonly_fields = ('subtotal', 'discount', 'delivery_cost', 'total', 'created_at', 'notification_error')
    inlines = [OrderItemInline]