from django.db import migrations


STYLE_VALUES = [str(value) for value in range(1, 13)]


def add_bumbu_style_option(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    ProductOption = apps.get_model('store', 'ProductOption')

    product = Product.objects.filter(slug='item42').first()
    if product is None:
        return

    ProductOption.objects.get_or_create(
        product=product,
        name='Style #',
        defaults={
            'values': STYLE_VALUES,
            'is_required': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_alter_product_category'),
    ]

    operations = [
        migrations.RunPython(add_bumbu_style_option, migrations.RunPython.noop),
    ]
