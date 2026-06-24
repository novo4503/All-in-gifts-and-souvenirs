from django.db import models
from django.utils.text import slugify


class SiteImage(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='site_images/')

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('women', 'Women'),
        ('men', 'Men'),
        ('jewelry', 'Jewelry'),
        ('bottle','Bottle'),
        ('bag','Bag'),
        ('hat','Hat')
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
        max_length=20,
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