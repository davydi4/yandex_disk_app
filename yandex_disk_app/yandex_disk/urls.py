from django.urls import path
from . import views

app_name = 'yandex_disk'

urlpatterns = [
    path('', views.index, name='index'),
    path('files/<path:public_link>/', views.file_list, name='file_list'),
]
