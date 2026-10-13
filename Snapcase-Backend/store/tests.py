import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Brand, CartItem, Category, CustomerProfile, Order, OrderItem, Payment, PhoneModel, Product, ProductReview


class CartApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='shopper@example.com',
            email='shopper@example.com',
            password='SecurePassword123!',
        )

    def post_json(self, path, data):
        return self.client.post(path, data=json.dumps(data), content_type='application/json')

    def test_cart_requires_login(self):
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, 401)

    def test_cart_add_update_and_remove(self):
        self.client.force_login(self.user)

        added = self.post_json('/api/cart/', {'product_id': 'daisy'})
        self.assertEqual(added.status_code, 200)
        self.assertEqual(added.json()['count'], 1)
        self.assertEqual(added.json()['total'], 499)

        increased = self.post_json('/api/cart/', {'product_id': 'daisy'})
        self.assertEqual(increased.json()['count'], 2)
        self.assertEqual(increased.json()['total'], 998)

        updated = self.client.patch(
            '/api/cart/',
            data=json.dumps({'product_id': 'daisy', 'quantity': 3}),
            content_type='application/json',
        )
        self.assertEqual(updated.json()['count'], 3)
        self.assertEqual(updated.json()['total'], 1497)

        removed = self.client.delete(
            '/api/cart/',
            data=json.dumps({'product_id': 'daisy'}),
            content_type='application/json',
        )
        self.assertEqual(removed.json()['items'], [])
        self.assertEqual(removed.json()['total'], 0)

    def test_cart_removes_unavailable_products_and_reports_accurate_count(self):
        brand = Brand.objects.create(name='Cart Test Brand')
        category = Category.objects.create(name='Cart Test Category')
        product = Product.objects.create(
            name='Unavailable Cover',
            slug='unavailable-cover',
            brand=brand,
            category=category,
            description='A product that became unavailable.',
            price='299.00',
            stock=0,
            is_active=False,
        )
        product_id = f'db-{product.pk}'
        CartItem.objects.create(user=self.user, product_id=product_id)
        CartItem.objects.create(user=self.user, product_id='daisy', quantity=2)
        self.client.force_login(self.user)

        cart = self.client.get('/api/cart/').json()
        session = self.client.get('/api/session/').json()

        self.assertEqual(cart['count'], 2)
        self.assertEqual([item['product_id'] for item in cart['items']], ['daisy'])
        self.assertEqual(session['count'], 2)
        self.assertFalse(CartItem.objects.filter(user=self.user, product_id=product_id).exists())

    def test_cart_can_remove_a_product_that_became_unavailable(self):
        brand = Brand.objects.create(name='Inactive Cart Brand')
        category = Category.objects.create(name='Inactive Cart Category')
        product = Product.objects.create(
            name='Inactive Cover',
            slug='inactive-cover',
            brand=brand,
            category=category,
            description='A product removed from the active catalog.',
            price='199.00',
            stock=0,
            is_active=False,
        )
        product_id = f'db-{product.pk}'
        CartItem.objects.create(user=self.user, product_id=product_id)
        self.client.force_login(self.user)

        response = self.client.delete(
            '/api/cart/',
            data=json.dumps({'product_id': product_id}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])
        self.assertFalse(CartItem.objects.filter(user=self.user, product_id=product_id).exists())

    def test_cart_rejects_unknown_products_and_invalid_quantities(self):
        self.client.force_login(self.user)
        unknown_product = self.post_json('/api/cart/', {'product_id': 'not-a-product'})
        self.assertEqual(unknown_product.status_code, 400)

        self.post_json('/api/cart/', {'product_id': 'daisy'})
        invalid_quantity = self.client.patch(
            '/api/cart/',
            data=json.dumps({'product_id': 'daisy', 'quantity': True}),
            content_type='application/json',
        )
        self.assertEqual(invalid_quantity.status_code, 400)

    def test_registration_creates_account_and_profile(self):
        response = self.post_json('/api/register/', {
            'full_name': 'Taylor Shopper',
            'phone': '1234567890',
            'address': '12 Sample Street',
            'email': 'taylor@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.client.session.get('_auth_user_id'))
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_login_requires_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get('/login.html')
        self.assertEqual(page.status_code, 200)
        response = client.post(
            '/api/login/',
            data=json.dumps({'email': 'shopper@example.com', 'password': 'SecurePassword123!'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            '/api/login/',
            data=json.dumps({'email': 'shopper@example.com', 'password': 'SecurePassword123!'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get('/api/session/').json()['authenticated'], True)


class AuthenticationPageTests(TestCase):
    def test_main_pages_render_with_root_relative_static_assets(self):
        for path in ('/', '/login/', '/Registration.html', '/home.html', '/home/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '/static/')
                self.assertNotContains(response, '{%')

    def test_login_and_registration_pages_show_back_navigation_and_notifications(self):
        login_page = self.client.get('/login.html')
        registration_page = self.client.get('/Registration.html')

        self.assertEqual(login_page.status_code, 200)
        self.assertContains(login_page, 'Back to home')
        self.assertEqual(registration_page.status_code, 200)
        self.assertContains(registration_page, 'Back to home')
        self.assertContains(registration_page, 'form-error')
        self.assertContains(registration_page, 'notification-success')

    def test_login_error_appears_as_notification(self):
        response = self.client.post('/login/', {
            'username_or_email': 'missing@example.com',
            'password': 'wrong-password',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username/email or password.')
        self.assertContains(response, 'auth-notification message-error')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_forgot_password_flow_stays_on_customer_pages(self):
        user = get_user_model().objects.create_user(
            username='reset@example.com',
            email='reset@example.com',
            password='SecurePassword123!',
        )
        login_page = self.client.get('/login.html')
        self.assertContains(login_page, 'href="/accounts/password_reset/"')

        reset_page = self.client.get('/accounts/password_reset/')
        self.assertEqual(reset_page.status_code, 200)
        self.assertContains(reset_page, 'Reset your password')
        self.assertNotContains(reset_page, 'admin-shell')

        response = self.client.post('/accounts/password_reset/', {'email': user.email})
        self.assertRedirects(response, '/accounts/password_reset/done/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/accounts/reset/', mail.outbox[0].body)

        done_page = self.client.get('/accounts/password_reset/done/')
        self.assertEqual(done_page.status_code, 200)
        self.assertContains(done_page, 'Check your email')
        self.assertNotContains(done_page, 'admin-shell')

        encoded_user_id = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_path = f'/accounts/reset/{encoded_user_id}/{token}/'
        confirm_page = self.client.get(confirm_path, follow=True)
        self.assertEqual(confirm_page.status_code, 200)
        self.assertContains(confirm_page, 'Choose a new password')
        self.assertNotContains(confirm_page, 'admin-shell')

        response = self.client.post(f'/accounts/reset/{encoded_user_id}/set-password/', {
            'new_password1': 'NewSecurePassword456!',
            'new_password2': 'NewSecurePassword456!',
        })
        self.assertRedirects(response, '/accounts/reset/done/')

        complete_page = self.client.get('/accounts/reset/done/')
        self.assertEqual(complete_page.status_code, 200)
        self.assertContains(complete_page, 'Password updated')
        self.assertNotContains(complete_page, 'admin-shell')
        self.assertTrue(self.client.login(username=user.username, password='NewSecurePassword456!'))


class CustomerAccountAndOrderTests(TestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username='customer@example.com',
            email='customer@example.com',
            first_name='Casey Customer',
            password='SecurePassword123!',
        )
        self.profile = CustomerProfile.objects.create(
            user=self.customer,
            phone='1234567890',
            address='10 Sample Street',
        )
        self.category, _ = Category.objects.get_or_create(name='Customer Test Cases')
        self.brand, _ = Brand.objects.get_or_create(name='Customer Test Brand')
        self.phone_model, _ = PhoneModel.objects.get_or_create(brand=self.brand, name='Customer Test Model')
        self.product = Product.objects.create(
            name='Galaxy Test Cover',
            slug='galaxy-test-cover',
            brand=self.brand,
            phone_model=self.phone_model,
            category=self.category,
            description='A cover used to test customer orders.',
            price='499.00',
            stock=5,
        )

    def test_login_adds_requested_product_and_returns_to_storefront(self):
        response = self.client.post('/login/', {
            'username_or_email': self.customer.username,
            'password': 'SecurePassword123!',
            'next': '/home.html',
            'product': f'db-{self.product.pk}',
        })

        self.assertRedirects(response, '/home.html')
        cart_item = CartItem.objects.get(user=self.customer, product_id=f'db-{self.product.pk}')
        self.assertEqual(cart_item.quantity, 1)

    def test_customer_can_update_profile_and_view_empty_order_history(self):
        self.client.force_login(self.customer)

        response = self.client.post('/account/', {
            'name': 'Casey Updated',
            'email': 'updated@example.com',
            'phone': '9876543210',
            'address': '22 New Sample Road',
        })

        self.assertRedirects(response, '/account/')
        self.customer.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.customer.first_name, 'Casey Updated')
        self.assertEqual(self.customer.email, 'updated@example.com')
        self.assertEqual(self.customer.username, 'updated@example.com')
        self.assertEqual(self.profile.phone, '9876543210')
        self.assertEqual(self.profile.address, '22 New Sample Road')
        self.assertContains(self.client.get('/orders/'), 'No orders yet')

    def test_customer_account_and_orders_require_authentication(self):
        self.assertRedirects(self.client.get('/account/'), '/login/?next=/account/')
        self.assertRedirects(self.client.get('/orders/'), '/login/?next=/orders/')
        cart_page = self.client.get('/cart.html')
        self.assertEqual(cart_page.status_code, 200)
        self.assertContains(cart_page, 'Place order')
        self.assertContains(cart_page, 'csrfmiddlewaretoken')

    def test_checkout_creates_order_items_pending_cod_payment_and_updates_stock(self):
        self.client.force_login(self.customer)
        CartItem.objects.create(user=self.customer, product_id=f'db-{self.product.pk}', quantity=2)

        response = self.client.post('/checkout/', {'shipping_address': '12 Delivery Avenue'})

        order = Order.objects.get(customer=self.customer)
        order_item = OrderItem.objects.get(order=order)
        payment = Payment.objects.get(order=order)
        self.assertRedirects(response, f'/orders/{order.pk}/')
        self.assertEqual(order.total, Decimal('998.00'))
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.line_total, Decimal('998.00'))
        self.assertEqual(payment.payment_method, 'Cash on Delivery')
        self.assertEqual(payment.status, 'Pending')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(CartItem.objects.filter(user=self.customer).exists())
        self.assertContains(self.client.get('/orders/'), order.order_number)
        self.assertContains(self.client.get(f'/orders/{order.pk}/'), self.product.name)

    def test_customer_cannot_view_another_users_order(self):
        another_customer = get_user_model().objects.create_user(
            username='another@example.com',
            email='another@example.com',
            password='SecurePassword123!',
        )
        order = Order.objects.create(
            customer=another_customer,
            order_number='SC-OTHER-ORDER',
            total='499.00',
        )
        self.client.force_login(self.customer)

        response = self.client.get(f'/orders/{order.pk}/')

        self.assertEqual(response.status_code, 404)

    def test_checkout_rejects_insufficient_stock_without_creating_order(self):
        self.client.force_login(self.customer)
        CartItem.objects.create(user=self.customer, product_id=f'db-{self.product.pk}', quantity=6)

        response = self.client.post('/checkout/', {'shipping_address': '12 Delivery Avenue'})

        self.assertRedirects(response, '/cart.html')
        self.assertFalse(Order.objects.filter(customer=self.customer).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)


class AndroidStorefrontTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='SecurePassword123!',
        )
        self.apple = Brand.objects.create(name='Apple')
        self.apple_model = PhoneModel.objects.create(brand=self.apple, name='iPhone Test')
        self.category = Category.objects.create(name='Test Cases')
        self.apple_product = Product.objects.create(
            name='iPhone Test Cover',
            slug='iphone-test-cover',
            brand=self.apple,
            phone_model=self.apple_model,
            category=self.category,
            description='Apple phone cover for storefront filtering test.',
            price='499.00',
            stock=5,
        )

    def test_storefront_only_shows_android_brands_and_products(self):
        response = self.client.get('/home.html')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'iPhone Test Cover')
        self.assertNotContains(response, '>Apple</option>')
        self.assertContains(response, 'Samsung')
        self.assertContains(response, 'Realme')

    def test_add_to_cart_feedback_is_shown_without_redirecting_to_cart(self):
        brand = Brand.objects.create(name='Test Android')
        phone_model = PhoneModel.objects.create(brand=brand, name='Test Android Model')
        product = Product.objects.create(
            name='Test Android Cover',
            slug='test-android-cover',
            brand=brand,
            phone_model=phone_model,
            category=self.category,
            description='A product for add-to-cart feedback tests.',
            price='499.00',
            stock=5,
        )

        storefront = self.client.get('/home.html')
        detail = self.client.get(f'/products/{product.pk}/')

        self.assertContains(storefront, f'data-product-id="db-{product.pk}"')
        self.assertContains(storefront, 'class="cart-item-status"')
        self.assertNotContains(storefront, 'window.location.href = "/cart.html"')
        self.assertContains(detail, 'id="detail-message"')
        self.assertNotContains(detail, 'window.location.href = "/cart.html"')

    def test_apple_product_detail_is_not_available_in_storefront(self):
        response = self.client.get(f'/products/{self.apple_product.pk}/')

        self.assertEqual(response.status_code, 404)

    def test_customer_can_add_one_review_and_storefront_aggregates_rating(self):
        brand, _ = Brand.objects.get_or_create(name='Realme')
        phone_model = PhoneModel.objects.create(brand=brand, name='Realme Test')
        product = Product.objects.create(
            name='Realme Test Cover',
            slug='realme-test-cover',
            brand=brand,
            phone_model=phone_model,
            category=self.category,
            description='A test cover for Android review testing.',
            price='399.00',
            stock=4,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            f'/products/{product.pk}/reviews/',
            {'rating': '5', 'title': 'Great fit', 'body': 'Fits the phone perfectly and feels sturdy.'},
        )

        self.assertRedirects(response, f'/products/{product.pk}/')
        self.assertEqual(ProductReview.objects.filter(product=product, customer=self.user).count(), 1)
        detail = self.client.get(f'/products/{product.pk}/')
        self.assertContains(detail, '5.0 out of 5')
        self.assertContains(detail, 'Fits the phone perfectly and feels sturdy.')

    def test_demo_reviews_are_labeled_and_disclosed_as_samples(self):
        product = Product.objects.get(slug='realme-12-pro-clear-cover')
        sample_review = ProductReview.objects.get(product=product, is_sample=True)

        self.assertIsNone(sample_review.customer)
        detail = self.client.get(f'/products/{product.pk}/')
        self.assertContains(detail, 'Includes 1 labeled sample review')
        self.assertContains(detail, 'SnapCase sample review')
