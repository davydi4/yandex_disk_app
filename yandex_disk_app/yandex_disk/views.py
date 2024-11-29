from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
import requests
from .forms import PublicLinkForm
from typing import List, Dict
import zipfile
import io


API_BASE_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"


def index(request):
    """Главная страница с формой для ввода публичной ссылки."""
    if request.method == 'POST':
        form = PublicLinkForm(request.POST)
        if form.is_valid():
            public_link = form.cleaned_data['public_link']
            return redirect('file_list', public_link=public_link)
    else:
        form = PublicLinkForm()
    return render(request, 'disk/index.html', {'form': form})


def filter_files(files: List[Dict], file_type: str) -> List[Dict]:
    """Фильтрация файлов по типу"""
    if file_type == "documents":
        # MIME-типы для документов
        allowed_types = ["application/pdf", "application/msword",
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    elif file_type == "images":
        # MIME-типы для изображений
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
    else:
        return files  # Без фильтрации

    return [file for file in files if file.get('mime_type') in allowed_types]


def file_list(request):
    """Отображение списка файлов по публичной ссылке."""
    public_link = request.GET.get('public_link')
    file_type = request.GET.get('type')  # Получаем тип файла из параметров запроса
    if not public_link:
        return redirect('index')

    params = {'public_key': public_link}
    response = requests.get(API_BASE_URL, params=params)

    if response.status_code == 200:
        files = response.json()['_embedded']['items']
        if file_type:
            files = filter_files(files, file_type)  # Применяем фильтр
        return render(request, 'disk/files.html', {'files': files, 'public_link': public_link})
    else:
        return render(request, 'disk/files.html', {'error': 'Не удалось получить список файлов.'})


def download_file(request, file_path):
    """Загрузка выбранного файла."""
    public_link = request.GET.get('public_link')
    download_url = f"{API_BASE_URL}/download"
    params = {'public_key': public_link, 'path': file_path}

    response = requests.get(download_url, params=params)
    if response.status_code == 200:
        download_link = response.json()['href']
        file_response = requests.get(download_link, stream=True)

        response = HttpResponse(file_response.content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
        return response
    else:
        return HttpResponse('Ошибка загрузки файла.', status=400)


def download_multiple_files(request):
    """Скачивание нескольких файлов архивом."""
    if request.method == 'POST':
        public_link = request.POST.get('public_link')
        selected_files = request.POST.getlist('files')

        if not selected_files:
            return HttpResponse("Не выбрано ни одного файла", status=400)

        # Создание архива
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for file_path in selected_files:
                # Получение ссылки на файл
                download_url = f"{API_BASE_URL}/download"
                params = {'public_key': public_link, 'path': file_path}
                response = requests.get(download_url, params=params)
                if response.status_code == 200:
                    file_download_link = response.json()['href']
                    file_response = requests.get(file_download_link, stream=True)

                    # Добавление файла в архив
                    file_name = file_path.split('/')[-1]
                    zf.writestr(file_name, file_response.content)

        zip_buffer.seek(0)
        response = FileResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="files.zip"'
        return response

    return HttpResponse("Метод не поддерживается", status=405)
