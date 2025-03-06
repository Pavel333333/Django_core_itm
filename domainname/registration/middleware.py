from registration.services import DRFTokenService


class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.token_service = DRFTokenService()

    def __call__(self, request):
        # Пропускаем логин и регистрацию
        if request.path in ['/login/', '/signup/']:
            return self.get_response(request)

        tokens = self.token_service.get_tokens_from_cookies(request)
        access_token = tokens.get("access")
        refresh_token = tokens.get("refresh")

        # Нет refresh_token — перенаправляем на логин
        if not refresh_token:
            return self.token_service.redirect_to_login(request)

        response = self.get_response(request)

        # Проверяем и обновляем до вызова view access, если он истёк
        if not self.token_service.is_access_token_valid(access_token):
            try:
                new_access = self.token_service.refresh_access_token(refresh_token)
                access_token = new_access['access']
            except Exception as e:
                return self.token_service.redirect_to_login(request)

        # Устанавливаем jwt_access_token перед вызовом view
        request.jwt_access_token = access_token

        response = self.get_response(request)

        # Обновляем куки после обработки запроса
        if not self.token_service.is_access_token_valid(
                tokens.get("access")):  # Строка 27: Изменено - проверяем исходный токен
            response.set_cookie(
                'access_token',
                access_token,  # Строка 30: Изменено - используем актуальный токен
                httponly=True,
                samesite='Lax',
                secure=False,
                max_age=60,
                path='/'
            )

        # **Обновляем refresh_token, если близок к истечению**
        if self.token_service.should_update_refresh_token(refresh_token):
            try:
                new_tokens = self.token_service.refresh_token(refresh_token)
                self.update_tokens_in_response(response, new_tokens)
            except Exception as e:
                return self.token_service.redirect_to_login(request)

        return response

    def update_tokens_in_response(self, request, new_tokens):
        response = self.get_response(request)
        response.set_cookie(
            'access_token',
            new_tokens['access'],
            httponly=True,
            samesite='Lax',
            secure=False,  # Для локальной разработки
            max_age=60,    # 1 минута, как в ACCESS_TOKEN_LIFETIME
            path='/'
        )
        if 'refresh' in new_tokens:  # Если DRF вернул новый refresh_token
            response.set_cookie(
                'refresh_token',
                new_tokens['refresh'],
                httponly=True,
                samesite='Lax',
                secure=False,
                max_age=60 * 60 * 24,  # 1 день
                path='/'
            )
        return response