"""
URL configuration for Print project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main.views import *
from django.conf import settings
from django.conf.urls.static import static 
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('' , home , name="home"),
    path('login/' , login_page , name="login"),
    path('register/' , register_page , name="register"),
    path('main/' , main , name = "main"),
    path('logout/' , logout_page , name="logout"),
    path('products/', product_list, name='product_list'),
    path('cart/', view_cart, name='cart'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('update-quantity/', update_quantity, name='update_quantity'),
    path('remove-from-cart/', remove_from_cart, name='remove_from_cart'),
    path('admin/login/', admin_login, name='admin_login'),
    path('admin/logout/', admin_logout, name='admin_logout'),
    path('create-admin/', create_admin_account, name='create_admin_account'),
    path('orders/cancel/', cancel_order, name='cancel_order'),
    path('admin/login/', admin_login, name='admin_login'),
    path('admin/logout/', admin_logout, name='admin_logout'),
    path('orders/', order_list, name='order_list'),
    path('create-order/', create_order, name='create_order'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/order-details/<int:order_id>/', get_order_details, name='get_order_details'),
    path('admin/update-order-status/', update_order_status, name='update_order_status'),
    path('admin/order/<int:order_id>/', order_detail_view, name='order_detail'),
    path('split-payment/', split_payment, name='split_payment'),
    path('smart-navigation/<int:order_id>/', smart_navigation, name='smart_navigation'),
    path('admin/dashboard/vendor/dashboard/', vendor_dashboard, name='vendor_dashboard'),
    path('vendor/create-event/', create_event, name='create_event'),
    path('vendor/register/', vendor_registration, name='vendor_registration'),
    path('buy_vibies/', buy_vibies, name='buy_vibies'),
    path('select-seats/<int:event_id>/', select_seats, name='select_seats'),
    
    
    
   
    
    
    


    path('admin/', admin.site.urls),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)