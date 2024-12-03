from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.core.cache import cache
import requests

API_BASE_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"


def index(request):
    if request.method == 'POST':
        public_link = request.POST.get('public_link')
        if public_link:
            return redirect(reverse('yandex_disk:file_list', kwargs={'public_link': public_link}))
    return render(request, 'yandex_disk/index.html')


def file_list(request, public_link):
    # Получаем тип файла из параметров GET-запроса
    file_type = request.GET.get('file_type', '')  # Например, "image", "video", "document"
    cache_key = f'files_{public_link}_{file_type}'  # Уникальный ключ для кэша

    # Проверяем наличие данных в кэше
    files = cache.get(cache_key)
    if not files:
        # Запрашиваем данные через API Яндекс.Диска
        params = {'public_key': public_link}
        response = requests.get(API_BASE_URL, params=params)
        if response.status_code == 200:
            all_files = response.json().get('_embedded', {}).get('items', [])

            # Фильтруем файлы по типу
            if file_type:
                files = [f for f in all_files if f.get('media_type') == file_type]
            else:
                files = all_files

            # Сохраняем данные в кэш на 5 минут
            cache.set(cache_key, files, timeout=60 * 5)
        else:
            return render(request, 'yandex_disk/files.html', {'error': 'Не удалось получить список файлов.'})

    return render(request, 'yandex_disk/files.html',
                  {'files': files, 'public_link': public_link, 'file_type': file_type})


def download_file(request, public_link, file_path):
    """
    Функция для скачивания конкретного файла по его пути.
    """
    download_url = f"{API_BASE_URL}/download"
    params = {'public_key': public_link, 'path': file_path}
    response = requests.get(download_url, params=params)
    if response.status_code == 200:
        download_link = response.json()['href']
        file_content = requests.get(download_link).content
        file_name = file_path.split('/')[-1]
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    else:
        return HttpResponse('Ошибка при скачивании файла', status=500)
