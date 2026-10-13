from django.db import migrations


def add_common_phone_brands(apps, schema_editor):
    Brand = apps.get_model('store', 'Brand')
    Category = apps.get_model('store', 'Category')
    Product = apps.get_model('store', 'Product')
    PhoneModel = apps.get_model('store', 'PhoneModel')

    models_by_brand = {
        'Samsung': ['Galaxy S24', 'Galaxy A55'],
        'Realme': ['Realme 12 Pro', 'Realme Narzo 70'],
    }

    for brand_name, model_names in models_by_brand.items():
        brand, _ = Brand.objects.get_or_create(name=brand_name)
        for model_name in model_names:
            PhoneModel.objects.get_or_create(brand=brand, name=model_name)

    category, _ = Category.objects.get_or_create(
        name='Phone Covers',
        defaults={'description': 'Protective phone covers for popular devices.'},
    )
    compatible_products = [
        ('samsung-galaxy-s24-clear-cover', 'Samsung Galaxy S24 Clear Cover', 'Samsung', 'Galaxy S24', 'Clear protective cover for Samsung Galaxy S24.', '549.00', 18),
        ('samsung-galaxy-a55-cover', 'Samsung Galaxy A55 Cover', 'Samsung', 'Galaxy A55', 'Everyday protective cover for Samsung Galaxy A55.', '499.00', 15),
        ('realme-12-pro-cover', 'Realme 12 Pro Cover', 'Realme', 'Realme 12 Pro', 'Slim protective cover made for Realme 12 Pro.', '499.00', 16),
        ('realme-narzo-70-cover', 'Realme Narzo 70 Cover', 'Realme', 'Realme Narzo 70', 'Flexible protective cover made for Realme Narzo 70.', '449.00', 12),
    ]
    for slug, name, brand_name, model_name, description, price, stock in compatible_products:
        brand = Brand.objects.get(name=brand_name)
        phone_model = PhoneModel.objects.get(brand=brand, name=model_name)
        Product.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'category': category,
                'brand': brand,
                'phone_model': phone_model,
                'description': description,
                'price': price,
                'stock': stock,
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_brand_category_alter_customerprofile_address_and_more'),
    ]

    operations = [
        migrations.RunPython(add_common_phone_brands, migrations.RunPython.noop),
    ]
