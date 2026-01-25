from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient, Service, Appointment, Doctor
from django.db.models import Count
from datetime import date


# Проверка ролей
def is_admin(user):
    return user.is_staff and user.role == 'admin'


def is_nurse(user):
    return user.role == 'nurse'


def is_receptionist(user):
    return user.role == 'receptionist'


def is_doctor(user):
    return user.role == 'doctor'


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Редирект в зависимости от роли
            if is_admin(user):
                return redirect('admin_dashboard')
            elif is_nurse(user):
                return redirect('nurse_dashboard')  # пока заглушка
            elif is_receptionist(user):
                return redirect('reception_dashboard')  # пока заглушка
            elif is_doctor(user):
                return redirect('doctor_dashboard')  # добавили для врача
            else:
                return redirect('admin_dashboard')  # по умолчанию
        else:
            messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'login.html')


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    today = date.today()
    appointments = Appointment.objects.filter(date_time__date=today).select_related('patient', 'doctor', 'doctor__user')
    scheduled = appointments.filter(status='scheduled')
    completed = appointments.filter(status='completed')
    context = {
        'scheduled': scheduled,
        'completed': completed,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def doctor_dashboard(request):
    if not is_doctor(request.user):
        return redirect('access_denied')
    # Пример: получить записи, назначенные этому врачу на сегодня
    doctor_instance = Doctor.objects.get(user=request.user)
    today = date.today()
    appointments = Appointment.objects.filter(doctor=doctor_instance, date_time__date=today)
    context = {
        'appointments': appointments,
    }
    return render(request, 'doctor_dashboard.html', context)


def access_denied(request):
    return render(request, '403.html')


@login_required
def patient_list(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    patients = Patient.objects.all()
    return render(request, 'patient_list.html', {'patients': patients})


@login_required
def service_list(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    services = Service.objects.all()
    return render(request, 'service_list.html', {'services': services})


@login_required
def schedule_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    doctors = Doctor.objects.filter(is_active=True)
    appointments = Appointment.objects.select_related('patient', 'doctor').filter(
        date_time__date=date.today()
    )
    return render(request, 'schedule.html', {
        'doctors': doctors,
        'appointments': appointments
    })


@login_required
def stats_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    # Пример простой статистики
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()
    completed_count = Appointment.objects.filter(status='completed').count()
    doctors_stats = Doctor.objects.annotate(appointments_count=Count('appointment'))

    context = {
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'completed_count': completed_count,
        'doctors_stats': doctors_stats,
    }
    return render(request, 'stats.html', context)
