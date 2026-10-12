from django.db import migrations, models


def assign_category_images(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    database = schema_editor.connection.alias
    image_by_slug = {
        'coffee': 'categories/coffeeimage.jpeg',
        'cake': 'categories/cake101.jpeg',
    }

    for slug, image_path in image_by_slug.items():
        Category.objects.using(database).filter(slug=slug).filter(
            models.Q(image='') | models.Q(image__isnull=True)
        ).update(image=image_path)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0017_category_parent_alter_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='categories/'),
        ),
        migrations.RunPython(assign_category_images, migrations.RunPython.noop),
    ]