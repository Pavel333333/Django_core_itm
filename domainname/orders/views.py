from django.shortcuts import render

from app_domainname.constants import menu


def order_analyze_pic(request):
    data = {'title': 'Заказ анализа картинки', 'text_page': 'Здесь будет страница с заказом анализа картинок', 'menu': menu}
    return render(request, 'orders/order_analyze_pic.html', context=data)

def orders_payments(request):
    data = {'title': 'Оплата заказа', 'text_page': 'Здесь будет страница с оплатой заказов', 'menu': menu}
    return render(request, 'orders/orders_payments.html', context=data)
