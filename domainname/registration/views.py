from django.contrib.auth import logout, login
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect

from app_domainname.constants import menu, restricted_urls


def login_view(request):

    form = AuthenticationForm()
    data = {'form': form, 'title': 'Вход', 'menu': menu}
    next_url = request.GET.get('next', 'homepage')  # Если next не указан, переводим на главную страницу

    if request.user.is_authenticated:

        # Проверяем, имеет ли он доступ к next_url
        if next_url in restricted_urls and not request.user.is_superuser:
            return redirect("homepage")  # Перенаправляем на главную

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

            return redirect(next_url)  # Перенаправляем на страницу, откуда пришел пользователь

    return render(request, 'registration/login.html', context=data)


def signup(request):

    if request.user.is_authenticated:
        return render(request, 'registration/already_authenticated.html',
                      context={'title': 'Вы уже зарегистрированы', 'menu': menu})

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user: AbstractBaseUser = form.save()
            login(request, user)  # Автоматический вход
            return redirect("/")  # Перенаправление после регистрации
    else:
        form = UserCreationForm()

    data = {'form': form, 'menu': menu}

    return render(request, "registration/signup.html", context=data)

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("/login")  # Перенаправление после разлогинивания
    return render(request, 'registration/logout.html', context={'title': 'Вы не авторизованы', 'menu': menu})


