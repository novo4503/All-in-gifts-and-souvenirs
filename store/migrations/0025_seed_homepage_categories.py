from django.db import migrations


ROOT_CATEGORIES = [
    ('all-mens-clothing', 'Men', 'mens'),
    ('all-womens-clothing', 'Women', 'women'),
    ('all-children', 'Children', None),
    ('all-jewelry', 'Jewelry', 'nice_jew'),
    ('all-bob-marley', 'Bob Marley', 'bob_main'),
    ('all-essentials', 'Essentials', 'essensial'),
    ('all-bags', 'Bags', 'bago1'),
    ('all-caps-and-hats', 'Caps & Hats', 'AllAX'),
    ('bottles', 'Bottles', 'AllA1'),
    ('toys', 'Toys', 'Toys_Bottom'),
    ('sunscreen', 'Sunscreen', 'SunscreenOG'),
    ('jamaican-treats', 'Jamaican Treats', 'Jamaican_Treats'),
    ('all-cigars', 'Cigars', 'cigar_bottom'),
    ('towels', 'Towels', 'Towels_Bottom'),
    ('spices', 'Spices', 'Spicies_Bottom'),
    ('liquor', 'Liquor', 'LiquorOG'),
]

CHILD_CATEGORIES = {
    'all-mens-clothing': ('dress-shirts', 'shorts', 'pants', 't-shirt'),
    'all-womens-clothing': ('dress', 'bluse', 'womenshirt', 'cover-ups'),
    'all-children': (
        'kids-t-shirts', 'jamaica-outfits', 'kids-dresses', 'baby-onesies',
    ),
    'all-jewelry': (
        'silver-jewelry', 'necklaces', 'bob-marley-bracelets', 'earrings',
    ),
    'all-bob-marley': ('hoodies', 'posters', 'accessories'),
    'all-essentials': ('sunscreen', 'souvenirs', 'bongs', 'vape'),
    'all-bags': ('bags', 'beach-bags', 'purse', 'tote-bags'),
    'all-caps-and-hats': ('baseball', 'fedora', 'visor', 'rasta-tams'),
    'bottles': ('water-bottles', 'thermal-bottles', 'mugs', 'sports-bottles'),
    'toys': (
        'jamaica-souvenir-figurines', 'kids-souvenir-toys',
        'jamaican-themed-toys', 'miniature-cars-vehicles', 'wooden-toys',
    ),
    'jamaican-treats': (
        'banana-drops', 'plantain-chips', 'coconut-drop', 'gizzada',
    ),
    'all-cigars': (
        'cohiba', 'montecristo', 'romeo-y-julieta', 'partagas', 'h-upmann',
    ),
    'towels': ('striped-towels', 'bob-marley-towels', 'beach-towels'),
    'spices': (
        'jamaican-jerk-seasoning', 'jamaican-curry-powder',
        'fish-seasoning', 'chicken-seasoning', 'cinnamon-powder',
    ),
}


def preserve_homepage_categories(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Product = apps.get_model('store', 'Product')
    SiteImage = apps.get_model('store', 'SiteImage')
    database = schema_editor.connection.alias
    labels = dict(
        Product._meta.get_field('category').choices
    )
    images = dict(
        SiteImage.objects.using(database).values_list('name', 'image')
    )
    root_ids = {}

    for slug, name, image_name in ROOT_CATEGORIES:
        category, created = Category.objects.using(database).get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'image': images.get(image_name, '') if image_name else '',
                'parent_id': None,
            },
        )
        if not created and image_name and not category.image and images.get(image_name):
            Category.objects.using(database).filter(pk=category.pk).update(
                image=images[image_name]
            )
        root_ids[slug] = category.pk

    for parent_slug, child_slugs in CHILD_CATEGORIES.items():
        for child_slug in child_slugs:
            if child_slug in root_ids:
                continue
            Category.objects.using(database).get_or_create(
                slug=child_slug,
                defaults={
                    'name': labels.get(child_slug, child_slug.replace('-', ' ').title()),
                    'image': '',
                    'parent_id': root_ids[parent_slug],
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_alter_productoption_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            preserve_homepage_categories,
            migrations.RunPython.noop,
        ),
    ]
