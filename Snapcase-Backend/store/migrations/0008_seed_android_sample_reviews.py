from django.db import migrations


SAMPLE_REVIEWS = [
    ('samsung-galaxy-s24-clear-cover', 5, 'Lovely print and fit', 'The floral design looks lovely, and the cover fits the phone model listed.'),
    ('samsung-s24-black-cover', 4, 'Simple and neat', 'A clean-looking cover with a comfortable grip for everyday use.'),
    ('samsung-a55-pink-cover', 5, 'Nice color', 'The pink color is bright and the case feels light on the phone.'),
    ('realme-12-pro-clear-cover', 4, 'Slim clear cover', 'A simple transparent style that keeps the phone design visible.'),
    ('realme-12-pro-floral-cover', 5, 'Cute floral design', 'The floral pattern adds a nice touch while keeping the case practical.'),
    ('realme-narzo-70-heart-cover', 4, 'Sweet design', 'The heart design is fun and the cover is easy to hold.'),
    ('oneplus-12-check-cover', 5, 'Standout pattern', 'The check pattern looks great and makes the phone easy to recognize.'),
    ('oneplus-12-clear-cover', 4, 'Light and minimal', 'A simple lightweight cover for a clean look.'),
]


def add_sample_reviews(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    ProductReview = apps.get_model('store', 'ProductReview')

    for slug, rating, title, body in SAMPLE_REVIEWS:
        product = Product.objects.filter(slug=slug, is_active=True).first()
        if product is None:
            continue
        ProductReview.objects.get_or_create(
            product=product,
            customer=None,
            is_sample=True,
            title=title,
            defaults={
                'rating': rating,
                'body': body,
            },
        )


def remove_sample_reviews(apps, schema_editor):
    ProductReview = apps.get_model('store', 'ProductReview')
    ProductReview.objects.filter(is_sample=True, customer__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_productreview_is_sample_alter_productreview_customer'),
    ]

    operations = [
        migrations.RunPython(add_sample_reviews, remove_sample_reviews),
    ]
