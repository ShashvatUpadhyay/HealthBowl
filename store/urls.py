from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from store import views

urlpatterns = [
    # --- STORE PAGES ---
    path('', views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('product/<int:id>/', views.product_detail, name="product_detail"),

    # --- CART ACTIONS (The JS Engine) ---
    path('update_item/', views.updateItem, name="update_item"),
    
    # (Optional fallback links)
    path('add_cart/<int:product_id>/', views.add_cart, name="add_cart"),
    path('remove_cart/<int:product_id>/', views.remove_cart, name="remove_cart"),
    path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name="remove_cart_item"),

    # --- ORDER & PAYMENT ---
    path('process_order/', views.processOrder, name="process_order"),
    path('payment/', views.payment, name="payment"),
    path('payment_success/', views.payment_success, name="payment_success"),

    # --- USER ACCOUNTS ---
    path('register/', views.registerPage, name="register"),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name="login"),
    path('logout/', auth_views.LogoutView.as_view(next_page='store'), name="logout"),
    path('my_orders/', views.myOrders, name="my_orders"),

    # --- ADMIN DASHBOARD & PRODUCT MANAGEMENT ---
    path('dashboard/', views.dashboard, name="dashboard"),
    path('update_status/<int:order_id>/', views.update_order_status, name="update_order_status"),
    
    # NEW: Create, Update, Delete Paths (Replaces manage_products)
    path('create_product/', views.createProduct, name="create_product"),
    path('update_product/<str:pk>/', views.updateProduct, name="update_product"),
    path('delete_product/<str:pk>/', views.deleteProduct, name="delete_product"),

    # ... your existing urls ...
    
    # Add this new line for the chatbot API:
    path('chat/', views.chat_api, name="chat_api"),
]