from django.contrib.auth.views import LogoutView
from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),     # http://127.0.0.1:8000/login/
    path('logout/', views.logout_view, name='logout'),  # http://127.0.0.1:8000/logout/
    path('signup/', views.signup, name='signup'),       # http://127.0.0.1:8000/signup/
    path('', include('django.contrib.auth.urls')),      # Подключаем встроенные маршруты
]