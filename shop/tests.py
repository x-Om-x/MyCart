import json

from django.test import TestCase
from django.urls import reverse

from .models import Order, Product
from .views import search_products

# Create your tests here.
class OrderInvoiceTests(TestCase):
	def setUp(self):
		self.product = Product.objects.create(
			product_name='Test product',
			category='Test',
			subcategory='Test',
			price=250,
			desc='A product used for invoice tests',
			pub_date='2026-01-01',
		)

	def test_checkout_uses_saved_product_price_and_downloads_invoice(self):
		response = self.client.post(reverse('Checkout'), {
			'itemsJson': json.dumps({f'pr{self.product.pk}': [2, 'Forged name', 1]}),
			'name': 'Test Customer',
			'email': 'customer@example.com',
			'address1': '1 Test Street',
			'city': 'Test City',
			'state': 'Test State',
			'zip_code': '12345',
			'phone': '5551234567',
			'amount': '2',
		})

		self.assertEqual(response.status_code, 200)
		order = Order.objects.get()
		self.assertEqual(order.amount, 500)
		self.assertEqual(
			json.loads(order.items_json),
			{f'pr{self.product.pk}': [2, 'Test product', 250]},
		)

		invoice = self.client.get(reverse('OrderInvoice', args=[response.context['pdf_token']]))
		self.assertEqual(invoice.status_code, 200)
		self.assertEqual(invoice['Content-Type'], 'application/pdf')
		self.assertTrue(invoice.content.startswith(b'%PDF'))

	def test_invoice_rejects_an_invalid_token(self):
		response = self.client.get(reverse('OrderInvoice', args=['invalid-token']))

		self.assertEqual(response.status_code, 404)


class ProductSearchTests(TestCase):
	def setUp(self):
		self.product = Product.objects.create(
			product_name='Blue mug',
			category='Kitchen',
			subcategory='Drinkware',
			price=250,
			desc='Ceramic cup',
			pub_date='2026-01-01',
		)

	def test_search_products_matches_product_fields_case_insensitively(self):
		groups = search_products('MUG')

		self.assertEqual(groups[0][0], [self.product])

	def test_search_page_shows_message_when_no_products_match(self):
		response = self.client.get(reverse('Search'), {'search': 'missing item'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'No results found for "missing item".')
