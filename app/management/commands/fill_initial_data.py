from django.core.management.base import BaseCommand
from app.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from app.models import (
    ClinicInfo, Doctor, Nurse, Receptionist, Service, Patient, Appointment, Invoice, InvoiceService, Document
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

        # 2. Услуги
        if not Service.objects.exists():
            Service.objects.create(name='Консультация', price=1000, duration=30)
            Service.objects.create(name='Лечение кариеса', price=2500, duration=60)
            Service.objects.create(name='Удаление зуба', price=1500, duration=40)
            Service.objects.create(name='Отбеливание', price=5000, duration=90)
            Service.objects.create(name='Имплантация', price=20000, duration=120)
            Service.objects.create(name='Протезирование', price=12000, duration=100)
            self.stdout.write(self.style.SUCCESS('Услуги созданы'))

        # 3. Врачи (4)
        doctors = []
        if not Doctor.objects.exists():
            doctor_data = [
                ('dr_ivanov', 'Иван', 'Иванов', 'Петрович', 'Терапевт', '101'),
                ('dr_petrov', 'Петр', 'Петров', 'Иванович', 'Хирург', '102'),
                ('dr_sokolov', 'Михаил', 'Соколов', 'Андреевич', 'Ортодонт', '103'),
                ('dr_lebedeva', 'Ольга', 'Лебедева', 'Владимировна', 'Пародонтолог', '104')
            ]
            for username, first, last, middle, specialty, room in doctor_data:
                user = User.objects.create_user(
                    username=username,
                    password='password123',
                    first_name=first,
                    last_name=last,
                    middle_name=middle,
                    role='doctor'
                )
                doctor = Doctor.objects.create(
                    user=user,
                    specialty=specialty,
                    room=room,
                    is_active=True
                )
                doctors.append(doctor)
                self.stdout.write(self.style.SUCCESS(f'Врач {last} создан'))
        else:
            doctors = list(Doctor.objects.all())

        # 4. Медсестра
        if not Nurse.objects.exists():
            user = User.objects.create_user(
                username='med_sestra',
                password='password123',
                first_name='Анна',
                last_name='Смирнова',
                middle_name='Сергеевна',
                role='nurse'
            )
            Nurse.objects.create(
                user=user,
                department='Терапия',
                room='101',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Медсестра создана'))

        # 5. Регистратор
        if not Receptionist.objects.exists():
            user = User.objects.create_user(
                username='reception',
                password='password123',
                first_name='Мария',
                last_name='Волкова',
                middle_name='Алексеевна',
                role='receptionist'
            )
            Receptionist.objects.create(
                user=user,
                office='1',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Регистратор создан'))

        # 6. Пациенты
        patients = []
        if not Patient.objects.exists():
            patient_data = [
                ('Алексей', 'Сидоров', 'Михайлович', '1990-05-15', '+7 (999) 888-77-66', 'alex@example.com'),
                ('Елена', 'Кузнецова', 'Олеговна', '1985-10-22', '+7 (999) 111-22-33', 'elena@example.com'),
                ('Дмитрий', 'Волков', 'Сергеевич', '1992-03-10', '+7 (999) 222-33-44', 'dmitry@example.com'),
                ('Анна', 'Зайцева', 'Петровна', '1988-07-18', '+7 (999) 333-44-55', 'anna@example.com'),
                ('Игорь', 'Морозов', 'Александрович', '1995-12-01', '+7 (999) 444-55-66', 'igor@example.com'),
                ('Екатерина', 'Васильева', 'Дмитриевна', '1987-09-14', '+7 (999) 555-66-77', 'ekaterina@example.com'),
                ('Александр', 'Петров', 'Михайлович', '1991-01-25', '+7 (999) 666-77-88', 'alexander@example.com'),
                ('Марина', 'Семенова', 'Игоревна', '1989-04-30', '+7 (999) 777-88-99', 'marina@example.com'),
                ('Владимир', 'Голубев', 'Алексеевич', '1993-08-12', '+7 (999) 888-99-00', 'vladimir@example.com'),
                ('Татьяна', 'Виноградова', 'Сергеевна', '1986-11-05', '+7 (999) 999-00-11', 'tatiana@example.com'),
            ]
            for first, last, middle, birth, phone, email in patient_data:
                patient = Patient.objects.create(
                    first_name=first,
                    last_name=last,
                    middle_name=middle,
                    birth_date=datetime.strptime(birth, '%Y-%m-%d').date(),
                    phone=phone,
                    email=email,
                    discount=10,
                    notes=f'Заметка для {first} {last}'
                )
                patients.append(patient)
            self.stdout.write(self.style.SUCCESS('Пациенты созданы'))
        else:
            patients = list(Patient.objects.all())

        # 7. Записи (10)
        if not Appointment.objects.exists():
            services = list(Service.objects.all())
            statuses = ['scheduled', 'waiting', 'active', 'completed']

            for i in range(10):
                patient = patients[i % len(patients)]
                doctor = doctors[i % len(doctors)]

                # ✅ Генерируем корректное будущее время, кратное 10 минутам
                now = timezone.now()
                # Убираем секунды и микросекунды
                base_time = now.replace(second=0, microsecond=0)
                # Округляем минуты до следующего кратного 10
                next_10_min = ((base_time.minute // 10) + 1) * 10
                if next_10_min >= 60:
                    next_10_min = 0
                    base_time += timedelta(hours=1)
                date_time = base_time.replace(minute=next_10_min)

                # Добавляем интервал между записями (по 1 часу)
                date_time += timedelta(hours=i)

                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    date_time=date_time,
                    status=statuses[i % len(statuses)],
                    duration=60
                )

                # Создаём счёт
                invoice = Invoice.objects.create(
                    appointment=appointment,
                    total_amount=services[i % len(services)].price,
                    discount_applied=10,
                    is_paid=True
                )

                # Создаём позицию в счёте
                InvoiceService.objects.create(
                    invoice=invoice,
                    service=services[i % len(services)],
                    price_at_time=services[i % len(services)].price,
                    quantity=1
                )

            self.stdout.write(self.style.SUCCESS('Записи, счета и услуги созданы'))

        # 8. Документы
        if not Document.objects.exists():
            titles = [
                'Политика конфиденциальности',
                'Договор на лечение',
                'Анкета пациента',
                'Согласие на обработку данных',
                'Рекомендации после лечения',
                'Справка о состоянии здоровья',
                'Согласие на лечение',
                'Форма опросника',
                'Договор на протезирование',
                'Рецепт на лекарства'
            ]
            for title in titles:
                Document.objects.create(
                    title=title,
                    description=f'Документ: {title}'
                )
            self.stdout.write(self.style.SUCCESS('Документы созданы'))

        self.stdout.write(self.style.SUCCESS('Все начальные данные заполнены!'))