from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about_view'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('services/', views.service_list, name='service_list'),
    path('nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('reception/', views.reception_dashboard, name='reception_dashboard'),

    # Новые URL для админа
    path('services-management/', views.services_management, name='services_management'),
    path('personnel/', views.personnel_management, name='personnel_management'),
    path('stats-full/', views.stats_full_view, name='stats_full_view'),
    path('documents/', views.documents_view, name='documents_view'),
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('patients-search/', views.patients_search, name='patients_search'),
    path('patient/<int:pk>/', views.patient_detail, name='patient_detail'),

    # API
    path('api/services/', views.api_services_list, name='api_services_list'),
    path('api/services/create/', views.api_service_create, name='api_service_create'),
    path('api/services/<int:pk>/delete/', views.api_service_delete, name='api_service_delete'),
    path('api/services/<int:pk>/update/', views.api_service_update, name='api_service_update'),
    path('api/services/<int:pk>/', views.api_service_detail, name='api_service_detail'),
    path('api/patients/search/', views.api_patients_search, name='api_patients_search'),
    path('api/patients/<int:pk>/update/', views.api_patient_update, name='api_patient_update'),
    path('api/schedule/', views.api_schedule_by_date_and_doctor, name='api_schedule_by_date_and_doctor'),

    # DOCTOR
    path('api/personnel/doctors/', views.api_doctors_list, name='api_doctors_list'),
    path('api/personnel/doctors/create/', views.api_doctor_create, name='api_doctor_create'),
    path('api/personnel/doctors/<int:pk>/update/', views.api_doctor_update, name='api_doctor_update'),
    path('api/personnel/doctors/<int:pk>/delete/', views.api_doctor_delete, name='api_doctor_delete'),
    path('api/personnel/doctors/<int:pk>/', views.api_doctor_detail, name='api_doctor_detail'),

    # NURSE
    path('api/personnel/nurses/', views.api_nurses_list, name='api_nurses_list'),
    path('api/personnel/nurses/create/', views.api_nurse_create, name='api_nurse_create'),
    path('api/personnel/nurses/<int:pk>/update/', views.api_nurse_update, name='api_nurse_update'),
    path('api/personnel/nurses/<int:pk>/delete/', views.api_nurse_delete, name='api_nurse_delete'),
    path('api/personnel/nurses/<int:pk>/', views.api_nurse_detail, name='api_nurse_detail'),

    # RECEPTIONIST
    path('api/personnel/receptionists/', views.api_receptionists_list, name='api_receptionists_list'),
    path('api/personnel/receptionists/create/', views.api_receptionist_create, name='api_receptionist_create'),
    path('api/personnel/receptionists/<int:pk>/update/', views.api_receptionist_update, name='api_receptionist_update'),
    path('api/personnel/receptionists/<int:pk>/delete/', views.api_receptionist_delete, name='api_receptionist_delete'),
    path('api/personnel/receptionists/<int:pk>/', views.api_receptionist_detail, name='api_receptionist_detail'),

    # DOCUMENTS
    path('documents/', views.documents_view, name='documents_view'),
    path('api/documents/create/', views.api_document_create, name='api_document_create'),
    path('api/documents/<int:pk>/update/', views.api_document_update, name='api_document_update'),
    path('api/documents/<int:pk>/delete/', views.api_document_delete, name='api_document_delete'),

    # STATISTICS
    path('api/stats/data/', views.api_stats_data, name='api_stats_data'),
]
