from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator


# ==================== Клиника ====================
class ClinicInfo(models.Model):
    name = models.CharField('Название клиники', max_length=200)
    program_name = models.CharField('Название программы', max_length=200, default='DentalClick')
    address = models.TextField('Адрес', blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Информация о клинике'
        verbose_name_plural = 'Информация о клинике'

    def __str__(self):
        return self.name


# ==================== ПОЛЬЗОВАТЕЛЬ ====================
phone_validator = RegexValidator(
    regex=r'^\+?\d{7,20}$',
    message='Телефон должен содержать только цифры и опционально знак +, длина 7-20 символов'
)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор (Главврач)'),
        ('receptionist', 'Регистратор'),
        ('doctor', 'Врач'),
        ('nurse', 'Медсестра'),
    ]
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='doctor')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    middle_name = models.CharField('Отчество', max_length=50, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='clinic_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='clinic_user_set',
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


# ==================== ПАЦИЕНТ ====================
class Patient(models.Model):
    first_name = models.CharField('Имя', max_length=50)
    last_name = models.CharField('Фамилия', max_length=50)
    middle_name = models.CharField('Отчество', max_length=50, blank=True, null=True)
    birth_date = models.DateField('Дата рождения')
    phone = models.CharField('Телефон', max_length=20, validators=[phone_validator])
    email = models.EmailField('Email', blank=True)
    discount = models.IntegerField('Скидка %', default=0)
    notes = models.TextField('Заметки', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name}"


# ==================== ВРАЧ ====================
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    specialty = models.CharField('Специальность', max_length=100)
    room = models.CharField('Кабинет', max_length=10, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'
        ordering = ['user__last_name']

    def __str__(self):
        return f"Др. {self.user.last_name} {self.user.first_name}"

    def get_full_name(self):
        parts = [self.user.last_name, self.user.first_name]
        if self.user.middle_name:
            parts.append(self.user.middle_name)
        return ' '.join(parts)


# ==================== УСЛУГА ====================
class Service(models.Model):
    name = models.CharField('Название', max_length=200)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    duration = models.IntegerField('Длительность (мин)', default=30)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['name']

    def __str__(self):
        return self.name


# ==================== МЕДСЕСТРА ====================
class Nurse(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    department = models.CharField('Отделение', max_length=100, blank=True)
    room = models.CharField('Кабинет', max_length=10, blank=True)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Медсестра'
        verbose_name_plural = 'Медсестры'
        ordering = ['user__last_name']

    def __str__(self):
        return f"Медсестра {self.user.last_name} {self.user.first_name} "

    def get_full_name(self):
        parts = [self.user.last_name, self.user.first_name]
        if self.user.middle_name:
            parts.append(self.user.middle_name)
        return ' '.join(parts)


# ==================== РЕГИСТРАТОР ====================
class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    office = models.CharField('Офис', max_length=100, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Регистратор'
        verbose_name_plural = 'Регистраторы'
        ordering = ['user__last_name']

    def __str__(self):
        return f"Регистратор {self.user.last_name} {self.user.first_name}"

    def get_full_name(self):
        parts = [self.user.last_name, self.user.first_name]
        if self.user.middle_name:
            parts.append(self.user.middle_name)
        return ' '.join(parts)


# ==================== ЗАПИСЬ НА ПРИЕМ ====================
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланирован'),
        ('waiting', 'Ожидает'),
        ('active', 'На приёме'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
        ('no_show', 'Не пришел'),
    ]

    CANCEL_REASON_CHOICES = [
        ('patient_cancelled', 'Пациент отменил'),
        ('doctor_cancelled', 'Врач отменил'),
        ('emergency', 'Экстренная ситуация'),
        ('other', 'Другое'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name='Пациент')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='Врач')
    date_time = models.DateTimeField('Дата и время приема')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='scheduled')

    duration = models.IntegerField(
        'Длительность приема (мин)',
        default=15,
        help_text="Кратно 10 минутам",
        validators=[MinValueValidator(10)]
    )

    cancel_reason_type = models.CharField(
        'Тип причины отмены',
        max_length=20,
        choices=CANCEL_REASON_CHOICES,
        blank=True,
        null=True,
        help_text="Выберите из списка"
    )

    reason = models.TextField('Причина обращения', blank=True)
    diagnosis = models.TextField('Диагноз', blank=True)
    treatment = models.TextField('Лечение', blank=True)
    cancel_reason = models.TextField('Причина отмены (комментарий)', blank=True)
    notes = models.TextField('Заметки врача', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Запись на прием'
        verbose_name_plural = 'Записи на прием'
        ordering = ['-date_time']
        # Partial index/condition: работает в PostgreSQL. Если используете SQLite в dev — учтите ограничение.
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'date_time'],
                name='unique_doctor_time',
                condition=models.Q(status='scheduled')
            )
        ]

    def clean(self):
        """ВАЛИДАЦИЯ ПЕРЕД СОХРАНЕНИЕМ"""
        super().clean()
        errors = {}

        #  Проверка: запись не в прошлом
        if self.date_time and self.date_time < timezone.now():
            errors['date_time'] = 'Нельзя записывать на прошедшее время'

        # Проверка: время кратно 10 минутам
        if self.date_time and (
                self.date_time.minute % 10 != 0 or self.date_time.second != 0 or self.date_time.microsecond != 0):
            errors['date_time'] = 'Время должно быть кратно 10 минутам (например: 10:00, 10:10, 10:20)'

        # Проверка: длительность кратна 10 минутам
        if self.duration and self.duration % 10 != 0:
            errors['duration'] = '⏱️ Длительность должна быть кратна 10 минутам'

        # Проверка: врач активен
        if self.doctor and not self.doctor.is_active:
            errors['doctor'] = '🚫 Этот врач временно не принимает (в отпуске или уволен)'

        if self.status == 'scheduled' and self.date_time and self.doctor:
            overlap_error = self._check_time_overlap()
            if overlap_error:
                errors['date_time'] = overlap_error

        #  Если статус "отменен", должна быть причина
        if self.status == 'cancelled' and not self.cancel_reason_type and not self.cancel_reason:
            errors['cancel_reason_type'] = '📝 Укажите причину отмены'
            errors['cancel_reason'] = '📝 Или напишите комментарий'

        if errors:
            raise ValidationError(errors)

    def _check_time_overlap(self):
        """Проверка пересечения времени у врача"""
        if not self.doctor or not self.date_time:
            return None

        end_time = self.date_time + timedelta(minutes=self.duration)

        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            status='scheduled'
        ).exclude(pk=self.pk if self.pk else None)

        for appointment in overlapping:
            appt_end = appointment.date_time + timedelta(minutes=appointment.duration)
            if (self.date_time < appt_end and end_time > appointment.date_time):
                return (
                    f"⏰ ВРЕМЯ ЗАНЯТО!\n"
                    f"У врача {self.doctor} уже есть запись:\n"
                    f"• Пациент: {appointment.patient}\n"
                    f"• Время: {appointment.date_time.strftime('%d.%m.%Y %H:%M')}\n"
                    f"• Длительность: {appointment.duration} мин\n"
                    f"• Окончание: {appt_end.strftime('%H:%M')}"
                )
        return None

    def get_time_slot_display(self):
        """Отображение временного слота"""
        if not self.date_time:
            return ""
        end_time = self.date_time + timedelta(minutes=self.duration)
        return f"{self.date_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

    def save(self, *args, **kwargs):
        """Автоматическая валидация и заполнение при сохранении"""
        # Вызываем полную валидацию
        self.full_clean()

        # Автоматически заполняем поля при отмене
        if self.status == 'cancelled' and not self.cancel_reason and self.cancel_reason_type:
            reason_map = {
                'patient_cancelled': 'Пациент отменил запись',
                'doctor_cancelled': 'Врач отменил запись',
                'emergency': 'Экстренная ситуация',
                'other': 'Запись отменена',
            }
            self.cancel_reason = reason_map.get(self.cancel_reason_type, 'Запись отменена')

        super().save(*args, **kwargs)

    def __str__(self):
        if not self.date_time:
            return f"{self.patient} → {self.doctor} | без времени | {self.get_status_display()}"
        time_slot = self.get_time_slot_display()
        return f"{self.patient} → {self.doctor} | {self.date_time:%d.%m.%Y} {time_slot} | {self.get_status_display()}"


# ==================== СЧЕТ ====================
class Invoice(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, verbose_name='Запись')
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_applied = models.IntegerField('Примененная скидка', default=0)
    final_amount = models.DecimalField('Итоговая сумма', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField('Оплачен', default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал',
        related_name='invoices_created'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    paid_at = models.DateTimeField('Дата оплаты', null=True, blank=True)

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'

    def __str__(self):
        return f"Счет #{self.id} - {self.final_amount} руб."

    def save(self, *args, **kwargs):
        # Используем Decimal для точных вычислений и округления
        total = Decimal(self.total_amount) if self.total_amount is not None else Decimal('0.00')
        discount = Decimal(self.discount_applied or 0)
        discount_factor = (Decimal(100) - discount) / Decimal(100)
        calculated = (total * discount_factor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.final_amount = calculated
        super().save(*args, **kwargs)


# ==================== УСЛУГИ В СЧЕТЕ ====================
class InvoiceService(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name='Счет', related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Услуга')
    quantity = models.IntegerField('Количество', default=1, validators=[MinValueValidator(1)])
    price_at_time = models.DecimalField('Цена на момент оказания', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Услуга в счете'
        verbose_name_plural = 'Услуги в счетах'

    def __str__(self):
        return f"{self.service.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Подставляем цену из Service, если не указана
        if (self.price_at_time is None or Decimal(self.price_at_time) == Decimal('0')) and self.service:
            self.price_at_time = self.service.price
        super().save(*args, **kwargs)


# models.py
class Document(models.Model):
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    file = models.FileField('Файл', upload_to='documents/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def __str__(self):
        return self.title