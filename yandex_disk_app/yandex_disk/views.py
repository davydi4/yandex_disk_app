from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.cache import cache
from typing import Optional, List, Dict
import requests

# URL для работы с API Яндекс.Диска
API_BASE_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"


def index(request: HttpRequest) -> HttpResponse:
    """
    Обрабатывает запрос на главную страницу.

    Если метод запроса POST и в теле запроса передан параметр `public_link`,
    происходит перенаправление на страницу списка файлов, используя ссылку.
    В противном случае отображается главная страница.

    Args:
        request (HttpRequest): Входящий HTTP-запрос.

    Returns:
        HttpResponse: Если метод POST и параметр `public_link` указан,
        выполняется перенаправление на `file_list`. В остальных случаях
        возвращается рендер главной страницы.
    """
    if request.method == 'POST':  # Проверка метода запроса
        public_link: Optional[str] = request.POST.get('public_link')  # Получаем параметр `public_link` из запроса
        if public_link:  # Если параметр передан
            # Перенаправляем на страницу списка файлов с использованием обратного URL-резолвера
            return redirect(reverse('yandex_disk:file_list', kwargs={'public_link': public_link}))

    # Если запрос не POST или параметр `public_link` отсутствует, рендерим главную страницу
    return render(request, 'yandex_disk/index.html')


def file_list(request: HttpRequest, public_link: str) -> HttpResponse:
    """
    Отображает список файлов, доступных по публичной ссылке Яндекс.Диска.

    Получает список файлов из API Яндекс.Диска, фильтрует их по типу,
    если параметр `file_type` указан, и сохраняет результат в кэш.

    Args:
        request (HttpRequest): HTTP-запрос.
        public_link (str): Публичная ссылка на ресурс в Яндекс.Диске.

    Returns:
        HttpResponse: Страница со списком файлов или сообщением об ошибке.
    """
    # Получаем тип файла из параметров GET-запроса
    file_type: str = request.GET.get('file_type', '')  # Например, "image", "video", "document"
    cache_key: str = f'files_{public_link}_{file_type}'  # Уникальный ключ для кэша

    # Проверяем, есть ли данные в кэше
    files: Optional[List[Dict]] = cache.get(cache_key)
    if not files:
        # Подготавливаем параметры для API-запроса
        params: Dict[str, str] = {'public_key': public_link}
        response = requests.get(API_BASE_URL, params=params)
        if response.status_code == 200:
            all_files: List[Dict] = response.json().get('_embedded', {}).get('items', [])

            # Если указан тип файла, фильтруем по нему
            if file_type:
                files = [f for f in all_files if f.get('media_type') == file_type]
            else:
                files = all_files

            # Сохраняем отфильтрованные данные в кэш на 5 минут
            cache.set(cache_key, files, timeout=60 * 5)
        else:
            return render(request, 'yandex_disk/files.html', {'error': 'Не удалось получить список файлов.'})

    # Рендерим страницу со списком файлов
    return render(
        request,
        'yandex_disk/files.html',
        {
            'files': files,
            'public_link': public_link,
            'file_type': file_type
        }
    )
