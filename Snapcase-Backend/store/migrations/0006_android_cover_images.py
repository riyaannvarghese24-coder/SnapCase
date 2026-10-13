from django.db import migrations


def add_android_cover_images(apps, schema_editor):
    Brand = apps.get_model('store', 'Brand')
    Category = apps.get_model('store', 'Category')
    PhoneModel = apps.get_model('store', 'PhoneModel')
    Product = apps.get_model('store', 'Product')

    catalog_image_by_slug = {
        'black-shock-case': 'black-case.jpg',
        'daisy-vibes-case': 'daisy-case.jpg',
        'pastel-waves-case': 'pastel-case.jpg',
        'plain-pink-case': 'plain-pink.jpg',
        'samsung-galaxy-s24-clear-cover': 'floral-case.jpg',
        'samsung-galaxy-a55-cover': 'check-case.jpg',
        'realme-12-pro-cover': 'daisy-case.jpg',
        'realme-narzo-70-cover': 'smile-case.jpg',
    }
    for slug, filename in catalog_image_by_slug.items():
        Product.objects.filter(slug=slug).update(catalog_image=filename)

    covers, _ = Category.objects.get_or_create(
        name='Phone Covers',
        defaults={'description': 'Phone covers in a range of colors and designs.'},
    )
    new_covers = [
        ('samsung-s24-black-cover', 'Samsung Galaxy S24 Black Cover', 'Samsung', 'Galaxy S24', 'plain-black.jpg', 'Classic black protective cover made for Samsung Galaxy S24.', '479.00', 14),
        ('samsung-s24-white-cover', 'Samsung Galaxy S24 White Cover', 'Samsung', 'Galaxy S24', 'plain-white.jpg', 'Clean white protective cover made for Samsung Galaxy S24.', '479.00', 11),
        ('samsung-a55-pink-cover', 'Samsung Galaxy A55 Pink Cover', 'Samsung', 'Galaxy A55', 'plain-pink.jpg', 'Soft pink protective cover made for Samsung Galaxy A55.', '499.00', 13),
        ('samsung-a55-yellow-cover', 'Samsung Galaxy A55 Yellow Cover', 'Samsung', 'Galaxy A55', 'plain-yellow.jpg', 'Bright yellow protective cover made for Samsung Galaxy A55.', '499.00', 9),
        ('realme-12-pro-clear-cover', 'Realme 12 Pro Clear Cover', 'Realme', 'Realme 12 Pro', 'plain-clear.jpg', 'Minimal transparent cover made for Realme 12 Pro.', '429.00', 20),
        ('realme-12-pro-floral-cover', 'Realme 12 Pro Floral Cover', 'Realme', 'Realme 12 Pro', 'floral-case.jpg', 'Floral print protective cover made for Realme 12 Pro.', '529.00', 8),
        ('realme-narzo-70-heart-cover', 'Realme Narzo 70 Heart Cover', 'Realme', 'Realme Narzo 70', 'heart-case.jpg', 'Heart design protective cover made for Realme Narzo 70.', '479.00', 10),
        ('realme-narzo-70-white-cover', 'Realme Narzo 70 White Cover', 'Realme', 'Realme Narzo 70', 'plain-white.jpg', 'Classic white protective cover made for Realme Narzo 70.', '429.00', 16),
        ('oneplus-12-check-cover', 'OnePlus 12 Check Cover', 'OnePlus', 'OnePlus 12', 'check-case.jpg', 'Check-pattern protective cover made for OnePlus 12.', '499.00', 7),
        ('oneplus-12-clear-cover', 'OnePlus 12 Clear Cover', 'OnePlus', 'OnePlus 12', 'plain-clear.jpg', 'Minimal transparent cover made for OnePlus 12.', '449.00', 12),
    ]

    for slug, name, brand_name, model_name, image, description, price, stock in new_covers:
        brand, _ = Brand.objects.get_or_create(name=brand_name)
        phone_model, _ = PhoneModel.objects.get_or_create(brand=brand, name=model_name)
        Product.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'category': covers,
                'brand': brand,
                'phone_model': phone_model,
                'description': description,
                'price': price,
                'stock': stock,
                'catalog_image': image,
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_product_catalog_image_productreview'),
    ]

    operations = [
        migrations.RunPython(add_android_cover_images, migrations.RunPython.noop),
    ]
