from django.urls import path
from . import views

app_name = 'yandex_disk'

urlpatterns = [
    path('', views.index, name='index'),
    path('files/<path:public_link>/', views.file_list, name='file_list'),
    path('files/<path:public_link>/download/<path:file_path>/', views.download_file, name='download_file'),
]
