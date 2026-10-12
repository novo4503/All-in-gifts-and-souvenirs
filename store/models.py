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
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


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
    ]

    name = models.CharField(max_length=100)

    slug = models.SlugField(
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='women'
    )

    show_on_home = models.BooleanField(default=False)

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