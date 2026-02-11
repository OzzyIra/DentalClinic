from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Patient, Service, Appointment, Doctor, Nurse, Receptionist, User, ClinicInfo, Document, \
    InvoiceService
from datetime import datetime, timedelta
from django.db.models import Count, Sum, F
from django.utils import timezone
import json
from django.db.models.functions import TruncMonth


# Проверка ролей
def is_admin(user):
    return user.role == 'admin'


def is_nurse(user):
    return user.role == 'nurse'


def is_receptionist(user):
    return user.role == 'receptionist'


def is_doctor(user):
    return user.role == 'doctor'


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        elif is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_doctor(request.user):
            return redirect('doctor_dashboard')
        elif is_receptionist(request.user):
            return redirect('reception_dashboard')
        elif is_nurse(request.user):
            return redirect('nurse_dashboard')
        else:
            return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if is_admin(user):
                return redirect('admin_dashboard')
            elif is_doctor(user):
                return redirect('doctor_dashboard')
            elif is_receptionist(user):
                return redirect('reception_dashboard')
            elif is_nurse(user):
                return redirect('nurse_dashboard')
            else:
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def access_denied(request):
    return render(request, '403.html')


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('access_denied')

    today = date.today()
    appointments = Appointment.objects.filter(date_time__date=today).select_related('patient', 'doctor', 'doctor__user')

    scheduled = appointments.filter(status='scheduled')
    waiting = appointments.filter(status='waiting')
    active = appointments.filter(status='active')
    completed = appointments.filter(status='completed')

    # Добавь это:
    current_year = today.year
    current_month = today.month - 1  # JS-месяцы: 0-based
    months = [
        {'value': i, 'name': name, 'selected': i == current_month}
        for i, name in enumerate(['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                                  'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
    ]

    context = {
        'scheduled': scheduled,
        'waiting': waiting,
        'active': active,
        'completed': completed,
        'current_year': current_year,
        'current_month': current_month,
        'months': months,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def about_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    clinic = ClinicInfo.objects.first()
    return render(request, 'about.html', {'clinic': clinic})


@login_required
def doctor_dashboard(request):
    if not is_doctor(request.user):
        return redirect('access_denied')
    try:
        doctor_instance = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('access_denied')
    today = date.today()
    appointments = Appointment.objects.filter(doctor=doctor_instance, date_time__date=today)
    context = {
        'appointments': appointments,
    }
    return render(request, 'doctor_dashboard.html', context)


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
def services_management(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    return render(request, 'services_management.html')


@login_required
def personnel_management(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    doctors = Doctor.objects.all()
    nurses = Nurse.objects.all()
    receptionists = Receptionist.objects.all()
    users = User.objects.all()
    return render(request, 'personnel_management.html', {
        'doctors': doctors,
        'nurses': nurses,
        'receptionists': receptionists,
        'users': users,
    })


@login_required
def documents_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    return render(request, 'documents.html')


@login_required
def doctors_list(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    doctors = Doctor.objects.all()
    return render(request, 'doctors_list.html', {'doctors': doctors})


# ==================== API ====================

@require_http_methods(["GET"])
@login_required
def api_services_list(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    services = Service.objects.all()
    data = [{'id': s.id, 'name': s.name, 'price': float(s.price), 'duration': s.duration} for s in services]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_service_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        service = Service.objects.create(
            name=data['name'],
            price=data['price'],
            duration=data['duration']
        )
        return JsonResponse(
            {'id': service.id, 'name': service.name, 'price': float(service.price), 'duration': service.duration})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
@login_required
def api_service_detail(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    service = get_object_or_404(Service, pk=pk)
    data = {
        'id': service.id,
        'name': service.name,
        'price': float(service.price),
        'duration': service.duration
    }
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def api_service_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    service = get_object_or_404(Service, pk=pk)
    try:
        data = json.loads(request.body)
        service.name = data['name']
        service.price = data['price']
        service.duration = data['duration']
        service.save()
        return JsonResponse({
            'id': service.id,
            'name': service.name,
            'price': float(service.price),
            'duration': service.duration
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def api_service_delete(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    return JsonResponse({'success': True})


@login_required
def patients_search(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    patients = Patient.objects.all()
    return render(request, 'patients_search.html', {'patients': patients})


from django.db.models import Q


@login_required
def api_patients_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    q_lower = query.lower()
    patients = []

    # Фильтрация в Python — для регистра
    for p in Patient.objects.all():
        if (q_lower in p.last_name.lower() or
                q_lower in p.first_name.lower() or
                q_lower in p.phone.lower()):
            patients.append(p)
            if len(patients) >= 10:
                break

    data = [{
        'id': p.id,
        'full_name': p.get_full_name(),
        'phone': p.phone,
        'birth_date': p.birth_date.isoformat()
    } for p in patients]
    return JsonResponse(data, safe=False)


@login_required
def patient_detail(request, pk):
    if not is_admin(request.user):
        return redirect('access_denied')
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patient_detail.html', {'patient': patient})


from datetime import date


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def api_patient_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    patient = get_object_or_404(Patient, pk=pk)
    try:
        data = json.loads(request.body)

        birth_date_str = data.get('birth_date')
        if birth_date_str:
            patient.birth_date = date.fromisoformat(birth_date_str)  # ← Ключевая строка

        patient.last_name = data['last_name']
        patient.first_name = data['first_name']
        patient.middle_name = data.get('middle_name', '')
        patient.phone = data['phone']
        patient.email = data.get('email', '')
        patient.discount = int(data.get('discount', 0))
        patient.notes = data.get('notes', '')

        patient.save()

        return JsonResponse({
            'id': patient.id,
            'full_name': patient.get_full_name(),
            'phone': patient.phone,
            'birth_date': patient.birth_date.isoformat(),  # Теперь это date → работает
            'email': patient.email,
            'discount': patient.discount,
            'notes': patient.notes
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_schedule_by_date_and_doctor(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    date_str = request.GET.get('date', '')
    doctor_id = request.GET.get('doctor_id', None)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)

    appointments = Appointment.objects.filter(date_time__date=selected_date)

    if doctor_id:
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            appointments = appointments.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Врач не найден'}, status=400)

    # ✅ Сортируем по времени
    scheduled = appointments.filter(status='scheduled').order_by('date_time')
    waiting = appointments.filter(status='waiting').order_by('date_time')
    active = appointments.filter(status='active').order_by('date_time')
    completed = appointments.filter(status='completed').order_by('date_time')

    data = {
        'scheduled': [{
            'id': a.id,
            'patient_name': a.patient.get_full_name(),
            'time': a.get_time_slot_display(),
            'doctor_name': a.doctor.get_full_name()
        } for a in scheduled],
        'waiting': [{
            'id': a.id,
            'patient_name': a.patient.get_full_name(),
            'doctor_name': a.doctor.get_full_name()
        } for a in waiting],
        'active': [{
            'id': a.id,
            'patient_name': a.patient.get_full_name(),
            'doctor_name': a.doctor.get_full_name()
        } for a in active],
        'completed': [{
            'id': a.id,
            'patient_name': a.patient.get_full_name(),
            'time': a.date_time.strftime('%H:%M'),
            'doctor_name': a.doctor.get_full_name()
        } for a in completed],
    }

    return JsonResponse(data)


# --- DOCTOR ---

@login_required
def api_doctors_list(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    doctors = Doctor.objects.all()
    data = []
    for d in doctors:
        data.append({
            'id': d.id,
            'full_name': d.get_full_name(),
            'specialty': d.specialty,
            'room': d.room,
            'is_active': d.is_active,
            'user_username': d.user.username
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def api_doctor_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='doctor'
        )
        user.middle_name = data.get('middle_name', '')
        user.save()
        doctor = Doctor.objects.create(
            user=user,
            specialty=data['specialty'],
            room=data.get('room', ''),
            is_active=data.get('is_active', True)
        )
        return JsonResponse({
            'id': doctor.id,
            'full_name': doctor.get_full_name(),
            'specialty': doctor.specialty,
            'room': doctor.room,
            'is_active': doctor.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_doctor_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        doctor = get_object_or_404(Doctor, pk=pk)
        data = json.loads(request.body)
        doctor.user.first_name = data['first_name']
        doctor.user.last_name = data['last_name']
        doctor.user.middle_name = data.get('middle_name', '')
        doctor.user.username = data['username']
        if data.get('password'):
            doctor.user.set_password(data['password'])
        doctor.user.save()
        doctor.specialty = data['specialty']
        doctor.room = data.get('room', '')
        doctor.is_active = data.get('is_active', True)
        doctor.save()
        return JsonResponse({
            'id': doctor.id,
            'full_name': doctor.get_full_name(),
            'specialty': doctor.specialty,
            'room': doctor.room,
            'is_active': doctor.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_doctor_delete(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        doctor = get_object_or_404(Doctor, pk=pk)
        doctor.user.delete()
        doctor.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_doctor_detail(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    doctor = get_object_or_404(Doctor, pk=pk)
    data = {
        'id': doctor.id,
        'full_name': doctor.get_full_name(),
        'specialty': doctor.specialty,
        'room': doctor.room,
        'is_active': doctor.is_active,
        'user_username': doctor.user.username
    }
    return JsonResponse(data)


# --- NURSE ---
@login_required
def nurse_dashboard(request):
    if not is_nurse(request.user):
        return redirect('access_denied')
    return render(request, 'nurse_dashboard.html')


@login_required
def api_nurses_list(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    nurses = Nurse.objects.all()
    data = []
    for n in nurses:
        data.append({
            'id': n.id,
            'full_name': n.get_full_name(),
            'department': n.department,
            'room': n.room,
            'is_active': n.is_active,
            'user_username': n.user.username
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def api_nurse_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='nurse'
        )
        user.middle_name = data.get('middle_name', '')
        user.save()

        nurse = Nurse.objects.create(
            user=user,
            department=data.get('department', ''),
            room=data.get('room', ''),
            is_active=data.get('is_active', True)
        )
        return JsonResponse({
            'id': nurse.id,
            'full_name': nurse.get_full_name(),
            'department': nurse.department,
            'room': nurse.room,
            'is_active': nurse.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_nurse_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        nurse = get_object_or_404(Nurse, pk=pk)
        data = json.loads(request.body)
        nurse.user.first_name = data['first_name']
        nurse.user.last_name = data['last_name']
        nurse.user.middle_name = data.get('middle_name', '')
        nurse.user.username = data['username']
        if data.get('password'):
            nurse.user.set_password(data['password'])
        nurse.user.save()
        nurse.department = data.get('department', '')
        nurse.room = data.get('room', '')
        nurse.is_active = data.get('is_active', True)
        nurse.save()
        return JsonResponse({
            'id': nurse.id,
            'full_name': nurse.get_full_name(),
            'department': nurse.department,
            'room': nurse.room,
            'is_active': nurse.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_nurse_delete(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        nurse = get_object_or_404(Nurse, pk=pk)
        nurse.user.delete()
        nurse.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_nurse_detail(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    nurse = get_object_or_404(Nurse, pk=pk)
    data = {
        'id': nurse.id,
        'full_name': nurse.get_full_name(),
        'department': nurse.department,
        'room': nurse.room,
        'is_active': nurse.is_active,
        'user_username': nurse.user.username
    }
    return JsonResponse(data)


# --- RECEPTIONIST ---
@login_required
def reception_dashboard(request):
    if not is_receptionist(request.user):
        return redirect('access_denied')
    return render(request, 'reception_dashboard.html')


@login_required
def api_receptionists_list(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    receptionists = Receptionist.objects.all()
    data = []
    for r in receptionists:
        data.append({
            'id': r.id,
            'full_name': r.get_full_name(),
            'office': r.office,
            'is_active': r.is_active,
            'user_username': r.user.username
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def api_receptionist_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='receptionist'
        )
        user.middle_name = data.get('middle_name', '')
        user.save()

        receptionist = Receptionist.objects.create(
            user=user,
            office=data.get('office', ''),
            is_active=data.get('is_active', True)
        )
        return JsonResponse({
            'id': receptionist.id,
            'full_name': receptionist.get_full_name(),
            'office': receptionist.office,
            'is_active': receptionist.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_receptionist_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        receptionist = get_object_or_404(Receptionist, pk=pk)
        data = json.loads(request.body)
        receptionist.user.first_name = data['first_name']
        receptionist.user.last_name = data['last_name']
        receptionist.user.middle_name = data.get('middle_name', '')
        receptionist.user.username = data['username']
        if data.get('password'):
            receptionist.user.set_password(data['password'])
        receptionist.user.save()
        receptionist.office = data.get('office', '')
        receptionist.is_active = data.get('is_active', True)
        receptionist.save()
        return JsonResponse({
            'id': receptionist.id,
            'full_name': receptionist.get_full_name(),
            'office': receptionist.office,
            'is_active': receptionist.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_receptionist_delete(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        receptionist = get_object_or_404(Receptionist, pk=pk)
        receptionist.user.delete()
        receptionist.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_receptionist_detail(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    receptionist = get_object_or_404(Receptionist, pk=pk)
    data = {
        'id': receptionist.id,
        'full_name': receptionist.get_full_name(),
        'office': receptionist.office,
        'is_active': receptionist.is_active,
        'user_username': receptionist.user.username
    }
    return JsonResponse(data)


# --- DOCUMENTS ---
@login_required
def documents_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    documents = Document.objects.all().order_by('-created_at')
    return render(request, 'documents.html', {'documents': documents})


@csrf_exempt
@login_required
def api_document_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')

        doc = Document.objects.create(
            title=title,
            description=description,
            file=file
        )
        return JsonResponse({
            'id': doc.id,
            'title': doc.title,
            'description': doc.description,
            'file_url': doc.file.url if doc.file else None,
            'created_at': doc.created_at.strftime('%d.%m.%Y %H:%M')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_document_delete(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        doc = get_object_or_404(Document, pk=pk)
        doc.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_document_update(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        doc = get_object_or_404(Document, pk=pk)
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')

        doc.title = title
        doc.description = description
        if file:
            doc.file = file
        doc.save()

        return JsonResponse({
            'id': doc.id,
            'title': doc.title,
            'description': doc.description,
            'file_url': doc.file.url if doc.file else None,
            'created_at': doc.created_at.strftime('%d.%m.%Y %H:%M')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# СТАТИСТИКА
@login_required
def stats_full_view(request):
    if not is_admin(request.user):
        return redirect('access_denied')
    return render(request, 'stats_full.html')

@login_required
def api_stats_data(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)

    # ✅ Исправлено: startDate → start_date (нет, наоборот!)
    start_date_str = request.GET.get('startDate')  # ✅
    end_date_str = request.GET.get('endDate')      # ✅

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=30)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.now()

    # 1. Пациенты по месяцам
    patients_by_month = (
        Patient.objects.filter(
            appointments__date_time__range=[start_date, end_date]
        )
        .annotate(month=TruncMonth('appointments__date_time'))
        .values('month')
        .annotate(count=Count('id', distinct=True))
        .order_by('month')
    )

    # 2. Записи по врачам
    appointments_by_doctor = (
        Appointment.objects.filter(
            date_time__range=[start_date, end_date]
        )
        .values('doctor__user__last_name', 'doctor__user__first_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # 3. Прибыль по услугам
    revenue_by_service = (
        InvoiceService.objects.filter(
            invoice__appointment__date_time__range=[start_date, end_date]
        )
        .values('service__name')
        .annotate(total=Sum(F('price_at_time') * F('quantity')))
        .order_by('-total')
    )

    data = {
        'patients_by_month': [
            {'month': str(item['month'].date()), 'count': item['count']} for item in patients_by_month
        ],
        'appointments_by_doctor': list(appointments_by_doctor),
        'revenue_by_service': [
            {
                'appointment__invoice__items__service__name': item['service__name'],
                'total': float(item['total']) if item['total'] else 0
            } for item in revenue_by_service
        ]
    }

    return JsonResponse(data)

# Добавление пациента
@csrf_exempt
@login_required
def api_patient_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        patient = Patient.objects.create(
            last_name=data['last_name'],
            first_name=data['first_name'],
            middle_name=data.get('middle_name', ''),
            phone=data['phone'],
            email=data.get('email', ''),
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d') if data.get('birth_date') else None,
            discount=data.get('discount', 0),
            notes=data.get('notes', '')
        )
        return JsonResponse({
            'id': patient.id,
            'full_name': patient.get_full_name(),
            'phone': patient.phone
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_appointment_create(request):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)

        # Получаем данные
        patient_id = data['patient_id']
        doctor_id = data['doctor_id']
        datetime_str = data['datetime']  # формат: '2026-02-09T10:00'
        status = data.get('status', 'scheduled')
        duration = data.get('duration', 15)  # ✅ Добавь duration

        # Проверяем существование
        patient = Patient.objects.get(id=patient_id)
        doctor = Doctor.objects.get(id=doctor_id)

        # Преобразуем строку в datetime
        naive_dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')

        # ✅ Проверяем, кратно ли 10 минутам
        if naive_dt.minute % 10 != 0:
            return JsonResponse({'error': 'Время должно быть кратно 10 минутам'}, status=400)

        # ✅ Проверяем, кратно ли duration 10 минутам
        if duration % 10 != 0:
            return JsonResponse({'error': 'Длительность должна быть кратна 10 минутам'}, status=400)

        # ✅ Делаем aware
        aware_dt = timezone.make_aware(naive_dt)

        # Создаём запись
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date_time=aware_dt,
            status=status,
            duration=duration
        )

        return JsonResponse({
            'id': appointment.id,
            'patient_name': appointment.patient.get_full_name(),
            'doctor_name': appointment.doctor.get_full_name(),
            'datetime': appointment.date_time.strftime('%H:%M'),
            'status': appointment.status
        })
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Пациент не найден'}, status=400)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Врач не найден'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@login_required
def api_appointment_update_status(request, pk):
    if not is_admin(request.user):
        return JsonResponse({'error': 'Доступ запрещён'}, status=403)
    try:
        data = json.loads(request.body)
        new_status = data['status']

        # Проверяем, что статус допустим
        valid_statuses = ['scheduled', 'waiting', 'active', 'completed']
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Недопустимый статус'}, status=400)

        # ✅ Обновляем статус напрямую, без валидации
        rows_updated = Appointment.objects.filter(id=pk).update(status=new_status)

        if rows_updated == 0:
            return JsonResponse({'error': 'Запись не найдена'}, status=404)

        # Возвращаем обновлённые данные
        appointment = Appointment.objects.get(id=pk)

        return JsonResponse({
            'success': True,
            'id': appointment.id,
            'status': appointment.status
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Запись не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
