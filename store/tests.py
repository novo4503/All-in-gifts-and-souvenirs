from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, ProductOption, ProductOptionValue, SiteImage


def create_product_option(product, name, values, is_required=True, position=0):
    option = ProductOption.objects.create(
        product=product,
        name=name,
        is_required=is_required,
        position=position,
    )
    ProductOptionValue.objects.bulk_create([
        ProductOptionValue(option=option, value=value, position=value_position)
        for value_position, value in enumerate(values)
    ])
    return option


class ProductOptionTests(TestCase):
    def test_product_with_options_requires_selection(self):
        product = Product.objects.create(
            name='Test Shirt',
            slug='test-shirt',
            description='Test',
            price=Decimal('30.00'),
            category='men',
        )
        create_product_option(product, 'Size', ['S', 'M', 'L'])

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'Please choose a valid Size.',
            [str(message) for message in get_messages(response.wsgi_request)],
        )
        self.assertFalse(self.client.session.get('cart'))

    def test_product_with_valid_option_is_saved_in_cart(self):
        product = Product.objects.create(
            name='Test Shirt',
            slug='test-shirt-2',
            description='Test',
            price=Decimal('30.00'),
            category='men',
        )
        option = create_product_option(product, 'Size', ['S', 'M', 'L'])
        detail = self.client.get(reverse('Product_Detail', args=[product.slug]))
        self.assertContains(detail, f'name="option_{option.pk}"')
        self.assertContains(detail, '<option value="M">M</option>')

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1', f'option_{option.pk}': 'M'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'], [{
            'product_id': product.pk,
            'quantity': 1,
            'selected_options': {'Size': 'M'},
        }])

    def test_cart_controls_change_only_the_selected_variation(self):
        product = Product.objects.create(
            name='Variant Shirt',
            slug='variant-shirt',
            description='Test',
            price=Decimal('30.00'),
            category='men',
        )
        option = create_product_option(product, 'Size', ['S', 'M', 'L'])
        colour = create_product_option(product, 'Colour', ['Red', 'Blue'])
        add_url = reverse('add_to_cart', args=[product.pk])
        self.client.post(add_url, {
            'quantity': '1',
            f'option_{option.pk}': 'M',
            f'option_{colour.pk}': 'Red',
        })
        self.client.post(add_url, {
            'quantity': '1',
            f'option_{option.pk}': 'M',
            f'option_{colour.pk}': 'Red',
        })
        self.client.post(add_url, {
            'quantity': '1',
            f'option_{option.pk}': 'L',
            f'option_{colour.pk}': 'Blue',
        })

        cart = self.client.session['cart']
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart[0]['quantity'], 2)
        self.client.post(reverse('change_cart', args=[product.pk]), {
            'action': 'increase',
            'line_index': '1',
        })
        cart = self.client.session['cart']
        self.assertEqual(cart[0]['quantity'], 2)
        self.assertEqual(cart[1]['quantity'], 2)

        checkout = self.client.get(reverse('checkout'))
        self.assertContains(checkout, 'Size: <strong>M</strong>')
        self.assertContains(checkout, 'Size: <strong>L</strong>')
        self.assertContains(checkout, 'Colour: <strong>Red</strong>')
        self.assertContains(checkout, 'Colour: <strong>Blue</strong>')
        self.assertContains(checkout, 'name="line_index" value="0"')
        self.assertContains(checkout, 'name="line_index" value="1"')

        self.client.post(reverse('change_cart', args=[product.pk]), {
            'action': 'remove',
            'line_index': '0',
        })
        self.assertEqual(self.client.session['cart'], [{
            'product_id': product.pk,
            'quantity': 2,
            'selected_options': {'Size': 'L', 'Colour': 'Blue'},
        }])

    def test_optional_product_option_can_be_left_unselected(self):
        product = Product.objects.create(
            name='Optional Flavour Cake',
            slug='optional-flavour-cake',
            description='Test',
            price=Decimal('24.00'),
            category='cake',
        )
        option = create_product_option(
            product, 'Flavour', ['Vanilla', 'Chocolate'], is_required=False
        )

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1', f'option_{option.pk}': ''},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][0]['selected_options'], {})

    def test_products_without_options_render_and_add_without_selection(self):
        product = Product.objects.create(
            name='Plain Toy',
            slug='plain-toy',
            description='No options',
            price=Decimal('12.00'),
            category='wooden-toys',
        )

        detail = self.client.get(reverse('Product_Detail', args=[product.slug]))
        self.assertContains(detail, reverse('add_to_cart', args=[product.pk]))
        self.assertNotContains(detail, 'name="option_')

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '2'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'], [{
            'product_id': product.pk,
            'quantity': 2,
            'selected_options': {},
        }])

    def test_required_option_without_values_is_hidden_and_does_not_block_cart(self):
        product = Product.objects.create(
            name='Unconfigured Product',
            slug='unconfigured-product',
            description='No configured values',
            price=Decimal('12.00'),
            category='wooden-toys',
        )
        option = ProductOption.objects.create(
            product=product,
            name='Size',
            is_required=True,
        )

        detail = self.client.get(reverse('Product_Detail', args=[product.slug]))
        self.assertNotContains(detail, f'name="option_{option.pk}"')

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['cart'][0]['selected_options'], {})

    def test_invalid_option_value_is_rejected(self):
        product = Product.objects.create(
            name='Flavour Cake',
            slug='flavour-cake',
            description='Test',
            price=Decimal('20.00'),
            category='cake',
        )
        option = create_product_option(product, 'Flavour', ['Vanilla', 'Chocolate'])

        response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1', f'option_{option.pk}': 'Strawberry'},
        )
        self.assertIn(
            'Invalid selection for Flavour.',
            [str(message) for message in get_messages(response.wsgi_request)],
        )
        self.assertFalse(self.client.session.get('cart'))

    def test_option_field_from_another_product_is_rejected(self):
        size_product = Product.objects.create(
            name='Size Product',
            slug='size-product',
            description='Test',
            price=Decimal('30.00'),
            category='men',
        )
        size = create_product_option(size_product, 'Size', ['S', 'M', 'L'])
        other_product = Product.objects.create(
            name='Other Product',
            slug='other-product',
            description='Test',
            price=Decimal('20.00'),
            category='cake',
        )
        flavour = create_product_option(
            other_product, 'Flavour', ['Vanilla', 'Chocolate']
        )

        response = self.client.post(
            reverse('add_to_cart', args=[size_product.pk]),
            {
                'quantity': '1',
                f'option_{size.pk}': 'M',
                f'option_{flavour.pk}': 'Vanilla',
            },
        )

        self.assertIn(
            'One or more selected options are not valid for this product.',
            [str(message) for message in get_messages(response.wsgi_request)],
        )
        self.assertFalse(self.client.session.get('cart'))


class ProductOptionAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username='options-admin',
            email='options-admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin_user)
        self.size_product = Product.objects.create(
            name='Admin Size Product',
            slug='admin-size-product',
            description='Test',
            price=Decimal('30.00'),
            category='men',
        )
        self.flavour_product = Product.objects.create(
            name='Admin Flavour Product',
            slug='admin-flavour-product',
            description='Test',
            price=Decimal('20.00'),
            category='cake',
        )

    def test_admin_manages_product_options_and_customers_use_saved_values(self):
        add_url = reverse('admin:store_productoption_add')
        size_response = self.client.post(add_url, {
            'product': str(self.size_product.pk),
            'name': 'Size',
            'position': '0',
            'is_required': 'on',
            'values-TOTAL_FORMS': '5',
            'values-INITIAL_FORMS': '0',
            'values-MIN_NUM_FORMS': '0',
            'values-MAX_NUM_FORMS': '1000',
            **{
                f'values-{index}-{field}': value
                for index, option_value in enumerate(
                    ['XXL', 'XL', 'L', 'M', 'S']
                )
                for field, value in (
                    ('position', str(index)),
                    ('value', option_value),
                )
            },
            '_save': 'Save',
        })
        self.assertEqual(size_response.status_code, 302)
        size = ProductOption.objects.get(product=self.size_product, name='Size')

        flavour_response = self.client.post(add_url, {
            'product': str(self.flavour_product.pk),
            'name': 'Flavour',
            'position': '0',
            'is_required': 'on',
            'values-TOTAL_FORMS': '3',
            'values-INITIAL_FORMS': '0',
            'values-MIN_NUM_FORMS': '0',
            'values-MAX_NUM_FORMS': '1000',
            **{
                f'values-{index}-{field}': value
                for index, option_value in enumerate(
                    ['Vanilla', 'Chocolate', 'Strawberry']
                )
                for field, value in (
                    ('position', str(index)),
                    ('value', option_value),
                )
            },
            '_save': 'Save',
        })
        self.assertEqual(flavour_response.status_code, 302)
        flavour = ProductOption.objects.get(
            product=self.flavour_product,
            name='Flavour',
        )

        self.assertEqual(size.value_list, ['XXL', 'XL', 'L', 'M', 'S'])
        self.assertEqual(flavour.value_list, ['Vanilla', 'Chocolate', 'Strawberry'])

        size_detail = self.client.get(
            reverse('Product_Detail', args=[self.size_product.slug])
        )
        flavour_detail = self.client.get(
            reverse('Product_Detail', args=[self.flavour_product.slug])
        )
        self.assertContains(size_detail, 'Size')
        self.assertContains(size_detail, '<option value="XXL">XXL</option>')
        self.assertNotContains(size_detail, 'Vanilla')
        self.assertContains(flavour_detail, 'Flavour')
        self.assertContains(
            flavour_detail,
            '<option value="Strawberry">Strawberry</option>',
        )
        self.assertNotContains(flavour_detail, '<option value="S">S</option>')

        self.client.post(
            reverse('add_to_cart', args=[self.size_product.pk]),
            {'quantity': '2', f'option_{size.pk}': 'M'},
        )
        self.client.post(
            reverse('add_to_cart', args=[self.flavour_product.pk]),
            {'quantity': '1', f'option_{flavour.pk}': 'Chocolate'},
        )
        self.assertEqual(
            self.client.session['cart'],
            [
                {
                    'product_id': self.size_product.pk,
                    'quantity': 2,
                    'selected_options': {'Size': 'M'},
                },
                {
                    'product_id': self.flavour_product.pk,
                    'quantity': 1,
                    'selected_options': {'Flavour': 'Chocolate'},
                },
            ],
        )

        checkout = self.client.get(reverse('checkout'))
        self.assertContains(checkout, 'Size: <strong>M</strong>')
        self.assertContains(checkout, 'Flavour: <strong>Chocolate</strong>')

        self.client.post(
            reverse('change_cart', args=[self.size_product.pk]),
            {'action': 'increase', 'line_index': '0'},
        )
        self.assertEqual(
            self.client.session['cart'][0]['selected_options'],
            {'Size': 'M'},
        )

        delete_response = self.client.post(
            reverse('admin:store_productoption_delete', args=[flavour.pk]),
            {'post': 'yes'},
        )
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(ProductOption.objects.filter(pk=flavour.pk).exists())

    def test_product_admin_shows_nested_option_values(self):
        option = create_product_option(
            self.size_product,
            'Food',
            ['Spicy', 'Mild', 'Sweet'],
        )

        response = self.client.get(
            reverse('admin:store_product_change', args=[self.size_product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Spicy')
        self.assertContains(response, 'Mild')
        self.assertContains(response, 'Sweet')
        self.assertContains(response, f'options-0-values-0-value')
        self.assertTrue(ProductOption.objects.filter(pk=option.pk).exists())

    def test_admin_adds_common_sizes_only_to_selected_products(self):
        changelist_url = reverse('admin:store_product_changelist')
        response = self.client.post(changelist_url, {
            'action': 'add_common_sizes',
            '_selected_action': [str(self.size_product.pk)],
            'index': '0',
        })

        self.assertEqual(response.status_code, 302)
        size_option = ProductOption.objects.get(
            product=self.size_product,
            name='Size',
        )
        self.assertEqual(size_option.value_list, ['S', 'M', 'L', 'XL', 'XXL'])
        self.assertFalse(
            ProductOption.objects.filter(product=self.flavour_product).exists()
        )

        detail = self.client.get(
            reverse('Product_Detail', args=[self.size_product.slug])
        )
        self.assertContains(detail, 'Select Size')
        self.assertContains(detail, '<option value="XXL">XXL</option>')
        self.client.post(
            reverse('add_to_cart', args=[self.size_product.pk]),
            {'quantity': '1', f'option_{size_option.pk}': 'M'},
        )
        checkout = self.client.get(reverse('checkout'))
        self.assertContains(checkout, 'Admin Size Product</strong>, Size: <strong>M</strong>')

        self.client.post(changelist_url, {
            'action': 'add_common_sizes',
            '_selected_action': [str(self.size_product.pk)],
            'index': '0',
        })
        size_option.refresh_from_db()
        self.assertEqual(size_option.value_list, ['S', 'M', 'L', 'XL', 'XXL'])


class IslandDeliveryTaxTests(TestCase):
    def test_island_gct_is_applied_to_subtotal(self):
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test',
            price=Decimal('100.00'),
            category='men',
        )
        session = self.client.session
        session['cart'] = [{'product_id': product.pk, 'quantity': 1, 'selected_options': {}}]
        session.save()

        checkout = self.client.get(reverse('checkout'))
        self.assertContains(checkout, 'GCT (15% of products after discount)')
        self.assertContains(checkout, '$15.00')
        self.assertContains(checkout, '$115.00')

        response = self.client.post(reverse('submit_order'), {
            'customer_name': 'John Doe',
            'phone': '876-555-1234',
            'delivery_address': 'Example Hotel',
            'room': '12',
            'delivery_time': 'ASAP',
            'cash_note': 'Exact amount',
            'delivery_type': 'not-a-valid-delivery-type',
        })
        self.assertEqual(response.status_code, 200)
        order = product.order_items.first().order if product.order_items.exists() else None
        self.assertIsNotNone(order)
        self.assertEqual(order.gct_amount, Decimal('15.00'))
        self.assertEqual(order.total, Decimal('115.00'))

    def test_discount_reduces_gct_taxable_product_subtotal(self):
        product = Product.objects.create(
            name='Discounted Product',
            slug='discounted-product',
            description='Test',
            price=Decimal('100.00'),
            category='men',
        )
        session = self.client.session
        session['cart'] = [{
            'product_id': product.pk,
            'quantity': 1,
            'selected_options': {},
        }]
        session['promo_code'] = 'ISLAND10'
        session.save()

        checkout = self.client.get(reverse('checkout'))
        self.assertContains(checkout, '$13.50')
        self.assertContains(checkout, '$103.50')

        response = self.client.post(reverse('submit_order'), {
            'customer_name': 'John Doe',
            'phone': '876-555-1234',
            'delivery_address': 'Example Hotel',
            'room': '12',
            'delivery_time': 'ASAP',
            'cash_note': 'Exact amount',
        })
        self.assertEqual(response.status_code, 200)
        order = product.order_items.first().order
        self.assertEqual(order.subtotal, Decimal('100.00'))
        self.assertEqual(order.discount, Decimal('10.00'))
        self.assertEqual(order.gct_amount, Decimal('13.50'))
        self.assertEqual(order.total, Decimal('103.50'))
        self.assertEqual(
            response.context['whatsapp_order_data']['gct_amount'],
            '13.50',
        )
        self.assertEqual(
            response.context['whatsapp_order_data']['total'],
            '103.50',
        )

    def test_order_preserves_selected_options_in_whatsapp_payload(self):
        product = Product.objects.create(
            name='Order Shirt',
            slug='order-shirt',
            description='Test',
            price=Decimal('50.00'),
            category='men',
        )
        option = create_product_option(product, 'Colour', ['Red', 'Blue'])
        self.client.post(reverse('add_to_cart', args=[product.pk]), {
            'quantity': '2',
            f'option_{option.pk}': 'Blue',
        })

        response = self.client.post(reverse('submit_order'), {
            'customer_name': 'John Doe',
            'phone': '876-555-1234',
            'delivery_address': 'Example Hotel',
            'room': '12',
            'delivery_time': 'ASAP',
            'cash_note': 'Exact amount',
        })
        order = product.order_items.first().order
        order_item = order.items.get()
        self.assertEqual(order_item.selected_options, {'Colour': 'Blue'})
        self.assertEqual(
            response.context['whatsapp_order_data']['items'][0]['selected_options'],
            {'Colour': 'Blue'},
        )
        self.assertEqual(order.subtotal, Decimal('100.00'))
        self.assertEqual(order.gct_amount, Decimal('15.00'))
        self.assertEqual(order.total, Decimal('115.00'))
        self.assertContains(response, 'GCT: $')
        self.assertContains(response, 'selected_options')


class CategoryProductListingTests(TestCase):
    def test_product_admin_choices_include_existing_category_pages(self):
        choices = dict(Product._meta.get_field('category').choices)
        for slug in ('toys', 'spices', 'jamaican-themed-toys', 'wooden-toys'):
            self.assertIn(slug, choices)

    def test_parent_category_page_lists_products_assigned_to_its_child(self):
        toys, _ = Category.objects.get_or_create(
            name='Toys',
            slug='toys',
            defaults={'parent': None},
        )
        Category.objects.get_or_create(
            name='Wooden Toys',
            slug='wooden-toys',
            defaults={'parent': toys},
        )
        product = Product.objects.create(
            name='New Wooden Toy',
            slug='new-wooden-toy',
            description='A toy added in admin',
            price=Decimal('14.00'),
            category='wooden-toys',
        )
        option = create_product_option(product, 'Size', ['Small', 'Large'])

        response = self.client.get(reverse('category_products', args=['toys']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertNotContains(response, f'name="option_{option.pk}"')

        detail = self.client.get(reverse('Product_Detail', args=[product.slug]))
        self.assertContains(detail, f'<select name="option_{option.pk}"')

    def test_category_and_subcategory_pages_render_their_own_hierarchy(self):
        cakes = Category.objects.create(name='Cakes', slug='cakes')
        chocolate = Category.objects.create(
            name='Chocolate Cake',
            slug='chocolate-cake',
            parent=cakes,
        )
        vanilla = Category.objects.create(
            name='Vanilla Cake',
            slug='vanilla-cake',
            parent=cakes,
        )
        red_velvet = Category.objects.create(
            name='Red Velvet Cake',
            slug='red-velvet-cake',
            parent=chocolate,
        )
        unrelated = Category.objects.create(
            name='Unrelated Category',
            slug='unrelated-category',
        )
        direct_product = Product.objects.create(
            name='Classic Cake',
            slug='classic-cake',
            description='A cake assigned directly to Cakes',
            price=Decimal('20.00'),
            category=cakes.slug,
        )
        nested_product = Product.objects.create(
            name='Red Velvet Slice',
            slug='red-velvet-slice',
            description='A product in a nested subcategory',
            price=Decimal('7.50'),
            category=red_velvet.slug,
        )
        unrelated_product = Product.objects.create(
            name='Glass Bong',
            slug='glass-bong-unrelated',
            description='Not a cake',
            price=Decimal('25.00'),
            category=unrelated.slug,
        )

        home = self.client.get(reverse('home'))
        self.assertContains(
            home,
            f'href="{reverse("category_products", args=[cakes.slug])}"',
        )
        self.assertContains(
            home,
            f'href="{reverse("category_products", args=[chocolate.slug])}"',
        )

        cakes_page = self.client.get(reverse('category_products', args=[cakes.slug]))
        self.assertEqual(cakes_page.status_code, 200)
        self.assertTemplateUsed(cakes_page, 'store/category_products.html')
        self.assertContains(cakes_page, 'Cakes')
        self.assertContains(cakes_page, 'Chocolate Cake')
        self.assertContains(cakes_page, 'Vanilla Cake')
        self.assertContains(cakes_page, direct_product.name)
        self.assertContains(cakes_page, nested_product.name)
        self.assertNotContains(cakes_page, unrelated_product.name)

        chocolate_page = self.client.get(
            reverse('category_products', args=[chocolate.slug])
        )
        self.assertEqual(chocolate_page.status_code, 200)
        self.assertContains(chocolate_page, 'Red Velvet Cake')
        self.assertContains(chocolate_page, nested_product.name)
        self.assertNotContains(chocolate_page, direct_product.name)
        self.assertNotContains(chocolate_page, unrelated_product.name)

    def test_unknown_category_slug_returns_404_and_legacy_categories_still_work(self):
        self.assertEqual(
            self.client.get(reverse('category_products', args=['not-a-category'])).status_code,
            404,
        )
        legacy_page = self.client.get(reverse('category_products', args=['men']))
        self.assertEqual(legacy_page.status_code, 200)
        self.assertContains(legacy_page, '<h1>Men</h1>')

    def test_category_admin_creates_parent_and_children_with_unique_slugs(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username='hierarchy-admin',
            email='hierarchy-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin_user)
        add_url = reverse('admin:store_category_add')

        parent_response = self.client.post(add_url, {
            'name': 'Cakes',
            'slug': '',
            'description': 'Island cakes',
            'image': '',
            'parent': '',
        })
        self.assertEqual(parent_response.status_code, 302)
        cakes = Category.objects.get(name='Cakes')
        self.assertEqual(cakes.slug, 'cakes')

        for name in ('Chocolate Cake', 'Vanilla Cake'):
            response = self.client.post(add_url, {
                'name': name,
                'slug': '',
                'description': '',
                'image': '',
                'parent': str(cakes.pk),
            })
            self.assertEqual(response.status_code, 302)
            subcategory = Category.objects.get(name=name)
            self.assertEqual(subcategory.parent, cakes)
            self.assertEqual(
                self.client.get(
                    reverse('category_products', args=[subcategory.slug])
                ).status_code,
                200,
            )

        product_add_url = reverse('admin:store_product_add')
        product_form = self.client.get(product_add_url)
        self.assertContains(
            product_form,
            '<option value="chocolate-cake">Chocolate Cake</option>',
        )
        product_response = self.client.post(product_add_url, {
            'name': 'Admin Chocolate Cake',
            'slug': 'admin-chocolate-cake',
            'description': 'Added through Product Admin',
            'price': '12.00',
            'category': 'chocolate-cake',
            'show_on_home': '',
            'gallery_images-TOTAL_FORMS': '3',
            'gallery_images-INITIAL_FORMS': '0',
            'options-TOTAL_FORMS': '0',
            'options-INITIAL_FORMS': '0',
        })
        self.assertEqual(product_response.status_code, 302)
        admin_product = Product.objects.get(slug='admin-chocolate-cake')
        self.assertEqual(admin_product.category, 'chocolate-cake')
        self.assertContains(
            self.client.get(
                reverse('category_products', args=['chocolate-cake'])
            ),
            admin_product.name,
        )

        duplicate_name = Category.objects.create(name='Cakes')
        self.assertEqual(duplicate_name.slug, 'cakes-2')

    def test_spices_category_lists_products_assigned_in_admin(self):
        product = Product.objects.create(
            name='Jamaican Jerk Seasoning',
            slug='jamaican-jerk-seasoning-product',
            description='Spice blend',
            price=Decimal('8.00'),
            category='spices',
        )

        response = self.client.get(reverse('category_products', args=['spices']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)

    def test_homepage_shows_new_category_and_existing_product_still_adds_to_cart(self):
        category = Category.objects.create(
            name='New Gifts',
            slug='new-gifts',
            image='categories/new-gifts.png',
        )
        subcategory = Category.objects.create(
            name='New Gift Accessories',
            slug='new-gift-accessories',
            parent=category,
        )
        flags = Category.objects.create(
            name='Flags',
            slug='flags',
            image='categories/flags.png',
        )
        for image_name in ('cigar', 'shoeff'):
            SiteImage.objects.create(
                name=image_name,
                image=f'site_images/{image_name}.png',
            )
        product = Product.objects.create(
            name='New Gift Item',
            slug='new-gift-item',
            description='Added through product management',
            price=Decimal('15.00'),
            category=category.slug,
            image='products/new-gift-item.png',
            show_on_home=True,
        )
        child_product = Product.objects.create(
            name='New Gift Accessory',
            slug='new-gift-accessory',
            description='A product in a child category',
            price=Decimal('8.00'),
            category=subcategory.slug,
        )
        flag_product = Product.objects.create(
            name='Jamaican Flag',
            slug='jamaican-flag',
            description='A Jamaican flag',
            price=Decimal('5.00'),
            category=flags.slug,
        )

        homepage = self.client.get(reverse('home'))
        self.assertEqual(homepage.status_code, 200)
        self.assertContains(homepage, 'data-category="new-gifts"')
        self.assertNotContains(homepage, 'data-category="new-gift-accessories"')
        self.assertContains(
            homepage,
            f'href="{reverse("category_products", args=[subcategory.slug])}"',
        )
        self.assertContains(homepage, 'title="View More"')
        self.assertContains(homepage, 'data-category="flags"')
        self.assertContains(homepage, '/media/categories/new-gifts.png')
        self.assertContains(homepage, '/media/products/new-gift-item.png')
        for image_name in ('cigar', 'shoeff'):
            self.assertContains(
                homepage,
                f'/media/site_images/{image_name}.png',
            )
        self.assertContains(
            homepage,
            reverse('category_products', args=[category.slug]),
        )
        expected_homepage_categories = list(
            Category.objects.filter(parent__isnull=True).order_by('name')
        )
        self.assertEqual(
            list(homepage.context['homepage_categories']),
            expected_homepage_categories,
        )

        category_page = self.client.get(
            reverse('category_products', args=[category.slug])
        )
        self.assertContains(category_page, product.name)
        self.assertContains(category_page, child_product.name)

        flags_page = self.client.get(
            reverse('category_products', args=[flags.slug])
        )
        self.assertContains(flags_page, flag_product.name)

        add_response = self.client.post(
            reverse('add_to_cart', args=[product.pk]),
            {'quantity': '1'},
        )
        self.assertEqual(add_response.status_code, 302)
        self.assertEqual(self.client.session['cart'][0]['product_id'], product.pk)
        self.assertEqual(self.client.session['cart'][0]['quantity'], 1)

        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username='category-admin',
            email='category-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin_user)
        product_admin = self.client.get(reverse('admin:store_product_add'))
        self.assertEqual(product_admin.status_code, 200)
        self.assertContains(product_admin, f'<option value="{category.slug}">New Gifts</option>')
        self.assertContains(product_admin, f'<option value="{flags.slug}">Flags</option>')

        category_admin = self.client.get(reverse('admin:store_category_add'))
        self.assertEqual(category_admin.status_code, 200)
        self.assertContains(category_admin, 'name="description"')
        self.assertContains(category_admin, 'name="image"')
        self.assertContains(category_admin, 'name="parent"')

    def test_homepage_category_grid_groups_all_subcategories_under_roots(self):
        homepage = self.client.get(reverse('home'))
        self.assertEqual(homepage.status_code, 200)

        root_categories = list(
            Category.objects.filter(parent__isnull=True).order_by('name')
        )
        child_categories = list(
            Category.objects.filter(parent__isnull=False).select_related('parent')
        )
        self.assertEqual(list(homepage.context['homepage_categories']), root_categories)

        for category in root_categories:
            self.assertContains(homepage, f'data-category="{category.slug}"')
        for subcategory in child_categories:
            self.assertNotContains(
                homepage,
                f'data-category="{subcategory.slug}"',
            )
            self.assertContains(
                homepage,
                f'href="{reverse("category_products", args=[subcategory.slug])}"',
            )