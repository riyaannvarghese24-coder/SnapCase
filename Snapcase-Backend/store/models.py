from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} profile"


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PhoneModel(models.Model):
    brand = models.ForeignKey(Brand, related_name='phone_models', on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('brand', 'name')

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class Product(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, unique=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    phone_model = models.ForeignKey(PhoneModel, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    catalog_image = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='product_reviews',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120)
    body = models.TextField()
    is_sample = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['product', 'customer'], name='unique_customer_product_review'),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='product_review_rating_1_to_5'),
        ]

    def __str__(self):
        reviewer = 'SnapCase sample' if self.is_sample else self.customer
        return f'{self.product.name} review by {reviewer}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    order_number = models.CharField(max_length=30, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=40, choices=PAYMENT_METHOD_CHOICES, default='Cash on Delivery')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_reference = models.CharField(max_length=80, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_id = models.CharField(max_length=32)
    quantity = models.PositiveSmallIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product_id'], name='unique_user_cart_product'),
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='cart_quantity_at_least_one'),
        ]
