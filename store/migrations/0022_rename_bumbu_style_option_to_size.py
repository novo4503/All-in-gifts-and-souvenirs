from django.db import migrations


def rename_bumbu_option(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    ProductOption = apps.get_model('store', 'ProductOption')

    product = Product.objects.filter(slug='item42').first()
    if product is None:
        return

    ProductOption.objects.filter(
        product=product,
        name='Style #',
    ).exclude(
        product__options__name='Size',
    ).update(name='Size')


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0021_bumbu_style_option'),
    ]

    operations = [
        migrations.RunPython(rename_bumbu_option, migrations.RunPython.noop),
    ]
