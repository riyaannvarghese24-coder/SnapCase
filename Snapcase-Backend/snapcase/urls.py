from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('home.html', views.customer_home, name='customer_home'),
    path('home/', views.customer_home, name='home'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/reviews/', views.submit_product_review, name='submit_product_review'),
    path('account/', views.customer_account, name='customer_account'),
    path('orders/', views.customer_orders, name='customer_orders'),
    path('orders/<int:order_id>/', views.customer_order_detail, name='customer_order_detail'),
    path('checkout/', views.place_order, name='place_order'),
    path('login.html', views.frontend_page, {'template_name': 'login.html'}, name='login_template'),
    path('login/', views.common_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('Registration.html', views.frontend_page, {'template_name': 'Registration.html'}, name='registration'),
    path('cart.html', views.frontend_page, {'template_name': 'cart.html'}, name='cart'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/products/', views.product_management, name='admin_products'),
    path('admin-dashboard/categories/', views.category_management, name='admin_categories'),
    path('admin-dashboard/brands/', views.brand_management, name='admin_brands'),
    path('admin-dashboard/phone-models/', views.phone_model_management, name='admin_phone_models'),
    path('admin-dashboard/orders/', views.order_management, name='admin_orders'),
    path('admin-dashboard/payments/', views.payment_management, name='admin_payments'),
    path('admin-dashboard/users/', views.user_management, name='admin_users'),
    path('accounts/', include(('django.contrib.auth.urls', 'auth'), namespace='auth')),
    path('api/register/', views.register, name='api-register'),
    path('api/login/', views.login_view, name='api-login'),
    path('api/logout/', views.logout_view, name='api-logout'),
    path('api/session/', views.session_view, name='api-session'),
    path('api/cart/', views.cart_view, name='api-cart'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
