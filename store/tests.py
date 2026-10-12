from decimal import Decimal
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Order, OrderItem, Product


class CheckoutFlowTests(TestCase):
	def setUp(self):
		self.product = Product.objects.create(
			name='Test Jamaican Shirt',
			slug='test-jamaican-shirt',
			description='A test product',
			price=Decimal('28.00'),
			category='men',
		)

	def test_add_to_cart_and_checkout_use_database_product(self):
		detail = self.client.get(
			reverse('Product_Detail', args=[self.product.slug])
		)
		self.assertContains(
			detail,
			reverse('add_to_cart', args=[self.product.pk]),
		)

		response = self.client.post(
			reverse('add_to_cart', args=[self.product.pk]),
			{'quantity': '2'},
		)

		self.assertRedirects(response, reverse('checkout'))
		checkout = self.client.get(reverse('checkout'))
		self.assertContains(checkout, self.product.name)
		self.assertContains(checkout, '$28.00 each')
		self.assertContains(checkout, '$56.00')

	def test_valid_order_opens_whatsapp_and_keeps_cart(self):
		session = self.client.session
		session['cart'] = {str(self.product.pk): 2}
		session['promo_code'] = 'ISLAND10'
		session.save()

		response = self.client.post(reverse('submit_order'), {
			'customer_name': 'John Brown',
			'phone': '876-555-1234',
			'delivery_address': 'Example Resort',
			'room': '214',
			'delivery_time': 'Afternoon (12-4)',
			'cash_note': '$100 bill',
			'delivery_notes': 'Call at the lobby.',
			'subtotal': '0.01',
			'total': '0.01',
		})

		order = Order.objects.get()
		item = OrderItem.objects.get(order=order)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Press Send in WhatsApp to place the order.')
		self.assertContains(response, 'const phoneNumber = "18762058967";')
		self.assertContains(response, 'window.location.href = whatsappURL;')
		self.assertContains(response, 'John Brown')
		self.assertContains(response, 'Example Resort')
		self.assertContains(response, 'Call at the lobby.')
		self.assertContains(response, self.product.name)
		self.assertContains(response, '"quantity": 2')
		self.assertContains(response, '"unit_price": "28.00"')
		self.assertContains(response, '"line_total": "56.00"')
		self.assertEqual(order.subtotal, Decimal('56.00'))
		self.assertEqual(order.discount, Decimal('5.60'))
		self.assertEqual(order.total, Decimal('50.40'))
		self.assertEqual(item.product_reference_id, self.product.pk)
		self.assertEqual(item.product_name, self.product.name)
		self.assertEqual(item.unit_price, Decimal('28.00'))
		self.assertEqual(item.quantity, 2)
		self.assertEqual(order.notification_status, 'pending')
		self.assertEqual(order.notification_error, '')
		self.assertEqual(self.client.session.get('cart'), {str(self.product.pk): 2})
		self.assertEqual(self.client.session.get('promo_code'), 'ISLAND10')

	def test_invalid_checkout_data_does_not_create_order_or_clear_cart(self):
		session = self.client.session
		session['cart'] = {str(self.product.pk): 1}
		session.save()

		response = self.client.post(reverse('submit_order'), {
			'customer_name': 'John Brown',
			'phone': 'not-a-phone',
			'delivery_address': 'Example Resort',
			'room': '214',
			'delivery_time': 'ASAP',
			'cash_note': 'Exact amount',
		})

		self.assertEqual(response.status_code, 400)
		self.assertContains(response, 'Enter a valid phone or WhatsApp number.', status_code=400)
		self.assertFalse(Order.objects.exists())
		self.assertEqual(self.client.session.get('cart'), {str(self.product.pk): 1})

	def test_checkout_submission_requires_csrf(self):
		client = Client(enforce_csrf_checks=True)
		client.get(reverse('checkout'))
		response = client.post(reverse('submit_order'), {})
		self.assertEqual(response.status_code, 403)


class CategoryHierarchyTests(TestCase):
	def test_requested_categories_are_seeded_under_their_existing_parents(self):
		category_slugs = {
			'liquor': ['white-rum', 'dark-rum', 'spiced-rum', 'gold-rum', 'rum-cream'],
			'coffee': [
				'blue-mountain-coffee', 'jablum-instant', 'cafe-coffee-roaster',
				'mocha-island', 'classic-decaf', 'cafe-expresso-blend-coffee',
			],
			'cake': [
				'original-jamaican-rum-cake', 'black-rum-cake', 'white-rum-cake',
				'coconut-rum-cake', 'pineapple-rum-cake', 'banana-rum-cake',
				'fruit-rum-cake', 'chocolate-rum-cake', 'ginger-rum-cake',
				'mini-rum-cakes-gift-boxes',
			],
		}
		for parent_slug, child_slugs in category_slugs.items():
			parent = Category.objects.get(slug=parent_slug)
			self.assertIsNone(parent.parent)
			self.assertSetEqual(
				set(parent.children.values_list('slug', flat=True)),
				set(child_slugs),
			)

	def test_product_admin_choices_and_category_slug_routes_include_new_categories(self):
		choices = dict(Product._meta.get_field('category').choices)
		for slug in (
			'white-rum', 'rum-cream', 'blue-mountain-coffee',
			'cafe-expresso-blend-coffee', 'original-jamaican-rum-cake',
			'mini-rum-cakes-gift-boxes',
		):
			self.assertIn(slug, choices)
			self.assertEqual(reverse('category_products', args=[slug]), f'/category/{slug}/')

	def test_homepage_places_coffee_and_cake_after_spices(self):
		response = self.client.get(reverse('home'))
		self.assertEqual(response.status_code, 200)
		content = response.content.decode()
		self.assertLess(content.index('>Spices</h3>'), content.index('data-category="coffee"'))
		self.assertLess(content.index('data-category="coffee"'), content.index('data-category="cake"'))
		self.assertLess(content.index('data-category="cake"'), content.index('data-category="liquor"'))
