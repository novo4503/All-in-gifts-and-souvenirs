from django.db import migrations


PLACEHOLDER_VALUES = [str(value) for value in range(1, 13)]


def remove_placeholder_bumbu_size(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    ProductOption = apps.get_model('store', 'ProductOption')

    product = Product.objects.filter(slug='item42').first()
    if product is None:
        return

    ProductOption.objects.filter(
        product=product,
        name='Size',
        values=PLACEHOLDER_VALUES,
        is_required=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_rename_bumbu_style_option_to_size'),
    ]

    operations = [
        migrations.RunPython(
            remove_placeholder_bumbu_size,
            migrations.RunPython.noop,
        ),
    ]
