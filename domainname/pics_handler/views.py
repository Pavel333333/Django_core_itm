import json
import os.path
import time

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from requests import RequestException

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
    """
    View для транзита файлов на DRF.
    """

    if request.method == 'POST' and request.FILES.getlist('files'):

        files = request.FILES.getlist('files')
        access_token = getattr(request, 'jwt_access_token', None)  # Извлекаем access_token из middleware
        print(f'3 3 3 access_token во view {access_token}')

        if not access_token:
            return JsonResponse({'detail': 'Access token missing'}, status=401)

        for file in files:
            if not file.content_type.startswith('image/'):
                return JsonResponse({'detail': 'Только изображения (jpeg, png, gif)!'}, status=415)

            # Сохранение файла в media
            save_file = default_storage.save(file.name, ContentFile(file.read())) # относительный путь
            file_path = default_storage.path(save_file)                           # полный путь
            drf_transit_url = settings.DRF_API_BASE_URL + '/transit_files/'

            # Отправляем файл в DRF с токеном
            with open(default_storage.path(save_file), 'rb') as f:
                response = requests.post(
                    drf_transit_url,
                    files={"file": (file.name, f, file.content_type)},
                    headers={"Authorization": f"Bearer {access_token}", "Host": settings.DRF_API_HOST}
                )

            if response.status_code != 200:
                return JsonResponse({'detail': response.json()}, status=response.status_code)

            # **Сохранение в БД**
            doc = Docs.objects.create(file_path=file_path, file_original_name=file.name, size=file.size // 1024)
            UsersToDocs.objects.create(username=request.user.username, docs_id=doc)

        return JsonResponse({'detail': 'Файлы успешно загружены! Перейдите на главную страницу для просмотра'},
                            status=200)

    if request.method == 'GET':

        data = {'title': 'Загрузка картинок', 'text_page': 'Загрузите картинки и смотрите их на главной странице',
                'menu': menu}
        return render(request, 'pics_handler/upload_file.html', context=data)


# @user_passes_test(lambda u: u.is_superuser, login_url='login')
def delete_doc(request):
    is_admin = request.user.is_superuser
    text_page = 'Удалите картинки, вводя их id в форму ниже' if is_admin else "Эта страница доступна только администратору"

    if request.method == 'POST':
        doc_ids_str = request.POST.get('doc_ids', '')
        access_token = getattr(request, 'jwt_access_token', None)  # Извлекаем access_token из middleware

        if not access_token:
            return JsonResponse({'detail': 'Access token missing'}, status=401)

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]

        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # Отправка запроса на FastAPI для удаления каждого документа через DRF
        drf_delete_url = settings.DRF_API_BASE_URL + '/transit_delete/'

        response = requests.post(
            drf_delete_url,
            data={"doc_ids": json.dumps(doc_ids)},  # Отправляем список как JSON
            headers={"Authorization": f"Bearer {access_token}", "Host": settings.DRF_API_HOST}
        )

        if response.status_code not in [200, 207]:  # Обрабатываем 200 и 207
            return JsonResponse({'detail': f"Ошибка при удалении: {response.text}"}, status=response.status_code)

        # Получаем подтверждённые удалённые id от DRF
        result = response.json()
        deleted_ids = result.get("deleted_ids", [])

        # Удаляем только подтверждённые id в Django
        for doc_id in deleted_ids:
            try:
                doc = Docs.objects.get(id=doc_id)
                file_path = doc.file_path.path  # получаем путь к файлу

                if os.path.exists(file_path):  # Проверяем, существует ли файл
                    os.remove(file_path)  # удаляем файл

                doc.delete()
            except Docs.DoesNotExist:
                pass  # Игнорируем, если запись уже удалена


        if response.status_code == 207:
            return JsonResponse({
                'detail': 'Частичное удаление',
                'deleted_ids': deleted_ids,
                'failed_ids': result.get("failed_ids", [])
            }, status=207)
        return JsonResponse({'detail': 'Документы успешно удалены!'})

    if request.method == 'GET':

        data = {'title': 'Удаление картинок', 'text_page': text_page, 'menu': menu, 'is_admin': is_admin}
        return render(request, 'pics_handler/delete_doc.html', context=data)


@login_required(login_url='/login/')
def doc_analyze(request):
    """
    View для запуска анализа текста через DRF/FastAPI и возврата результатов на фронт.
    Отправляет список id на /transit_analyze/ и получает текст через агрегированный ответ.
    """
    if request.method == 'POST':
        # получаем список id с фронта
        doc_ids_str = request.POST.get('doc_ids', '')
        access_token = getattr(request, 'jwt_access_token', None)  # Извлекаем access_token из middleware

        if not access_token:
            return JsonResponse({'detail': 'Access token missing'}, status=401)

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]
        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # URL для запуска анализа через DRF
        drf_analyze_url = settings.DRF_API_BASE_URL + '/transit_analyze/'

        try:
            # Отправляем список id одним запросом
            response = requests.post(
                drf_analyze_url,
                json={"doc_ids": doc_ids},    # data={"doc_ids": json.dumps(doc_ids)},  # Список как JSON
                headers={"Authorization": f"Bearer {access_token}", "Host": settings.DRF_API_HOST},
                timeout=30)  # Таймаут 5 секунд
            response.raise_for_status()  # Вызовет исключение, если статус не 2xx
        except RequestException as e:
            return JsonResponse({"error": "Не удалось обработать запрос"}, status=500)

        # Обрабатываем ответ от DRF
        if response.status_code not in [200, 207]:
            return JsonResponse({'detail': f"Ошибка при анализе: {response.text}"}, status=response.status_code)

        # Получаем результаты анализа
        result = response.json()
        analyzed_texts = result.get("analyzed_texts", {})
        failed_ids = result.get("failed_ids", [])

        # Формируем ответ для фронта
        results = {}
        for doc_id in doc_ids:
            doc_id_str = str(doc_id)  # DRF вернёт ключи как строки из JSON
            if doc_id_str in analyzed_texts:
                text = analyzed_texts[doc_id_str]
            else:
                text = failed_ids.get(doc_id_str, {}).get("error", "Ошибка загрузки текста")

            # Получаем путь к файлу
            try:
                doc = Docs.objects.get(id=doc_id)
                file_path = doc.file_original_name
            except Docs.DoesNotExist:
                file_path = ""

            results[doc_id] = {"file_path": file_path, "text": text}

        # Возвращаем результат
        if failed_ids:
            return JsonResponse({'detail': 'Частичный анализ', 'results': results, 'failed_ids': failed_ids},
                                status=207)
        return JsonResponse({'detail': results})

    if request.method == 'GET':
        data = {'title': 'Анализ текста картинки', 'text_page': 'Введите id картинок для анализа текста', 'menu': menu}
        return render(request, 'pics_handler/doc_analyze.html', context=data)


@login_required(login_url='/login/')
def get_text(request):
    """
    View для получения текста из базы FastAPI через DRF и возврата на фронт.
    Отправляет список id на /transit_get_text/ для получения текста.
    """
    if request.method == 'POST':
        # Получаем список id с фронта
        doc_ids_str = request.POST.get('doc_ids', '')
        access_token = getattr(request, 'jwt_access_token', None)

        if not access_token:
            return JsonResponse({'detail': 'Access token missing'}, status=401)

        # Разделяем строку на ID и проверяем на валидность
        doc_ids = [int(doc_id.strip()) for doc_id in doc_ids_str.split(',') if doc_id.strip().isdigit()]
        if not doc_ids:
            return JsonResponse({'detail': "Ошибка: Не были переданы корректные ID документов."}, status=400)

        # URL для получения текста через DRF
        drf_get_text_url = f"{settings.DRF_API_BASE_URL}/transit_get_text/"

        # Отправляем список id одним запросом
        response = requests.post(
            drf_get_text_url,
            data={"doc_ids": json.dumps(doc_ids)},  # Список как JSON
            headers={"Authorization": f"Bearer {access_token}", "Host": settings.DRF_API_HOST}
        )

        # Обрабатываем ответ от DRF
        if response.status_code not in [200, 207]:
            return JsonResponse({'detail': f"Ошибка при получении текста: {response.text}"}, status=response.status_code)

        # Получаем результаты
        result = response.json()
        retrieved_texts = result.get("retrieved_texts", {})
        failed_ids = result.get("failed_ids", [])
        from_cache = result.get("from_cache", False)  # Словарь {doc_id: boolean} из DRF

        # Формируем ответ для фронта
        results = {}
        for doc_id in doc_ids:
            doc_id_str = str(doc_id)  # DRF вернёт ключи как строки из JSON
            if doc_id_str in retrieved_texts:
                text = retrieved_texts[doc_id_str]
            else:
                text = failed_ids.get(doc_id_str, {}).get("error", "Ошибка загрузки текста")

            # Получаем путь к файлу
            try:
                doc = Docs.objects.get(id=doc_id)
                file_path = doc.file_original_name
            except Docs.DoesNotExist:
                file_path = ""

            results[doc_id] = {"file_path": file_path, "text": text, "from_cache": from_cache.get(doc_id_str, False)}

        # Возвращаем результат
        if failed_ids:
            return JsonResponse({'detail': 'Частичное получение текста', 'results': results, 'failed_ids': failed_ids}, status=207)
        return JsonResponse({'detail': results})

    if request.method == 'GET':
        data = {'title': 'Получить текст картинки', 'text_page': 'Введите id картинок для получения текста', 'menu': menu}
        return render(request, 'pics_handler/get_text.html', context=data)


def page_not_found(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')