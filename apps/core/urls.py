from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('healthz/', views.healthz, name='healthz'),
    path('', views.dashboard_view, name='dashboard'),
    path('cuenta-suspendida/', views.cuenta_suspendida_view, name='cuenta_suspendida'),
]
