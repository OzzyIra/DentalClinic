# app/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('services/', views.service_list, name='service_list'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('stats/', views.stats_view, name='stats'),
]