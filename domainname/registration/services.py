import jwt
import time
import requests
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect


class DRFTokenService:
    """
    Сервис для взаимодействия с DRF-сервисом для получения и обновления JWT-токенов.
    """

    def __init__(self):
        self.base_url = settings.DRF_API_BASE_URL  # URL DRF-сервиса
        self.host = settings.DRF_API_HOST

    def get_tokens_from_cookies(self, request):
        """
        Извлекает токены из куков.
        :param request: Объект запроса.
        :return: Словарь с токенами или None, если токены отсутствуют.
        """

        return {
            "access": request.COOKIES.get('access_token'),
            "refresh": request.COOKIES.get('refresh_token')
        }

    def is_access_token_valid(self, access_token):
        """
        Проверяет срок действия access-токена.
        :param access_token: Токен для проверки.
        :return: True, если токен действителен, иначе False.
        """
        if not access_token:
            return False
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_signature": False})
            return time.time() < payload.get("exp", 0)
        except Exception:
            return False

    def should_update_refresh_token(self, refresh_token):
        if not refresh_token:
            return False
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_signature": False})
            return (payload.get("exp", 0) - time.time()) < 3600  # Меньше часа
        except Exception:
            return False

    def obtain_token(self, username, password):
        """
        Получение пары токенов (access и refresh) от DRF-сервиса.
        :param username: Логин пользователя.
        :param password: Пароль пользователя.
        :return: Словарь с токенами {'access': ..., 'refresh': ...}.
        """
        url = f"{self.base_url}/token/"
        data = {"username": username, "password": password}
        # response = requests.post(url, json=data)
        # [Добавленная строка] Указываем Host явно
        response = requests.post(url, json=data, headers={"Content-Type": "application/json", "Host": self.host})
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to obtain token: {response.text}")

    def refresh_access_token(self, refresh_token):
        url = f"{self.base_url}/token/refresh/"
        data = {"refresh": refresh_token}  # Без update_lifetime
        response = requests.post(url, json=data, headers={"Content-Type": "application/json", "Host": self.host})
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to refresh access token: {response.text}")

    def refresh_token(self, refresh_token, update_lifetime=False):
        """
        Обновление access-токена через DRF-сервис.
        :param refresh_token: Refresh-токен.
        :return: Словарь с новым access-токеном {'access': ...}.
        """
        url = f"{self.base_url}/token/refresh/"
        data = {"refresh": refresh_token, "update_lifetime": True}
        response = requests.post(url, json=data, headers={"Content-Type": "application/json", "Host": self.host})
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to refresh token: {response.text}")

    def logout_user(self, request, get_response):
        """
        Разлогинивает пользователя и удаляет cookies.
        Передает управление дальше по цепочке middleware.
        :param request: Объект запроса Django.
        :param get_response: Функция для получения следующего response.
        :return: Response из следующего middleware/view.
        """
        # Разлогиниваем пользователя
        logout(request)
        print("Пользователь разлогинен в services")

        # Создаем response для удаления cookies
        response = get_response(request)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response

    def redirect_to_login(self, request):
        """Перенаправляет на страницу логина без изменения текущего response"""
        next_url = request.get_full_path()
        # return redirect(f'/login/?next={next_url}')
        logout(request)

        return redirect(f'/login/')