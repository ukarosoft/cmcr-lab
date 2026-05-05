from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('<int:pk>/leida/', views.marcar_leida, name='marcar_leida'),
    path('leidas/todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
