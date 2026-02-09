from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from app.models import (
    ClinicInfo, Doctor, Nurse, Receptionist, Service, Patient, Appointment, Invoice
)


class Command(BaseCommand):
    help = 'Заполняет базу данных начальными данными'

    def handle(self, *args, **options):
        # 1. Клиника
        if not ClinicInfo.objects.exists():
            ClinicInfo.objects.create(
                name="Клиника \"Улыбка\"",
                program_name="DentalClick",
                address="ул. Примерная, д. 123",
                phone="+7 (123) 456-78-90"
            )
            self.stdout.write(self.style.SUCCESS('Клиника создана'))

        # 2. Врачи
        if not Doctor.objects.exists():
            user1 = User.objects.create_user(
                username='dr_ivanov',
                password='password123',
                first_name='Иван',
                last_name='Иванов',
                middle_name='Петрович',
                role='doctor'
            )
            Doctor.objects.create(
                user=user1,
                specialty='Терапевт',
                room='101',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Врач Иванов создан'))

            user2 = User.objects.create_user(
                username='dr_petrov',
                password='password123',
                first_name='Петр',
                last_name='Петров',
                middle_name='Иванович',
                role='doctor'
            )
            Doctor.objects.create(
                user=user2,
                specialty='Хирург',
                room='102',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Врач Петров создан'))

        # 3. Медсестры
        if not Nurse.objects.exists():
            user3 = User.objects.create_user(
                username='med_sestra',
                password='password123',
                first_name='Анна',
                last_name='Смирнова',
                middle_name='Сергеевна',
                role='nurse'
            )
            Nurse.objects.create(
                user=user3,
                department='Терапия',
                room='101',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Медсестра Смирнова создана'))

        # 4. Регистраторы
        if not Receptionist.objects.exists():
            user4 = User.objects.create_user(
                username='reception',
                password='password123',
                first_name='Мария',
                last_name='Волкова',
                middle_name='Алексеевна',
                role='receptionist'
            )
            Receptionist.objects.create(
                user=user4,
                office='1',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Регистратор Волкова создана'))

        # 5. Услуги
        if not Service.objects.exists():
            Service.objects.create(name='Консультация', price=1000, duration=30)
            Service.objects.create(name='Лечение кариеса', price=2500, duration=60)
            Service.objects.create(name='Удаление зуба', price=1500, duration=40)
            Service.objects.create(name='Отбеливание', price=5000, duration=90)
            self.stdout.write(self.style.SUCCESS('Услуги созданы'))

        # 6. Пациенты
        if not Patient.objects.exists():
            patient1 = Patient.objects.create(
                first_name='Алексей',
                last_name='Сидоров',
                middle_name='Михайлович',
                birth_date=datetime(1990, 5, 15).date(),
                phone='+7 (999) 888-77-66',
                email='alex@example.com',
                discount=10,
                notes='Любит кофе'
            )
            patient2 = Patient.objects.create(
                first_name='Елена',
                last_name='Кузнецова',
                middle_name='Олеговна',
                birth_date=datetime(1985, 10, 22).date(),
                phone='+7 (999) 111-22-33',
                email='elena@example.com',
                discount=5,
                notes='Аллергия на анестетик'
            )
            self.stdout.write(self.style.SUCCESS('Пациенты созданы'))

        # 7. Записи
        if not Appointment.objects.exists():
            doctor1 = Doctor.objects.first()
            patient1 = Patient.objects.first()
            appointment1 = Appointment.objects.create(
                patient=patient1,
                doctor=doctor1,
                date_time=timezone.now().replace(hour=10, minute=0),
                status='scheduled',
                duration=60
            )
            Invoice.objects.create(
                appointment=appointment1,
                total_amount=2500,
                discount_applied=10,
                is_paid=True
            )
            self.stdout.write(self.style.SUCCESS('Запись и счёт созданы'))

        self.stdout.write(self.style.SUCCESS('Все начальные данные заполнены!'))
