import os.path
import time

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render

from app_domainname.constants import menu
from pics_handler.models import Docs, UsersToDocs


def homepage(request):

    # Получаем все записи в UsersToDocs для текущего пользователя
    user_docs = Docs.objects.filter(userstodocs__username=request.user.username)

    text_page = "Это ваши картинки" if user_docs.exists() \
        else "Здесь будут ваши картинки, которые можете загрузить по ссылке Добавить картинку"

    data = {
        'title': 'Главная страница',
        'text_page': text_page,
        'menu': menu,
        'user_docs': user_docs
    }

    return render(request, 'pics_handler/homepage.html', context=data)


@login_required(login_url='/login/')
def upload_file(request):

    if request.method == 'POST' and request.FILES.getlist('files'):

        files = request.FILES.getlist('files')

        for file in files:
            if not file.content_type.startswith('image/'):
                return JsonResponse({'detail': 'Только изображения (jpeg, png, gif)!'}, status=415)

            # **Сохранение файла в media**
            save_file = default_storage.save(file.name, ContentFile(file.read())) # относительный путь
            file_path = default_storage.path(save_file)                           # полный путь

            fastapi_upload_url = settings.BASE_FILE_URL + '/upload_doc'

            # **Отправка файла в другой сервис**
            with open(default_storage.path(save_file), 'rb') as f:
                response = requests.post(
                    fastapi_upload_url,
                    files={"file": (file.name, f, file.content_type)}
                )

            if response.status_code != 200:
                return JsonResponse({'detail': response.json()}, status=response.status_code)

            # **Сохранение в БД**
            doc = Docs.objects.create(file_path=file_path, file_original_name=file.name, size=file.size // 1024)
            UsersToDocs.objects.create(username=request.user.username, docs_id=doc)

        return JsonResponse({'detail': 'Файлы успешно загружены! Перейдите на главную страницу для просмотра'},
                            status=200)

    data = {'title': 'Загрузка картинок', 'text_page': 'Загрузите картинки и смотрите их на главной странице',
            'menu': menu}
    return render(request, 'pics_handler/upload_file.html', context=data)


# @user_passes_test(lambda u: u.is_superuser, login_url='login')
def delete_doc(request):
    is_admin = request.user.is_superuser
    text_page = 'Удалите картинки, вводя их id в форму ниже' if is_admin else "Эта страница доступна только администратору"

    if request.method == 'POST':
        doc_ids_str = request.POST.get('doc_ids', '')

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]

        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # Отправка запросов на FastAPI для удаления каждого документа
        fastapi_delete_url = settings.BASE_FILE_URL + '/doc_delete'

        for doc_id in doc_ids:
            response = requests.delete(f"{fastapi_delete_url}/{doc_id}")

            if response.status_code != 204:
                return JsonResponse({'detail': f"Ошибка при удалении документа с ID {doc_id}: {response.text}"},
                                     status=response.status_code)

            # Удаление записи из базы данных Django
            try:
                doc = Docs.objects.get(id=doc_id)
                # Получаем путь к файлу
                file_path = doc.file_path.path

                # Проверяем, существует ли файл, и удаляем его
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Удаляем запись из базы данных
                doc.delete()

            except Docs.DoesNotExist:
                return JsonResponse({'detail': f"Документ с ID {doc_id} не найден в базе данных."}, status=404)

        return JsonResponse({'detail': 'Документы успешно удалены!'})

    data = {'title': 'Удаление картинок', 'text_page': text_page, 'menu': menu, 'is_admin': is_admin}
    return render(request, 'pics_handler/delete_doc.html', context=data)


@login_required(login_url='/login/')
def doc_analyze(request):

    if request.method == 'POST':

        # получаем список id с фронта
        doc_ids_str = request.POST.get('doc_ids', '')

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]

        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # Отправка запросов на FastAPI для отправки запроса анализа каждого документа на Селери
        fastapi_analyze_url = settings.BASE_FILE_URL + '/doc_analyze'
        fastapi_get_text_url = settings.BASE_FILE_URL + '/get_text'

        for doc_id in doc_ids:
            response_analyze = requests.post(fastapi_analyze_url, json={"id": doc_id})
            if response_analyze.status_code != 200:
                return JsonResponse({'detail': f"Ошибка при попытке проанализировать документ с ID {doc_id}: "
                                               f"{response_analyze.text}"}, status=response_analyze.status_code)

        # Ждем обработки
        time.sleep(3)  # Ожидание 3 секунды перед получением текста

        results = {}

        for doc_id in doc_ids:
            response_get_text = requests.get(f"{fastapi_get_text_url}/{doc_id}")
            text = response_get_text.text if response_get_text.status_code == 200 else "Ошибка загрузки текста"

            # Получаем путь к файлу
            try:
                doc = Docs.objects.get(id=doc_id)
                file_path = doc.file_original_name
            except Docs.DoesNotExist:
                file_path = ""

            results[doc_id] = {"file_path": file_path, "text": text}

        return JsonResponse({'detail': results})

    data = {'title': 'Анализ текста картинки', 'text_page': 'Введите id картинок для анализа текста', 'menu': menu}
    return render(request, 'pics_handler/doc_analyze.html', context=data)


@login_required(login_url='/login/')
def get_text(request):

    if request.method == 'POST':

        # получаем список id с фронта
        doc_ids_str = request.POST.get('doc_ids', '')
        print(f'первый принт {doc_ids_str}')

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]
        print(f'второй принт {doc_ids}')

        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # Отправка запроса на FastAPI для отправки запроса на получение текста каждого документа
        fastapi_get_text_url = settings.BASE_FILE_URL + '/get_text'
        print(f'третий принт {fastapi_get_text_url}')

        results = {}

        for doc_id in doc_ids:
            response_get_text = requests.get(f"{fastapi_get_text_url}/{doc_id}")
            text = response_get_text.text if response_get_text.status_code == 200 else "Ошибка загрузки текста"

            # Получаем путь к файлу
            try:
                doc = Docs.objects.get(id=doc_id)
                file_path = doc.file_original_name
            except Docs.DoesNotExist:
                file_path = ""

            results[doc_id] = {"file_path": file_path, "text": text}

        return JsonResponse({'detail': results})

    data = {'title': 'Получить текст картинки', 'text_page': 'Введите id картинок для получения текста', 'menu': menu}
    return render(request, 'pics_handler/get_text.html', context=data)


def page_not_found(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')