from django.db import migrations


def update_sample_cover_styles(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    updates = {
        'samsung-galaxy-s24-clear-cover': (
            'Samsung Galaxy S24 Floral Cover',
            'Floral print protective cover made for Samsung Galaxy S24.',
        ),
        'samsung-galaxy-a55-cover': (
            'Samsung Galaxy A55 Check Cover',
            'Check-pattern protective cover made for Samsung Galaxy A55.',
        ),
        'realme-12-pro-cover': (
            'Realme 12 Pro Daisy Cover',
            'Daisy print protective cover made for Realme 12 Pro.',
        ),
        'realme-narzo-70-cover': (
            'Realme Narzo 70 Smile Cover',
            'Smiley design protective cover made for Realme Narzo 70.',
        ),
    }
    for slug, (name, description) in updates.items():
        Product.objects.filter(slug=slug).update(name=name, description=description)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_seed_phone_brands'),
    ]

    operations = [
        migrations.RunPython(update_sample_cover_styles, migrations.RunPython.noop),
    ]
