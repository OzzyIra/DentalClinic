from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.db.models import F, Sum
from django.core.exceptions import ValidationError
from .models import (
    User,
    Patient,
    Doctor,
    Nurse,
    Receptionist,
    Service,
    Appointment,
    Invoice,
    InvoiceService,
    ClinicInfo,
)


# Проверка доступа к админке
def user_has_admin_access(user):
    return user.is_superuser or (user.is_staff and user.role == 'admin')


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Имя")
    last_name = forms.CharField(max_length=150, required=True, label="Фамилия")
    phone = forms.CharField(max_length=20, required=True, label="Телефон")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'role')


class CustomUserChangeForm(UserChangeForm):
    first_name = forms.CharField(max_length=150, required=True, label="Имя")
    last_name = forms.CharField(max_length=150, required=True, label="Фамилия")
    phone = forms.CharField(max_length=20, required=True, label="Телефон")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'role')


class CustomUserAdmin(BaseUserAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = (
        ('Личная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Контактные данные', {'fields': ('phone',)}),
        ('Аккаунт', {'fields': ('username', 'password')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Дополнительно', {'fields': ('role',)}),
    )

    add_fieldsets = (
        ('Личная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Контактные данные', {'fields': ('phone',)}),
        ('Аккаунт', {'fields': ('username', 'password1', 'password2')}),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'groups', 'user_permissions'),
        }),
        ('Дополнительно', {'fields': ('role',)}),
    )


@admin.register(ClinicInfo)
class ClinicInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_name']

    def has_add_permission(self, request):
        # Запрещаем создавать более одной записи
        if ClinicInfo.objects.exists():
            return False
        return super().has_add_permission(request)


# Кастомный PatientAdmin
class PatientAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

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


class DoctorAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    list_display = ['get_full_name', 'specialty', 'room', 'is_active', 'get_phone']
    list_filter = ['specialty', 'is_active']
    search_fields = ['user__last_name', 'user__first_name', 'specialty', 'room']
    list_editable = ['room', 'is_active']
    list_select_related = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        class DoctorForm(form):
            def clean(self):
                cleaned_data = super().clean()
                user = cleaned_data.get('user')

                if user:
                    if not user.first_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнено имя.")
                    if not user.last_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнена фамилия.")
                    if not user.phone.strip():
                        self.add_error('user', "У пользователя должен быть заполнен телефон.")

                specialty = cleaned_data.get('specialty')
                if specialty and not specialty.strip():
                    self.add_error('specialty', "Специальность не может быть пустой.")

                return cleaned_data

        return DoctorForm

    @admin.display(description='Врач', ordering='user__last_name')
    def get_full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    @admin.display(description='Телефон')
    def get_phone(self, obj):
        return obj.user.phone if obj.user.phone else "—"


class NurseAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    list_display = ['get_full_name', 'department', 'room', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['user__last_name', 'user__first_name']
    list_select_related = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        class NurseForm(form):
            def clean(self):
                cleaned_data = super().clean()
                user = cleaned_data.get('user')

                if user:
                    if not user.first_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнено имя.")
                    if not user.last_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнена фамилия.")
                    if not user.phone.strip():
                        self.add_error('user', "У пользователя должен быть заполнен телефон.")

                return cleaned_data

        return NurseForm

    @admin.display(description='Медсестра', ordering='user__last_name')
    def get_full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"


# Кастомный ReceptionistAdmin
class ReceptionistAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    list_display = ['get_full_name', 'office', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__last_name', 'user__first_name']
    list_select_related = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        class ReceptionistForm(form):
            def clean(self):
                cleaned_data = super().clean()
                user = cleaned_data.get('user')

                if user:
                    if not user.first_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнено имя.")
                    if not user.last_name.strip():
                        self.add_error('user', "У пользователя должно быть заполнена фамилия.")
                    if not user.phone.strip():
                        self.add_error('user', "У пользователя должен быть заполнен телефон.")

                return cleaned_data

        return ReceptionistForm

    @admin.display(description='Регистратор', ordering='user__last_name')
    def get_full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"


# Кастомный ServiceAdmin
class ServiceAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    list_display = ['name', 'price', 'duration', 'formatted_price']
    list_editable = ['price', 'duration']
    search_fields = ['name']

    @admin.display(description='Цена')
    def formatted_price(self, obj):
        try:
            return f"{obj.price:.2f} руб."
        except Exception:
            return obj.price


# Кастомный AppointmentAdmin
class AppointmentAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

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


# Кастомный InvoiceServiceInline
class InvoiceServiceInline(admin.TabularInline):
    model = InvoiceService
    extra = 1
    fields = ['service', 'quantity', 'price_at_time']
    readonly_fields = []
    autocomplete_fields = ['service']

    def has_add_permission(self, request, obj=None):
        return user_has_admin_access(request.user)

    def has_change_permission(self, request, obj=None):
        return user_has_admin_access(request.user)

    def has_delete_permission(self, request, obj=None):
        return user_has_admin_access(request.user)


# Кастомный InvoiceAdmin
class InvoiceAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return user_has_admin_access(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

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
            if not inst.price_at_time and inst.service:
                inst.price_at_time = inst.service.price
            inst.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()

        invoice = form.instance
        totals = InvoiceService.objects.filter(invoice=invoice).aggregate(
            total=Sum(F('price_at_time') * F('quantity'))
        )
        total_amount = totals.get('total') or 0
        invoice.total_amount = total_amount
        invoice.save()


# НАСТРОЙКИ АДМИНКИ
admin.site.site_header = "🦷 Стоматологическая клиника - Панель управления"
admin.site.site_title = "Стоматология"
admin.site.index_title = "Администрирование"

# Регистрация моделей
admin.site.register(User, CustomUserAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Nurse, NurseAdmin)
admin.site.register(Receptionist, ReceptionistAdmin)
