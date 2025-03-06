from django.contrib.auth import logout, login
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect

from app_domainname.constants import menu, restricted_urls
from registration.services import DRFTokenService


def login_view(request):
    """
    Представление для входа пользователя.
    После успешной авторизации получает JWT-токены от DRF-сервиса.
    """
    form = AuthenticationForm()
    data = {'form': form, 'title': 'Вход', 'menu': menu}
    next_url = request.GET.get('next', 'homepage')  # Если next не указан, переводим на главную страницу

    if request.user.is_authenticated:

        # Проверяем, имеет ли он доступ к next_url
        if next_url in restricted_urls and not request.user.is_superuser:
            return redirect("homepage")  # Перенаправляем на главную, если доступ запрещен

        # Если пользователь авторизован, показываем сообщение и не показываем форму
        return render(request, 'registration/already_authenticated.html',
                      context={'title': 'Вы уже авторизованы', 'menu': menu})
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Авторизация пользователя
            if next_url in restricted_urls and not request.user.is_superuser:
                return redirect("homepage")  # Если доступ запрещён — кидаем на главную

            # Получаем JWT-токены от DRF-сервиса
            token_service = DRFTokenService()
            try:
                tokens = token_service.obtain_token(request.POST['username'], request.POST['password'])
                # Создаем response на основе рендера HTML-страницы
                response = render(request,'registration/already_authenticated.html',
                                  context={'title': 'Вы авторизованы', 'menu': menu})
                response.set_cookie('access_token', tokens['access'], httponly=True, samesite='Lax', secure=False,
                                    max_age=60, path='/')
                response.set_cookie('refresh_token', tokens['refresh'], httponly=True, samesite='Lax', secure=False,
                                    max_age=60 * 60 * 24, path='/')
                return response  # Возвращаем ответ с cookies
            except Exception as e:
                logout(request)  # Если запрос к DRF неудачен, разлогиниваем пользователя
                return JsonResponse({"error": str(e)}, status=500)

        else:
            return render(request, 'registration/login.html', context=data)

    return render(request, 'registration/login.html', context=data)


def signup(request):
    """
    Представление для регистрации пользователя.
    После регистрации получает JWT-токены от DRF-сервиса.
    """
    if request.user.is_authenticated:
        return render(request, 'registration/already_authenticated.html',
                      context={'title': 'Вы уже зарегистрированы', 'menu': menu})
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user: AbstractBaseUser = form.save()  # Создаем нового пользователя
            login(request, user)  # Автоматический вход

            # Получаем пароль из формы (используем password1)
            raw_password = form.cleaned_data.get('password1')

            # Получаем JWT-токены от DRF-сервиса
            token_service = DRFTokenService()
            try:
                tokens = token_service.obtain_token(user.username, raw_password)
                # Создаем редирект с cookies
                next_url = request.GET.get('next', '/')  # Получаем URL для редиректа
                response = HttpResponseRedirect(next_url)  # Создаем редирект
                response.set_cookie('access_token', tokens['access'], httponly=True, samesite='Lax')
                response.set_cookie('refresh_token', tokens['refresh'], httponly=True, samesite='Lax')
                redirect("/")  # Перенаправление после регистрации
                return render(request, 'registration/already_authenticated.html',
                              context={'title': 'Вы зарегистрированы', 'menu': menu})
                # return response  # Возвращаем ответ с cookies
            except Exception as e:
                logout(request)  # Если запрос к DRF неудачен, разлогиниваем пользователя
                return JsonResponse({"error": str(e)}, status=500)
    else:
        form = UserCreationForm()

    data = {'form': form, 'menu': menu}

    return render(request, "registration/signup.html", context=data)

def logout_view(request):
    """
    Представление для выхода пользователя.
    Удаляет JWT-токены из сессии.
    """
    if request.method == "POST":
        logout(request)  # Стандартный выход Django
        request.session.flush()  # Полная очистка сессии
        return redirect("/login")  # Перенаправление после разлогинивания

    return render(request, 'registration/logout.html', context={'title': 'Вы не авторизованы', 'menu': menu})