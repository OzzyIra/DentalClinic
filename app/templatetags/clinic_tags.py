from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as date_filter

register = template.Library()


@register.simple_tag
def get_clinic_info():
    from app.models import ClinicInfo
    return ClinicInfo.objects.first() or ClinicInfo(
        name="Клиника",
        program_name="Программа"
    )


# Фильтр: добавляет "руб." к числу
@register.filter
def rubles(value):
    try:
        return f"{float(value):.2f} руб."
    except (ValueError, TypeError):
        return value


# Фильтр: читаемый формат времени (HH:MM)
@register.filter
def time_format(value):
    if value:
        return value.strftime("%H:%M")
    return ""


# Фильтр: читаемый формат даты и времени
@register.filter
def datetime_format(value):
    if value:
        return date_filter(value, "d.m.Y H:i")
    return ""


# Фильтр: возвращает HTML-цвет в зависимости от статуса
@register.filter
def status_color(status):
    colors = {
        'scheduled': '#d1ecf1',
        'completed': '#d4edda',
        'cancelled': '#f8d7da',
        'no_show': '#fff3cd',
    }
    return colors.get(status, '#ffffff')


# Фильтр: возвращает читаемый статус
@register.filter
def status_label(status):
    labels = {
        'scheduled': 'Запланирован',
        'completed': 'Завершён',
        'cancelled': 'Отменён',
        'no_show': 'Не пришёл',
    }
    return labels.get(status, status)


# Простой тег: получить количество активных пациентов
@register.simple_tag
def active_patients_count():
    from app.models import Patient
    return Patient.objects.count()


# Простой тег: получить количество активных врачей
@register.simple_tag
def active_doctors_count():
    from app.models import Doctor
    return Doctor.objects.filter(is_active=True).count()


# Простой тег: получить количество записей на сегодня
@register.simple_tag
def appointments_today_count():
    from app.models import Appointment
    from datetime import date
    return Appointment.objects.filter(date_time__date=date.today()).count()
