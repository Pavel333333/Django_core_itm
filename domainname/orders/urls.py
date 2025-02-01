from django.urls import path
from . import views

urlpatterns = [
    path('order_analyze_pic/', views.order_analyze_pic, name='order_analyze_pic'), # http://127.0.0.1:8000/categories/order_analyze_pic/
    path('orders_payments/', views.orders_payments, name='orders_payments'),       # http://127.0.0.1:8000/categories/orders_payments/
]