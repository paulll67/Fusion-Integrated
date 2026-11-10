from django.urls import path, include
from .views import *

app_name = 'leave'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_leave, name='create_leave'),
    path('<int:pk>/', views.leave_detail, name='leave_detail'),
]
