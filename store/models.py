# store/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class SiteImage(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='site_images/')

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        parent = self.parent
        seen_parent_ids = set()
        while parent:
            if self.pk and parent.pk == self.pk:
                raise ValidationError({
                    'parent': 'A category cannot be its own parent or a descendant of itself.'
                })
            if parent.pk in seen_parent_ids:
                raise ValidationError({
                    'parent': 'The selected parent has an invalid category hierarchy.'
                })
            seen_parent_ids.add(parent.pk)
            parent = parent.parent

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:50].strip('-')
            if not base_slug:
                raise ValidationError({'slug': 'Enter a name that can form a valid slug.'})

            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                suffix = f'-{counter}'
                slug = f'{base_slug[:50 - len(suffix)]}{suffix}'
            self.slug = slug
        super().save(*args, **kwargs)


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('women', 'Women'),
        ('shoes', 'Shoes'),
        ('bathsuit', 'Bathsuit'),
        ('men', 'Men'),
        ('kids', 'Kids'),
        ('jewelry', 'Jewelry'),
        ('bottle', 'Bottle'),
        ('hat', 'Hat'),
        ('shorts', 'Shorts'),
        ('dress-shirt', 'Dress-Shirt'),
        ('pants', 'Pants'),
        ('tshirt', 'TShirt'),
        ('kids-t-shirts', 'Kids T-Shirts'),
        ('jamaica-outfits', 'Jamaica Outfits'),
        ('kids-dresses', 'Kids Dresses'),
        ('baby-onesies', 'Baby Onesies'),
        ('silver-jewelry', 'Silver Jewelry'),
        ('necklaces', 'Necklaces'),
        ('bob-marley-bracelets', 'Bob Marley Bracelets'),
        ('earrings', 'Earrings'),
        ('baseball', 'Baseball'),
        ('fedora', 'Fedora'),
        ('visor', 'Visor'),
        ('rasta-tams', 'Rasta Tams'),
        ('cigar', 'Cigar'),
        ('liquor', 'Liquor'),
        ('white-rum', 'White Rum'),
        ('dark-rum', 'Dark Rum'),
        ('spiced-rum', 'Spiced Rum'),
        ('gold-rum', 'Gold Rum'),
        ('rum-cream', 'Rum Cream'),
        ('coffee', 'Coffee'),
        ('blue-mountain-coffee', 'Blue Mountain Coffee'),
        ('jablum-instant', 'Jablum Instant'),
        ('cafe-coffee-roaster', 'Cafe Coffee Roaster'),
        ('mocha-island', 'Mocha Island'),
        ('classic-decaf', 'Classic Decaf'),
        ('cafe-expresso-blend-coffee', 'Cafe Expresso Blend Coffee'),
        ('cake', 'Cake'),
        ('original-jamaican-rum-cake', 'Original Jamaican Rum Cake'),
        ('black-rum-cake', 'Black Rum Cake'),
        ('white-rum-cake', 'White Rum Cake'),
        ('coconut-rum-cake', 'Coconut Rum Cake'),
        ('pineapple-rum-cake', 'Pineapple Rum Cake'),
        ('banana-rum-cake', 'Banana Rum Cake'),
        ('fruit-rum-cake', 'Fruit Rum Cake'),
        ('chocolate-rum-cake', 'Chocolate Rum Cake'),
        ('ginger-rum-cake', 'Ginger Rum Cake'),
        ('mini-rum-cakes-gift-boxes', 'Mini Rum Cakes & Gift Boxes'),
        ('dress', 'Dress'),
        ('bluse', 'Bluse'),
        ('womenshirt', 'Womenshirt'),
        ('hoodies', 'Hoodies'),
        ('posters', 'Posters'),
        ('Accessories', 'Accessories'),
        ('mugs', 'Mugs'),
        ('thermal-bottles', 'Thermal Bottles'),
        ('sports-bottles', 'Sports Bottles'),
        ('sunscreen', 'Sunscreen'),
        ('souvenirs', 'Souvenirs'),
        ('bongs', 'Bongs'),
        ('vape', 'Vape'),
        ('bags', 'Bags'),
        ('purse', 'Purse'),
        ('tote-bags', 'Tote Bags'),
        ('beach-bags', 'Beach Bags'),
        ('cover-ups', 'Cover-ups'),
        ('all-mens-clothing', 'All Mens Clothing'),
        ('all-womens-clothing', 'All Womens Clothing'),
        ('all-children', 'All Children'),
        ('all-jewelry', 'All Jewelry'),
        ('all-bob-marley', 'All Bob Marley'),
        ('all-essentials', 'All Essentials'),
        ('all-bags', 'All Bags'),
        ('all-caps-and-hats', 'All Caps & Hats'),
        ('all-bottles', 'All Bottles'),
        ('all-childrens-clothing', 'All Childrens Clothing'),
        ('all-cigars', 'All Cigars'),
        ('jamaica-souvenir-figurines', 'Jamaica Souvenir Figurines'),
        ('kids-souvenir-toys', "Kids' Souvenir Toys"),
        ('wooden-toys', 'Wooden Toys'),
        ('miniature-cars-vehicles', 'Miniature Cars & Vehicles'),
        ('accessories', 'Accessories'),
        ('bag', 'Bag'),
        ('banana-drops', 'Banana Drops'),
        ('beach-towels', 'Beach Towels'),
        ('bob-marley-towels', 'Bob Marley Towels'),
        ('bottles', 'Bottles'),
        ('chicken-seasoning', 'Chicken Seasoning'),
        ('cigars', 'Cigars'),
        ('cinnamon-powder', 'Cinnamon Powder'),
        ('coconut-drop', 'Coconut Drop'),
        ('cohiba', 'Cohiba'),
        ('dress-shirts', 'Dress Shirts'),
        ('essentials', 'Essentials'),
        ('fish-seasoning', 'Fish Seasoning'),
        ('gizzada', 'Gizzada'),
        ('h-upmann', 'H. Upmann'),
        ('hats', 'Hats'),
        ('jamaican-curry-powder', 'Jamaican Curry Powder'),
        ('jamaican-jerk-seasoning', 'Jamaican Jerk Seasoning'),
        ('jamaican-themed-toys', 'Jamaican Themed Toys'),
        ('montecristo', 'Montecristo'),
        ('partagas', 'Partagas'),
        ('plantain-chips', 'Plantain Chips'),
        ('romeo-y-julieta', 'Romeo y Julieta'),
        ('spices', 'Spices'),
        ('striped-towels', 'Striped Towels'),
        ('t-shirt', 'T-Shirt'),
        ('towels', 'Towels'),
        ('toys', 'Toys'),
        ('water-bottles', 'Water Bottles'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='women')
    show_on_home = models.BooleanField(default=False)

    def clean_fields(self, exclude=None):
        excluded_fields = set(exclude or ())
        if (
            'category' not in excluded_fields
            and self.category
            and Category.objects.filter(slug=self.category).exists()
        ):
            # Database categories are added dynamically in ProductAdmin.
            category_field = self._meta.get_field('category')
            try:
                category_field.run_validators(
                    category_field.to_python(self.category)
                )
            except ValidationError as error:
                raise ValidationError({'category': error.error_list})
            excluded_fields.add('category')
            exclude = excluded_fields
        return super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=80)
    is_required = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'name')
        ordering = ('position', 'pk')

    def __str__(self):
        return f'{self.product.name} - {self.name}'

    @property
    def value_list(self):
        return [option_value.value for option_value in self.values.all()]


class ProductOptionValue(models.Model):
    option = models.ForeignKey(
        ProductOption,
        on_delete=models.CASCADE,
        related_name='values',
    )
    value = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self):
        return self.value


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="gallery_images"
    )
    image = models.ImageField(upload_to="product_gallery/")
    angle_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.product.name} image"


class Order(models.Model):
    NOTIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    customer_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    delivery_address = models.CharField(max_length=255)
    room = models.CharField(max_length=80, blank=True)
    delivery_time = models.CharField(max_length=40)
    cash_note = models.CharField(max_length=40)
    delivery_notes = models.TextField(blank=True)
    promo_code = models.CharField(max_length=40, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gct_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_type = models.CharField(max_length=30, default='island')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notification_status = models.CharField(
        max_length=10,
        choices=NOTIFICATION_STATUS_CHOICES,
        default='pending',
    )
    notification_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} - {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
    )
    product_reference_id = models.PositiveIntegerField()
    product_name = models.CharField(max_length=100)
    product_image = models.CharField(max_length=500, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    selected_options = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'{self.product_name} x {self.quantity} (Order #{self.order_id})'