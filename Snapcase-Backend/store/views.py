import json
import secrets
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import Brand, CartItem, Category, CustomerProfile, Order, OrderItem, Payment, PhoneModel, Product, ProductReview


PRODUCTS = {
    'daisy': {'name': 'Daisy Vibes Case', 'price': 499, 'image': 'static/images/daisy-case.jpg'},
    'smile': {'name': 'Smile Always Case', 'price': 449, 'image': 'static/images/smile-case.jpg'},
    'floral': {'name': 'Floral Clear Case', 'price': 549, 'image': 'static/images/floral-case.jpg'},
    'pastel': {'name': 'Pastel Waves Case', 'price': 599, 'image': 'static/images/pastel-case.jpg'},
    'pink': {'name': 'Soft Pink Case', 'price': 549, 'image': 'static/images/plain-pink.jpg'},
    'rugged': {'name': 'Rugged Pro Case', 'price': 649, 'image': 'static/images/black-case.jpg'},
    'check': {'name': 'Trendy Check Case', 'price': 379, 'image': 'static/images/check-case.jpg'},
    'geo': {'name': 'Pink Geo Case', 'price': 499, 'image': 'static/images/heart-case.jpg'},
}


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@ensure_csrf_cookie
def frontend_page(request, template_name):
    context = {
        'next': request.GET.get('next', ''),
        'product': request.GET.get('product', ''),
    }
    if template_name == 'cart.html' and request.user.is_authenticated:
        profile = CustomerProfile.objects.filter(user=request.user).first()
        context['shipping_address'] = profile.address if profile else ''
    return render(request, template_name, context)


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    user_queryset = get_user_model().objects.filter(is_staff=False)
    revenue = Order.objects.aggregate(total_sales=Sum('total'))['total_sales'] or Decimal('0')
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    inventory = Product.objects.filter(is_active=True).order_by('-stock')[:5]

    context = {
        'total_products': Product.objects.count(),
        'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(),
        'total_users': user_queryset.count(),
        'total_revenue': revenue,
        'recent_orders': recent_orders,
        'inventory_summary': inventory,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def product_management(request):
    search = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')

    products = Product.objects.select_related('category', 'brand', 'phone_model').order_by('-created_at')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if category_filter:
        products = products.filter(category_id=category_filter)
    if brand_filter:
        products = products.filter(brand_id=brand_filter)

    selected_product = None
    edit_id = request.GET.get('edit')
    if edit_id:
        selected_product = get_object_or_404(Product, pk=edit_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            product.delete()
            messages.success(request, f'{product.name} was deleted successfully.')
            return redirect('admin_products')

        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        category_id = request.POST.get('category') or None
        brand_id = request.POST.get('brand') or None
        phone_model_id = request.POST.get('phone_model') or None
        price = request.POST.get('price', '0')
        stock = request.POST.get('stock', '0')

        if not name or not description:
            messages.error(request, 'Product name and description are required.')
        else:
            try:
                price_value = Decimal(str(price))
                stock_value = int(stock)
            except Exception:
                messages.error(request, 'Price and stock must be valid numbers.')
                price_value = Decimal('0')
                stock_value = 0

            if price_value <= 0:
                messages.error(request, 'Price must be greater than zero.')
            elif stock_value < 0:
                messages.error(request, 'Stock cannot be negative.')
            else:
                product_id = request.POST.get('product_id')
                product = Product.objects.filter(pk=product_id).first() if product_id else None
                if product is None:
                    product = Product()
                product.name = name
                product.description = description
                product.category_id = category_id
                product.brand_id = brand_id
                product.phone_model_id = phone_model_id
                product.price = price_value
                product.stock = stock_value
                product.is_active = request.POST.get('is_active') == 'on'
                product.slug = slugify(name)
                if product.pk:
                    base_slug = product.slug
                    counter = 1
                    while Product.objects.filter(slug=product.slug).exclude(pk=product.pk).exists():
                        product.slug = f'{base_slug}-{counter}'
                        counter += 1
                else:
                    base_slug = product.slug
                    counter = 1
                    while Product.objects.filter(slug=product.slug).exists():
                        product.slug = f'{base_slug}-{counter}'
                        counter += 1

                uploaded_image = request.FILES.get('image')
                if uploaded_image:
                    product.image = uploaded_image
                elif request.POST.get('remove_image') == 'on' and product.image:
                    product.image.delete(save=False)
                    product.image = None

                product.save()
                messages.success(request, f'{product.name} saved successfully.')
                return redirect('admin_products')

    context = {
        'products': products,
        'categories': Category.objects.order_by('name'),
        'brands': Brand.objects.order_by('name'),
        'selected_product': selected_product,
        'search': search,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'phone_models': PhoneModel.objects.select_related('brand').order_by('brand__name', 'name'),
    }
    return render(request, 'admin_products.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_management(request):
    category_queryset = Category.objects.order_by('name')
    search = (request.GET.get('search') or '').strip()
    if search:
        category_queryset = category_queryset.filter(name__icontains=search)

    selected_category = None
    edit_id = request.GET.get('edit')
    if edit_id:
        selected_category = get_object_or_404(Category, pk=edit_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            category.delete()
            messages.success(request, f'{category.name} was deleted successfully.')
            return redirect('admin_categories')

        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
        else:
            category_id = request.POST.get('category_id')
            category = Category.objects.filter(pk=category_id).first() if category_id else Category()
            category.name = name
            category.description = description
            category.save()
            messages.success(request, f'{category.name} saved successfully.')
            return redirect('admin_categories')

    context = {
        'categories': category_queryset,
        'selected_category': selected_category,
        'search': search,
    }
    return render(request, 'admin_categories.html', context)


@login_required
@user_passes_test(is_admin_user)
def brand_management(request):
    search = (request.GET.get('search') or '').strip()
    brand_queryset = Brand.objects.order_by('name')
    if search:
        brand_queryset = brand_queryset.filter(name__icontains=search)

    selected_brand = None
    edit_id = request.GET.get('edit')
    if edit_id:
        selected_brand = get_object_or_404(Brand, pk=edit_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            brand = get_object_or_404(Brand, pk=request.POST.get('brand_id'))
            brand.delete()
            messages.success(request, f'{brand.name} was deleted successfully.')
            return redirect('admin_brands')

        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Brand name is required.')
        else:
            brand_id = request.POST.get('brand_id')
            brand = Brand.objects.filter(pk=brand_id).first() if brand_id else Brand()
            brand.name = name
            brand.save()
            messages.success(request, f'{brand.name} saved successfully.')
            return redirect('admin_brands')

    context = {
        'brands': brand_queryset,
        'selected_brand': selected_brand,
        'search': search,
    }
    return render(request, 'admin_brands.html', context)


@login_required
@user_passes_test(is_admin_user)
def phone_model_management(request):
    search = (request.GET.get('search') or '').strip()
    brand_filter = request.GET.get('brand_filter', '')
    models_queryset = PhoneModel.objects.select_related('brand').order_by('brand__name', 'name')
    if search:
        models_queryset = models_queryset.filter(Q(name__icontains=search) | Q(brand__name__icontains=search))
    if brand_filter:
        models_queryset = models_queryset.filter(brand_id=brand_filter)

    selected_model = None
    edit_id = request.GET.get('edit')
    if edit_id:
        selected_model = get_object_or_404(PhoneModel, pk=edit_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            model = get_object_or_404(PhoneModel, pk=request.POST.get('model_id'))
            model.delete()
            messages.success(request, f'{model.name} was deleted successfully.')
            return redirect('admin_phone_models')

        brand_id = request.POST.get('brand')
        model_name = (request.POST.get('name') or '').strip()
        if not brand_id or not model_name:
            messages.error(request, 'Please select a brand and enter a model name.')
        else:
            model_id = request.POST.get('model_id')
            model = PhoneModel.objects.filter(pk=model_id).first() if model_id else PhoneModel()
            model.brand_id = brand_id
            model.name = model_name
            model.save()
            messages.success(request, f'{model.name} saved successfully.')
            return redirect('admin_phone_models')

    context = {
        'models': models_queryset,
        'brands': Brand.objects.order_by('name'),
        'selected_model': selected_model,
        'search': search,
        'brand_filter': brand_filter,
    }
    return render(request, 'admin_phone_models.html', context)


@login_required
@user_passes_test(is_admin_user)
def order_management(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')
    search = (request.GET.get('search') or '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(customer__username__icontains=search)
            | Q(customer__email__icontains=search)
            | Q(customer__first_name__icontains=search)
            | Q(customer__last_name__icontains=search)
        )
    if status_filter:
        orders = orders.filter(status=status_filter)

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        if order_id and new_status:
            order = get_object_or_404(Order, pk=order_id)
            order.status = new_status
            order.save()
            messages.success(request, f'Order {order.order_number} updated to {new_status}.')
            return redirect('admin_orders')

    orders_with_items = []
    for order in orders:
        order_items = order.items.select_related('product')
        orders_with_items.append({'order': order, 'items': order_items})

    context = {
        'orders': orders_with_items,
        'search': search,
        'status_filter': status_filter,
        'order_statuses': [choice[0] for choice in Order.STATUS_CHOICES],
    }
    return render(request, 'admin_orders.html', context)


@login_required
def customer_account(request):
    if is_admin_user(request.user):
        return redirect('admin_dashboard')

    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        phone = (request.POST.get('phone') or '').strip()
        address = (request.POST.get('address') or '').strip()

        if len(name) < 2 or len(name) > 80:
            messages.error(request, 'Enter a name between 2 and 80 characters.')
        elif len(email) > 150:
            messages.error(request, 'Email addresses must be 150 characters or fewer.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Enter a valid email address.')
            else:
                User = get_user_model()
                email_in_use = User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists()
                username_in_use = User.objects.filter(username__iexact=email).exclude(pk=request.user.pk).exists()
                if email_in_use or username_in_use:
                    messages.error(request, 'An account with this email already exists.')
                elif phone and (len(phone) != 10 or not phone.isdigit()):
                    messages.error(request, 'Enter a valid 10-digit phone number or leave it blank.')
                elif len(address) > 200:
                    messages.error(request, 'Address must be 200 characters or fewer.')
                else:
                    request.user.first_name = name
                    request.user.email = email
                    request.user.username = email
                    request.user.save(update_fields=['first_name', 'email', 'username'])
                    profile.phone = phone
                    profile.address = address
                    profile.save(update_fields=['phone', 'address'])
                    messages.success(request, 'Your profile was updated successfully.')
                    return redirect('customer_account')

    recent_orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')[:3]
    return render(request, 'customer_account.html', {
        'profile': profile,
        'customer_name': request.POST.get('name', request.user.first_name),
        'customer_email': request.POST.get('email', request.user.email),
        'customer_phone': request.POST.get('phone', profile.phone),
        'customer_address': request.POST.get('address', profile.address),
        'recent_orders': recent_orders,
        'total_orders': request.user.orders.count(),
    })


@login_required
def customer_orders(request):
    if is_admin_user(request.user):
        return redirect('admin_dashboard')
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'customer_orders.html', {'orders': orders})


@login_required
def customer_order_detail(request, order_id):
    if is_admin_user(request.user):
        return redirect('admin_dashboard')
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product').select_related('payment'),
        pk=order_id,
        customer=request.user,
    )
    return render(request, 'customer_order_detail.html', {'order': order})


@login_required
@require_http_methods(['POST'])
def place_order(request):
    if is_admin_user(request.user):
        return redirect('admin_dashboard')

    shipping_address = (request.POST.get('shipping_address') or '').strip()
    if len(shipping_address) < 5 or len(shipping_address) > 500:
        messages.error(request, 'Enter a delivery address between 5 and 500 characters.')
        return redirect('cart')

    cart_items = list(CartItem.objects.filter(user=request.user).order_by('added_at', 'id'))
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    cart_product_ids = [item.product_id for item in cart_items]
    if any(not product_id.startswith('db-') or not product_id[3:].isdigit() for product_id in cart_product_ids):
        messages.error(request, 'One or more cart items are no longer available for checkout. Remove them and try again.')
        return redirect('cart')

    try:
        with transaction.atomic():
            products_by_id = {
                f'db-{product.pk}': product
                for product in Product.objects.select_for_update().filter(
                    pk__in=[product_id[3:] for product_id in cart_product_ids],
                    is_active=True,
                )
            }
            if len(products_by_id) != len(set(cart_product_ids)):
                raise ValueError('One or more products are no longer available.')

            for cart_item in cart_items:
                product = products_by_id[cart_item.product_id]
                if cart_item.quantity > product.stock:
                    raise ValueError(f'Only {product.stock} unit(s) of {product.name} are currently in stock.')

            total = sum(
                (products_by_id[item.product_id].price * item.quantity for item in cart_items),
                Decimal('0.00'),
            )
            order_number = f"SC-{timezone.now():%Y%m%d%H%M%S}-{secrets.token_hex(3).upper()}"
            order = Order.objects.create(
                customer=request.user,
                order_number=order_number,
                total=total,
                shipping_address=shipping_address,
            )
            for cart_item in cart_items:
                product = products_by_id[cart_item.product_id]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                )
                product.stock -= cart_item.quantity
                product.save(update_fields=['stock'])
            Payment.objects.create(
                order=order,
                customer=request.user,
                amount=total,
                payment_method='Cash on Delivery',
                status='Pending',
            )
            CartItem.objects.filter(user=request.user).delete()
    except ValueError as error:
        messages.error(request, str(error))
        return redirect('cart')

    messages.success(request, f'Order {order.order_number} was placed successfully.')
    return redirect('customer_order_detail', order_id=order.pk)


@login_required
@user_passes_test(is_admin_user)
def payment_management(request):
    payments = Payment.objects.select_related('order', 'customer').order_by('-payment_date')
    search = (request.GET.get('search') or '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        payments = payments.filter(
            Q(order__order_number__icontains=search)
            | Q(customer__username__icontains=search)
            | Q(customer__email__icontains=search)
        )
    if status_filter:
        payments = payments.filter(status=status_filter)

    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        payment_status = request.POST.get('status')
        verified = request.POST.get('verified') == 'on'
        if payment_id and payment_status:
            payment = get_object_or_404(Payment, pk=payment_id)
            if payment_status == 'Successful' and not verified:
                messages.error(request, 'Payment verification is required before marking a payment successful.')
            else:
                payment.status = payment_status
                payment.payment_reference = payment.payment_reference or request.POST.get('reference', '').strip()
                payment.notes = request.POST.get('notes', '').strip()
                payment.save()
                messages.success(request, f'Payment {payment.order.order_number} updated successfully.')
            return redirect('admin_payments')

    context = {
        'payments': payments,
        'search': search,
        'status_filter': status_filter,
        'payment_statuses': [choice[0] for choice in Payment.PAYMENT_STATUS_CHOICES],
    }
    return render(request, 'admin_payments.html', context)


@login_required
@user_passes_test(is_admin_user)
def user_management(request):
    User = get_user_model()
    users = User.objects.order_by('-date_joined')
    search = (request.GET.get('search') or '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, pk=user_id)
        if target_user.is_staff and target_user != request.user:
            messages.error(request, 'Administrator accounts are protected and cannot be altered from this view.')
            return redirect('admin_users')
        if target_user == request.user and action == 'deactivate':
            messages.error(request, 'You cannot deactivate your own account while logged in.')
            return redirect('admin_users')

        target_user.is_active = action == 'activate'
        target_user.save(update_fields=['is_active'])
        messages.success(request, f'{target_user.get_full_name() or target_user.username} was updated successfully.')
        return redirect('admin_users')

    context = {
        'users': users,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'admin_users.html', context)


def _json_body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _authenticated_user(request):
    if not request.user.is_authenticated:
        return None
    return request.user


def _cart_response(user):
    items = []
    unavailable_item_ids = []
    total = 0
    count = 0
    for item in CartItem.objects.filter(user=user).order_by('added_at', 'id'):
        product = PRODUCTS.get(item.product_id)
        if product is None and item.product_id.startswith('db-'):
            catalog_product = Product.objects.filter(
                pk=item.product_id[3:],
                is_active=True,
            ).first()
            if catalog_product is not None:
                product = {
                    'name': catalog_product.name,
                    'price': catalog_product.price,
                    'image': (
                        catalog_product.image.url
                        if catalog_product.image
                        else f'/static/images/{catalog_product.catalog_image}'
                        if catalog_product.catalog_image
                        else '/static/images/plain-clear.jpg'
                    ),
                }
        if product is None:
            unavailable_item_ids.append(item.pk)
            continue
        line_total = product['price'] * item.quantity
        total += line_total
        count += item.quantity
        items.append({
            'product_id': item.product_id,
            'name': product['name'],
            'price': product['price'],
            'image': product['image'],
            'quantity': item.quantity,
            'line_total': line_total,
        })
    if unavailable_item_ids:
        CartItem.objects.filter(pk__in=unavailable_item_ids).delete()
    return {'items': items, 'total': total, 'count': count}


@require_http_methods(['POST'])
def register(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Please submit valid registration details.'}, status=400)

    full_name = str(data.get('full_name', '')).strip()
    phone = str(data.get('phone', '')).strip()
    address = str(data.get('address', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not full_name or len(full_name) > 80 or len(full_name) < 2:
        return JsonResponse({'error': 'Enter a name between 2 and 80 characters.'}, status=400)
    if len(phone) != 10 or not phone.isdigit():
        return JsonResponse({'error': 'Enter a valid 10-digit phone number.'}, status=400)
    if len(address) < 5 or len(address) > 200:
        return JsonResponse({'error': 'Enter an address between 5 and 200 characters.'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Enter a valid email address.'}, status=400)
    if len(email) > 150:
        return JsonResponse({'error': 'Email addresses must be 150 characters or fewer.'}, status=400)
    if not isinstance(password, str) or not isinstance(confirm_password, str):
        return JsonResponse({'error': 'Enter a valid password.'}, status=400)
    if password != confirm_password:
        return JsonResponse({'error': 'Passwords do not match.'}, status=400)
    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)

    User = get_user_model()
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'error': 'An account with this email already exists.'}, status=400)

    with transaction.atomic():
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
        )
        CustomerProfile.objects.create(user=user, phone=phone, address=address)
    login(request, user)
    return JsonResponse({'ok': True, 'name': user.first_name}, status=201)


@require_http_methods(['POST'])
def login_view(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Please enter your email and password.'}, status=400)
    email = data.get('email', '')
    password = data.get('password', '')
    if not isinstance(email, str) or not isinstance(password, str):
        return JsonResponse({'error': 'Please enter your email and password.'}, status=400)
    email = email.strip().lower()

    user = authenticate(request, username=email, password=password)
    if user is None:
        user_obj = get_user_model().objects.filter(email__iexact=email).first()
        if user_obj is not None:
            user = authenticate(request, username=user_obj.username, password=password)
    if user is None:
        return JsonResponse({'error': 'Email or password is incorrect.'}, status=400)
    login(request, user)
    return JsonResponse({'ok': True, 'name': user.first_name})


@require_http_methods(['POST'])
def logout_view(request):
    if not _authenticated_user(request):
        return JsonResponse({'error': 'Please log in first.'}, status=401)
    logout(request)
    return JsonResponse({'ok': True})


@require_http_methods(['GET'])
def session_view(request):
    user = _authenticated_user(request)
    if user is None:
        return JsonResponse({'authenticated': False, 'count': 0})
    count = _cart_response(user)['count']
    return JsonResponse({'authenticated': True, 'name': user.first_name, 'count': count})


@require_http_methods(['GET', 'POST', 'PATCH', 'DELETE'])
def cart_view(request):
    user = _authenticated_user(request)
    if user is None:
        return JsonResponse({'error': 'Log in to use your cart.'}, status=401)
    if request.method == 'GET':
        return JsonResponse(_cart_response(user))

    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Please submit valid cart details.'}, status=400)
    product_id = data.get('product_id')
    if not isinstance(product_id, str) or not product_id or len(product_id) > 32:
        return JsonResponse({'error': 'That product is not available.'}, status=400)
    if request.method != 'DELETE':
        if product_id not in PRODUCTS:
            if not product_id.startswith('db-') or not product_id[3:].isdigit():
                return JsonResponse({'error': 'That product is not available.'}, status=400)
            if not Product.objects.filter(pk=product_id[3:], is_active=True).exists():
                return JsonResponse({'error': 'That product is not available.'}, status=400)

    if request.method == 'POST':
        item, created = CartItem.objects.get_or_create(
            user=user,
            product_id=product_id,
            defaults={'quantity': 1},
        )
        if not created:
            CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') + 1)
    elif request.method == 'PATCH':
        quantity = data.get('quantity')
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 99:
            return JsonResponse({'error': 'Quantity must be a whole number between 1 and 99.'}, status=400)
        updated = CartItem.objects.filter(user=user, product_id=product_id).update(quantity=quantity)
        if not updated:
            return JsonResponse({'error': 'That item is not in your cart.'}, status=404)
    else:
        deleted, _ = CartItem.objects.filter(user=user, product_id=product_id).delete()
        if not deleted:
            return JsonResponse({'error': 'That item is not in your cart.'}, status=404)

    return JsonResponse(_cart_response(user))


def common_login(request):
    if request.method == 'POST':
        username_or_email = (request.POST.get('username_or_email') or '').strip()
        password = request.POST.get('password') or ''
        next_url = request.POST.get('next', '')
        product_id = request.POST.get('product', '')

        if not username_or_email or not password:
            messages.error(request, 'Please enter both your username or email and password.')
            return render(request, 'login.html', {
                'username_or_email': username_or_email,
                'next': next_url,
                'product': product_id,
            })

        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            user_obj = get_user_model().objects.filter(email__iexact=username_or_email).first()
            if user_obj is not None:
                user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            messages.error(request, 'Invalid username/email or password.')
            return render(request, 'login.html', {
                'username_or_email': username_or_email,
                'next': next_url,
                'product': product_id,
            })

        login(request, user)
        if is_admin_user(user):
            return redirect('admin_dashboard')
        safe_next_url = next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        if safe_next_url and product_id.startswith('db-') and product_id[3:].isdigit():
            product = Product.objects.filter(pk=product_id[3:], is_active=True).first()
            if product is not None:
                item, created = CartItem.objects.get_or_create(
                    user=user,
                    product_id=product_id,
                    defaults={'quantity': 1},
                )
                if not created:
                    CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') + 1)
        if safe_next_url:
            return redirect(next_url)
        return redirect('customer_home')

    return render(request, 'login.html', {
        'next': request.GET.get('next', ''),
        'product': request.GET.get('product', ''),
    })


def logout_user(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@ensure_csrf_cookie
def customer_home(request):
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'brand', 'phone_model'
    ).filter(brand__isnull=False).exclude(brand__name__iexact='Apple').annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True),
        sample_review_count=Count('reviews', filter=Q(reviews__is_sample=True), distinct=True),
    )
    brand_id = request.GET.get('brand', '')
    model_id = request.GET.get('model', '')
    category_id = request.GET.get('category', '')

    if brand_id.isdigit():
        products = products.filter(brand_id=brand_id)
    else:
        brand_id = ''
    if model_id.isdigit():
        products = products.filter(phone_model_id=model_id)
    else:
        model_id = ''
    if category_id.isdigit():
        products = products.filter(category_id=category_id)
    else:
        category_id = ''

    selected_brand = (
        Brand.objects.filter(pk=brand_id).exclude(name__iexact='Apple').first()
        if brand_id else None
    )
    phone_models = (
        PhoneModel.objects.filter(brand=selected_brand).order_by('name')
        if selected_brand else PhoneModel.objects.none()
    )
    fallback_images = {
        'daisy-vibes-case': '/static/images/daisy-case.jpg',
        'pastel-waves-case': '/static/images/pastel-case.jpg',
        'black-shock-case': '/static/images/black-case.jpg',
        'plain-pink-case': '/static/images/plain-pink.jpg',
        'samsung-galaxy-s24-clear-cover': '/static/images/floral-case.jpg',
        'samsung-galaxy-a55-cover': '/static/images/check-case.jpg',
        'realme-12-pro-cover': '/static/images/daisy-case.jpg',
        'realme-narzo-70-cover': '/static/images/smile-case.jpg',
    }
    available_images = [
        '/static/images/daisy-case.jpg',
        '/static/images/smile-case.jpg',
        '/static/images/floral-case.jpg',
        '/static/images/pastel-case.jpg',
        '/static/images/black-case.jpg',
        '/static/images/check-case.jpg',
        '/static/images/heart-case.jpg',
        '/static/images/plain-pink.jpg',
        '/static/images/plain-yellow.jpg',
    ]
    storefront_products = [
        {
            'product': product,
            'rating_stars': int(round(product.average_rating or 0)),
            'image_url': (
                product.image.url
                if product.image
                else f'/static/images/{product.catalog_image}'
                if product.catalog_image
                else fallback_images.get(
                    product.slug,
                    available_images[product.pk % len(available_images)],
                )
            ),
        }
        for product in products.order_by('brand__name', 'phone_model__name', 'name')
    ]

    return render(request, 'storefront_home.html', {
        'featured_products': storefront_products,
        'brands': Brand.objects.exclude(name__iexact='Apple').order_by('name'),
        'categories': Category.objects.order_by('name'),
        'phone_models': phone_models,
        'selected_brand_id': brand_id,
        'selected_model_id': model_id,
        'selected_category_id': category_id,
    })


@ensure_csrf_cookie
def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand', 'phone_model')
        .filter(brand__isnull=False)
        .exclude(brand__name__iexact='Apple'),
        pk=product_id,
        is_active=True,
    )
    fallback_images = {
        'daisy-vibes-case': '/static/images/daisy-case.jpg',
        'pastel-waves-case': '/static/images/pastel-case.jpg',
        'black-shock-case': '/static/images/black-case.jpg',
        'plain-pink-case': '/static/images/plain-pink.jpg',
        'samsung-galaxy-s24-clear-cover': '/static/images/floral-case.jpg',
        'samsung-galaxy-a55-cover': '/static/images/check-case.jpg',
        'realme-12-pro-cover': '/static/images/daisy-case.jpg',
        'realme-narzo-70-cover': '/static/images/smile-case.jpg',
    }
    image_url = (
        product.image.url
        if product.image
        else f'/static/images/{product.catalog_image}'
        if product.catalog_image
        else fallback_images.get(product.slug, '/static/images/plain-clear.jpg')
    )
    related_products = Product.objects.filter(
        is_active=True,
        brand=product.brand,
        phone_model=product.phone_model,
    ).exclude(pk=product.pk).annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True),
        sample_review_count=Count('reviews', filter=Q(reviews__is_sample=True), distinct=True),
    ).order_by('name')[:4]
    related_entries = [
        {
            'product': related_product,
            'rating_stars': int(round(related_product.average_rating or 0)),
            'image_url': (
                related_product.image.url
                if related_product.image
                else f'/static/images/{related_product.catalog_image}'
                if related_product.catalog_image
                else fallback_images.get(related_product.slug, '/static/images/plain-clear.jpg')
            ),
        }
        for related_product in related_products
    ]
    rating_summary = product.reviews.aggregate(
        average_rating=Avg('rating'),
        review_count=Count('id'),
        sample_review_count=Count('id', filter=Q(is_sample=True)),
    )
    already_reviewed = (
        request.user.is_authenticated
        and product.reviews.filter(customer=request.user).exists()
    )
    return render(request, 'product_detail.html', {
        'product': product,
        'image_url': image_url,
        'related_products': related_entries,
        'reviews': product.reviews.select_related('customer').all(),
        'average_rating': rating_summary['average_rating'] or 0,
        'rating_stars': int(round(rating_summary['average_rating'] or 0)),
        'review_count': rating_summary['review_count'],
        'sample_review_count': rating_summary['sample_review_count'],
        'already_reviewed': already_reviewed,
    })


@login_required
@require_http_methods(['POST'])
def submit_product_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    rating = request.POST.get('rating', '')
    title = (request.POST.get('title') or '').strip()
    body = (request.POST.get('body') or '').strip()

    try:
        rating_value = int(rating)
    except (TypeError, ValueError):
        rating_value = 0

    if not 1 <= rating_value <= 5:
        messages.error(request, 'Choose a rating from 1 to 5 stars.')
    elif not 3 <= len(title) <= 120:
        messages.error(request, 'Review title must be between 3 and 120 characters.')
    elif not 10 <= len(body) <= 2000:
        messages.error(request, 'Review details must be between 10 and 2,000 characters.')
    elif product.reviews.filter(customer=request.user).exists():
        messages.error(request, 'You have already reviewed this cover.')
    else:
        ProductReview.objects.create(
            product=product,
            customer=request.user,
            rating=rating_value,
            title=title,
            body=body,
        )
        messages.success(request, 'Thank you. Your review has been added.')

    return redirect('product_detail', product_id=product_id)
