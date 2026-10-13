from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from django.views.generic import TemplateView

from store import views

auth_urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(
            success_url=reverse_lazy('auth:password_change_done'),
        ),
        name='password_change',
    ),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            success_url=reverse_lazy('auth:password_reset_done'),
        ),
        name='password_reset',
    ),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            success_url=reverse_lazy('auth:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

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
    path('wishlist/', views.frontend_page, {'template_name': 'wishlist.html'}, name='wishlist'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/products/', views.product_management, name='admin_products'),
    path('admin-dashboard/categories/', views.category_management, name='admin_categories'),
    path('admin-dashboard/brands/', views.brand_management, name='admin_brands'),
    path('admin-dashboard/phone-models/', views.phone_model_management, name='admin_phone_models'),
    path('admin-dashboard/orders/', views.order_management, name='admin_orders'),
    path('admin-dashboard/payments/', views.payment_management, name='admin_payments'),
    path('admin-dashboard/users/', views.user_management, name='admin_users'),
    path('accounts/', include((auth_urlpatterns, 'auth'), namespace='auth')),
    path('api/register/', views.register, name='api-register'),
    path('api/login/', views.login_view, name='api-login'),
    path('api/logout/', views.logout_view, name='api-logout'),
    path('api/session/', views.session_view, name='api-session'),
    path('api/cart/', views.cart_view, name='api-cart'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
