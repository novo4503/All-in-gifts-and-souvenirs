# store/admin.py
from django.contrib import admin
from django.db import transaction
import nested_admin
from django.utils.html import format_html
from .models import (
    Category,
    SiteImage,
    Product,
    ProductImage,
    Order,
    OrderItem,
    ProductOption,
    ProductOptionValue,
)


class ProductCategoryFilter(admin.SimpleListFilter):
    title = 'category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        choices = dict(Product.CATEGORY_CHOICES)
        choices.update(
            Category.objects.order_by('name').values_list('slug', 'name')
        )
        return sorted(choices.items(), key=lambda choice: choice[1].casefold())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 3


class ProductOptionValueInline(nested_admin.NestedTabularInline):
    model = ProductOptionValue
    extra = 1
    fields = ('position', 'value')
    sortable_field_name = 'position'


class ProductOptionInline(nested_admin.NestedStackedInline):
    model = ProductOption
    extra = 0
    fields = ('position', 'name', 'is_required')
    sortable_field_name = 'position'
    inlines = [ProductOptionValueInline]


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "price", "category", "image_preview", "show_on_home")
    list_filter = (ProductCategoryFilter,)
    readonly_fields = ("image_preview",)
    inlines = [ProductImageInline, ProductOptionInline]
    actions = ['add_common_sizes']

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)
        if db_field.name == 'category':
            choices = dict(formfield.choices)
            choices.update(
                Category.objects.order_by('name').values_list('slug', 'name')
            )
            formfield.choices = [('', '---------')] + sorted(
                choices.items(),
                key=lambda choice: choice[1].casefold(),
            )
        return formfield

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image uploaded"

    image_preview.short_description = "Image Preview"

    @admin.action(
        description='Add common sizes (S, M, L, XL, XXL) to selected products'
    )
    def add_common_sizes(self, request, queryset):
        common_sizes = ('S', 'M', 'L', 'XL', 'XXL')
        updated_products = 0

        with transaction.atomic():
            for product in queryset.iterator():
                option = product.options.filter(name__iexact='Size').first()
                if option is None:
                    last_option = product.options.order_by('position', 'pk').last()
                    option = ProductOption.objects.create(
                        product=product,
                        name='Size',
                        is_required=True,
                        position=last_option.position + 1 if last_option else 0,
                    )
                    option_changed = True
                else:
                    option_changed = False

                existing_values = list(option.values.order_by('position', 'pk'))
                existing_value_names = {
                    value.value.casefold() for value in existing_values
                }
                next_position = (
                    existing_values[-1].position + 1 if existing_values else 0
                )
                new_values = []
                for size in common_sizes:
                    if size.casefold() not in existing_value_names:
                        new_values.append(ProductOptionValue(
                            option=option,
                            value=size,
                            position=next_position,
                        ))
                        existing_value_names.add(size.casefold())
                        next_position += 1

                if new_values:
                    ProductOptionValue.objects.bulk_create(new_values)
                    option_changed = True
                if option_changed:
                    updated_products += 1

        self.message_user(
            request,
            f'Common sizes added or confirmed for {updated_products} selected product(s).',
        )


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    inlines = [ProductOptionValueInline]
    list_display = ("product", "name", "position", "is_required")
    search_fields = ("product__name", "name")
    ordering = ('product', 'position', 'pk')


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
    fields = ("name", "slug", "description", "image", "parent")
    readonly_fields = ("image_preview",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['slug'].required = False
        return form

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
    readonly_fields = ('subtotal', 'discount', 'delivery_cost', 'gct_amount', 'total', 'created_at', 'notification_error')
    inlines = [OrderItemInline]