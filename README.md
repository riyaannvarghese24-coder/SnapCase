# SnapCase

SnapCase is a Django-powered storefront for browsing and ordering phone covers. Customers can filter covers by phone brand, model, and category; manage a cart; place cash-on-delivery orders; and leave product reviews. Staff manage the catalog and orders through a custom dashboard.

## Features

- Responsive storefront with product details, compatibility information, stock status, and customer reviews
- Filters for phone brand, phone model, and cover category
- Customer registration, login, account details, and order history
- Cart actions that update the cart without leaving the current product page
- Checkout with stock validation and cash on delivery
- Staff dashboard for managing products, categories, brands, phone models, orders, payments, and users
- Django admin site for built-in administration
- Password reset pages and email templates

## Tech stack

- Python 3.10+
- Django 5.2
- SQLite
- Django templates, HTML, CSS, and JavaScript

The frontend is served by Django; there is no separate Node.js build step.

## Project structure

```text
Snapcase/
├── Snapcase-Backend/
│   ├── manage.py
│   ├── snapcase/              # Django settings and URL configuration
│   └── store/                 # Models, views, migrations, and tests
├── Snapcase-Frontend/
│   ├── registration/          # Django templates, including password reset pages
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   └── js/
│   └── *.html                 # Storefront, account, cart, and dashboard templates
└── README.md
```

## Run locally

### 1. Create and activate a virtual environment

From the repository root, run in PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -3.10 -m venv .venv
.\.venv\Scripts\activate.bat
```

### 2. Install dependencies

Run this from the repository root with the virtual environment active:

```powershell
python -m pip install --upgrade pip
python -m pip install "Django==5.2.17" "Pillow>=10"
```

Pillow is required for Django's product image fields.

### 3. Apply database migrations

```powershell
cd .\Snapcase-Backend
python manage.py migrate
```

The migrations create the database schema and seed the initial phone brands, models, categories, and sample catalog data.

### 4. Create an administrator

```powershell
python manage.py createsuperuser
```

Use the account you create to sign in to either the Django admin or the custom staff dashboard.

### 5. Start the development server

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

## Main pages

| Page | URL |
| --- | --- |
| Landing page | `/` |
| Storefront | `/home.html` |
| Product details | `/products/<product_id>/` |
| Cart | `/cart.html` |
| Customer login | `/login/` |
| Customer registration | `/Registration.html` |
| Account | `/account/` |
| Order history | `/orders/` |
| Staff dashboard | `/admin-dashboard/` |
| Django admin | `/admin/` |

Staff dashboard pages require a staff or superuser account.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/register/` | Register a customer |
| `POST` | `/api/login/` | Sign in through the JSON API |
| `POST` | `/api/logout/` | Sign out through the JSON API |
| `GET` | `/api/session/` | Read session and cart-count information |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/cart/` | Read, add, update, or remove cart items |

API requests that change data require a valid Django CSRF token. Cart endpoints require an authenticated customer.

## Run tests

From `Snapcase-Backend`:

```powershell
python manage.py test store
```

## Email configuration

Password-reset pages and email templates are included. **Real password-reset email delivery is not configured by default.** Configure Django's email backend, SMTP host, port, credentials, TLS settings, and sender address for your mail provider before relying on password-reset emails. Do not commit mail credentials to the repository; keep secrets in environment variables or a local, untracked environment file.

## Production note

The checked-in Django settings are for local development (`DEBUG = True` and a development fallback secret key). Before deploying, use a strong secret key from the environment, turn off debug mode, configure production `ALLOWED_HOSTS`, HTTPS and secure cookies, email, static/media hosting, and a production database. Do not expose the development configuration to the public internet.
