from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.db.models import F, Sum
from .models import (
    User,
    Patient,
    Doctor,
    Service,
    Appointment,
    Invoice,
    InvoiceService,
)


# ПОЛЬЗОВАТЕЛЬ
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Информация о сотруднике', {'fields': ('role', 'phone')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Информация о сотруднике', {'fields': ('role', 'phone')}),
    )


#  ПАЦИЕНТ
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'middle_name', 'phone', 'birth_date', 'discount', 'created_at']
    list_filter = ['discount', 'created_at']
    search_fields = ['last_name', 'first_name', 'phone', 'email']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('last_name', 'first_name', 'middle_name', 'birth_date')
        }),
        ('Контакты', {
            'fields': ('phone', 'email')
        }),
        ('Дополнительно', {
            'fields': ('discount', 'notes', 'created_at')
        }),
    )


#  ВРАЧ
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'specialty', 'room', 'is_active', 'get_phone']
    list_filter = ['specialty', 'is_active']
    search_fields = ['user__last_name', 'user__first_name', 'specialty', 'room']
    list_editable = ['room', 'is_active']
    list_select_related = ('user',)

    @admin.display(description='Врач', ordering='user__last_name')
    def get_full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    @admin.display(description='Телефон')
    def get_phone(self, obj):
        return obj.user.phone if obj.user.phone else "—"


# УСЛУГА
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration', 'formatted_price']
    list_editable = ['price', 'duration']
    search_fields = ['name']

    @admin.display(description='Цена')
    def formatted_price(self, obj):
        try:
            return f"{obj.price:.2f} руб."
        except Exception:
            return obj.price


# ЗАПИСЬ

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date_time', 'get_time_slot', 'duration', 'get_status_display',
                    'cancel_reason_type']
    list_filter = ['status', 'doctor', 'date_time']
    search_fields = ['patient__last_name', 'patient__first_name', 'doctor__user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'get_time_slot']
    date_hierarchy = 'date_time'
    list_per_page = 20
    list_select_related = ('patient', 'doctor', 'doctor__user')

    actions = ['mark_as_completed', 'mark_as_cancelled', 'mark_as_no_show']

    fieldsets = (
        ('Основная информация', {
            'fields': ('patient', 'doctor', 'date_time', 'duration', 'status')
        }),
        ('Информация о приеме', {
            'fields': ('reason', 'diagnosis', 'treatment', 'notes')
        }),
        ('Отмена записи', {
            'fields': ('cancel_reason_type', 'cancel_reason'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('get_time_slot', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Кастомная форма с HTML5 виджетом времени
    def get_form(self, request, obj=None, **kwargs):
        class AppointmentForm(forms.ModelForm):
            date_time = forms.DateTimeField(
                widget=forms.DateTimeInput(attrs={
                    'type': 'datetime-local',
                    'step': '600',  # 10 минут в секундах
                    'class': 'vDateTimeField',
                    'placeholder': 'Выберите дату и время (кратно 10 минутам)'
                }),
                input_formats=['%Y-%m-%dT%H:%M'],
                label="Дата и время приема",
                help_text="Время должно быть кратно 10 минутам (10:00, 10:10, 10:20...)"
            )

            duration = forms.IntegerField(
                min_value=10,
                max_value=480,  # 8 часов максимум
                help_text="Длительность в минутах (кратно 10)",
                widget=forms.NumberInput(attrs={'step': 10})
            )

            class Meta:
                model = Appointment
                fields = '__all__'

        kwargs['form'] = AppointmentForm
        return super().get_form(request, obj, **kwargs)

    @admin.display(description='Временной слот')
    def get_time_slot(self, obj):
        if not obj or not obj.date_time:
            return ""
        return obj.get_time_slot_display()

    @admin.display(description='Статус')
    def get_status_display(self, obj):
        return obj.get_status_display()

    # Кастомные действия
    @admin.action(description='Отметить как завершенные')
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} записей отмечено как завершенные")

    @admin.action(description='Отменить выбранные записи')
    def mark_as_cancelled(self, request, queryset):
        count = 0
        for appointment in queryset:
            appointment.status = 'cancelled'
            if not appointment.cancel_reason_type:
                appointment.cancel_reason_type = 'other'
            appointment.save()
            count += 1
        self.message_user(request, f"{count} записей отменено")

    @admin.action(description='Отметить как "Не пришел"')
    def mark_as_no_show(self, request, queryset):
        updated = queryset.update(status='no_show')
        self.message_user(request, f"{updated} пациентов не пришли на прием")


# СЧЕТ (INLINE для услуг)
class InvoiceServiceInline(admin.TabularInline):
    model = InvoiceService
    extra = 1
    fields = ['service', 'quantity', 'price_at_time']
    readonly_fields = []  # можно добавить 'price_at_time' если автозаполнение настроено
    autocomplete_fields = ['service']


# СЧЕТ
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'total_amount', 'discount_applied', 'final_amount', 'is_paid', 'created_at']
    list_filter = ['is_paid', 'created_at']
    search_fields = ['appointment__patient__last_name', 'appointment__doctor__user__last_name']
    readonly_fields = ['final_amount', 'created_at', 'paid_at']
    inlines = [InvoiceServiceInline]
    list_select_related = ('appointment', 'created_by')

    fieldsets = (
        ('Основная информация', {
            'fields': ('appointment', 'total_amount', 'discount_applied', 'final_amount')
        }),
        ('Оплата', {
            'fields': ('is_paid', 'paid_at', 'created_by')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Сохраняем инлайны, затем пересчитываем суммы в счёте.
        """
        instances = formset.save(commit=False)
        for inst in instances:
            # Если price_at_time не заполнено, заполняем текущей ценой услуги
            if not inst.price_at_time and inst.service:
                inst.price_at_time = inst.service.price
            inst.save()
        # удалить удалённые
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()

        # После сохранения инлайнов пересчитываем total и final
        invoice = form.instance
        totals = InvoiceService.objects.filter(invoice=invoice).aggregate(
            total=Sum(F('price_at_time') * F('quantity'))
        )
        total_amount = totals.get('total') or 0
        invoice.total_amount = total_amount
        # final_amount пересчитывается в модели Invoice.save()
        invoice.save()


# НАСТРОЙКИ АДМИНКИ
admin.site.site_header = "🦷 Стоматологическая клиника - Панель управления"
admin.site.site_title = "Стоматология"
admin.site.index_title = "Администрирование"
