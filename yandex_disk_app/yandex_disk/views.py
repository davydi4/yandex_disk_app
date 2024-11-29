from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
import requests
from .forms import PublicLinkForm


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


def file_list(request):
    """Отображение списка файлов по публичной ссылке."""
    public_link = request.GET.get('public_link')
    if not public_link:
        return redirect('index')

    params = {'public_key': public_link}
    response = requests.get(API_BASE_URL, params=params)

    if response.status_code == 200:
        files = response.json()['_embedded']['items']
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
