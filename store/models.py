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

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('women', 'Women'),
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