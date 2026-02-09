// ✅ Переменная для хранения текущей даты
let currentDate = null;

document.addEventListener('DOMContentLoaded', function() {
    // Данные из контекста (получаются из HTML)
    const currentYear = parseInt(document.body.dataset.currentYear);
    const currentMonth = parseInt(document.body.dataset.currentMonth);

    // ✅ Восстанавливаем дату из localStorage или устанавливаем сегодня
    const savedDate = localStorage.getItem('selectedDate');
    if (savedDate) {
        currentDate = savedDate;
    } else {
        const today = new Date();
        currentDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    }

    // Инициализация календаря
    const triggerBtn = document.getElementById('calendar-trigger');
    const modalEl = document.getElementById('calendarModal');
    const calendarModal = new bootstrap.Modal(modalEl);

    // Генерация календаря
    function generateCalendar(year, month) {
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startDayOfWeek = firstDay.getDay();

        const container = document.getElementById('cal-days');
        container.innerHTML = '';

        // Пустые ячейки до первого дня
        for (let i = 0; i < startDayOfWeek; i++) {
            const div = document.createElement('div');
            div.style.width = '28px';
            div.style.height = '28px';
            div.style.border = '1px solid #eee';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.justifyContent = 'center';
            div.style.fontSize = '0.8rem';
            div.style.cursor = 'default';
            container.appendChild(div);
        }

        // Дни месяца
        for (let day = 1; day <= daysInMonth; day++) {
            const div = document.createElement('div');
            div.textContent = day;
            div.style.width = '28px';
            div.style.height = '28px';
            div.style.border = '1px solid #eee';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.justifyContent = 'center';
            div.style.fontSize = '0.8rem';
            div.style.cursor = 'pointer';
            div.classList.add('cal-day');
            div.dataset.date = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

            // Подсветка сегодня
            const today = new Date();
            if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {
                div.style.backgroundColor = '#00C8B3';
                div.style.color = 'white';
                div.style.fontWeight = 'bold';
            }

            // Подсветка выбранной даты
            if (div.dataset.date === currentDate) {
                div.style.backgroundColor = '#e0f7fa';
            }

            div.addEventListener('click', () => {
                document.querySelectorAll('#cal-days .cal-day').forEach(d => d.style.backgroundColor = '');
                div.style.backgroundColor = '#e0f7fa';
                document.getElementById('selected-date').value = div.dataset.date;
                currentDate = div.dataset.date; // ✅ Сохраняем выбранную дату
            });

            container.appendChild(div);
        }
    }

    // Открытие модального окна
    triggerBtn?.addEventListener('click', function() {
        generateCalendar(currentYear, currentMonth);
        calendarModal.show();
    });

    // Применить дату
    document.getElementById('apply-calendar')?.addEventListener('click', function() {
        const date = document.getElementById('selected-date').value;
        if (!date) return;
        currentDate = date; // ✅ Сохраняем дату
        localStorage.setItem('selectedDate', currentDate); // ✅ Сохраняем в localStorage
        loadSchedule(date, '');
        calendarModal.hide();
    });

    // Загрузка расписания
    async function loadSchedule(date, doctorId) {
        try {
            const res = await fetch(`/api/schedule/?date=${date}${doctorId ? '&doctor_id=' + doctorId : ''}`);
            if (!res.ok) throw new Error('Ошибка загрузки');

            const data = await res.json();

            const [y, m, d] = date.split('-');
            const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                            'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
            const newTitle = `Записи на ${d}.${months[parseInt(m)-1]}.${y}`;
            const sectionTitle = document.getElementById('section-title');
            sectionTitle.innerHTML = newTitle;
            sectionTitle.innerHTML += `
                <button id="add-btn" class="btn btn-sm btn-success ms-2">+</button>
                <button id="calendar-trigger" class="btn btn-sm btn-outline-secondary ms-1">📅</button>
            `;
            setupEventListeners();

            // Обновляем колонки
            updateSection('scheduled', data.scheduled || []);
            updateSection('waiting', data.waiting || []);
            updateSection('active', data.active || []);
            updateSection('completed', data.completed || []);

            // Инициализация Drag & Drop
            setupDragAndDrop();

        } catch (e) {
            alert('Ошибка: ' + e.message);
        }
    }

    function updateSection(section, items) {
        const container = document.getElementById(`${section}-list`);
        const countEl = document.getElementById(`${section}-count`);

        if (!container) return;

        // ✅ Сортируем по времени (если есть поле time)
        const sortedItems = [...items].sort((a, b) => {
            // Если есть время в формате HH:MM - сортируем по нему
            if (a.time && b.time) {
                return a.time.localeCompare(b.time);
            }
            return 0;
        });

        container.innerHTML = sortedItems.length > 0
            ? sortedItems.map(i => `
                <div class="patient-card" draggable="true" data-id="${i.id}">
                    ${i.patient_name} ${i.time || ''} вр ${i.doctor_name}
                </div>
              `).join('')
            : '<p>Нет записей</p>';

        if (countEl) countEl.textContent = sortedItems.length;

        // Сделать карточки перетаскиваемыми
        document.querySelectorAll(`#${section}-list .patient-card`).forEach(card => {
            card.addEventListener('dragstart', e => {
                e.dataTransfer.setData('text/plain', card.dataset.id);
            });
        });
    }

    function setupEventListeners() {
        // Живое привязывание обработчиков
        document.getElementById('add-btn')?.addEventListener('click', () => {
            openAddPatientAndAppointmentModal();
        });

        document.getElementById('calendar-trigger')?.addEventListener('click', function() {
            generateCalendar(currentYear, currentMonth);
            calendarModal.show();
        });
    }

    // ✅ Drag & Drop (без reload)
    function setupDragAndDrop() {
        const columns = document.querySelectorAll('.column');
        columns.forEach(col => {
            col.addEventListener('dragover', e => {
                e.preventDefault();
                col.classList.add('drag-over');
            });

            col.addEventListener('dragleave', e => {
                col.classList.remove('drag-over');
            });

            col.addEventListener('drop', async e => {
                e.preventDefault();
                col.classList.remove('drag-over');

                const appointmentId = e.dataTransfer.getData('text/plain');
                const newStatus = col.dataset.status; // scheduled, waiting, active, completed

                try {
                    const res = await fetch(`/api/appointments/${appointmentId}/update-status/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        },
                        body: JSON.stringify({ status: newStatus })
                    });

                    if (res.ok) {
                        // ✅ Не перезагружаем страницу, а обновляем расписание
                        loadSchedule(currentDate, ''); // ✅ Обновляем с текущей датой
                    } else {
                        const err = await res.json();
                        alert('Ошибка изменения статуса: ' + err.error);
                    }
                } catch (err) {
                    alert('Ошибка сети');
                }
            });
        });
    }

    // ✅ Открытие нового модального окна
    function openAddPatientAndAppointmentModal() {
        resetModal();
        new bootstrap.Modal(document.getElementById('addPatientAndAppointmentModal')).show();
    }

    // ✅ Сброс формы
    function resetModal() {
        selectedPatientId = null;
        document.getElementById('search-patient-input-modal').value = '';
        document.getElementById('search-results-modal').innerHTML = '';
        document.getElementById('selected-patient-info').innerHTML = '';
        document.getElementById('create-patient-form-modal').classList.add('d-none');
        document.getElementById('appointment-section').classList.add('d-none');
    }

    // ✅ Поиск пациента в модальном окне
    document.getElementById('search-patient-input-modal')?.addEventListener('input', handlePatientSearchInModal);

    async function handlePatientSearchInModal(e) {
        const query = e.target.value;
        if (query.length < 2) {
            document.getElementById('search-results-modal').innerHTML = '';
            return;
        }

        try {
            const res = await fetch(`/api/patients/search/?q=${encodeURIComponent(query)}`);
            const patients = await res.json();

            const resultsHtml = patients.map(p => `
                <div class="list-group-item list-group-item-action"
                     onclick="selectPatientFromModal(${p.id}, '${p.full_name}', '${p.phone}')">
                    ${p.full_name} (${p.phone})
                </div>
            `).join('');

            document.getElementById('search-results-modal').innerHTML = resultsHtml || '<div class="list-group-item">Не найдено</div>';
        } catch (err) {
            console.error('Ошибка поиска:', err);
        }
    }

    window.selectPatientFromModal = function(id, name, phone) {
        selectedPatientId = id;
        document.getElementById('selected-patient-info').innerHTML = `
            <div class="alert alert-success">
                Выбран пациент: <strong>${name}</strong> (${phone})
            </div>
        `;
        document.getElementById('appointment-section').classList.remove('d-none');
        loadDoctorsForAppointment();
    };

    // ✅ Показать форму создания пациента
    document.getElementById('show-create-form-btn')?.addEventListener('click', () => {
        document.getElementById('create-patient-form-modal').classList.remove('d-none');
        document.getElementById('appointment-section').classList.remove('d-none');
        loadDoctorsForAppointment();
    });

    // ✅ Создать нового пациента
    document.getElementById('create-patient-form-modal-inner')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        // Преобразуем FormData в объект
        const data = Object.fromEntries(formData.entries());

        try {
            const res = await fetch('/api/patients/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                const patient = await res.json();
                selectedPatientId = patient.id;

                document.getElementById('selected-patient-info').innerHTML = `
                    <div class="alert alert-success">
                        Создан пациент: <strong>${patient.full_name}</strong> (${patient.phone})
                    </div>
                `;
            } else {
                const err = await res.json();
                alert('Ошибка: ' + err.error);
            }
        } catch (err) {
            alert('Ошибка сети');
        }
    });

    // ✅ Загрузка врачей
    async function loadDoctorsForAppointment() {
        try {
            const res = await fetch('/api/personnel/doctors/');
            const doctors = await res.json();

            const select = document.getElementById('doctor-select-modal');
            select.innerHTML = '';

            doctors.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.full_name;
                select.appendChild(option);
            });

        } catch (err) {
            console.error('Ошибка загрузки врачей:', err);
        }
    }

    // ✅ Создать запись
    document.getElementById('create-appointment-btn')?.addEventListener('click', async () => {
        const doctorSelect = document.getElementById('doctor-select-modal');
        const datetimeInput = document.getElementById('datetime-input-modal');
        const durationSelect = document.getElementById('duration-select-modal');

        const doctorId = doctorSelect ? doctorSelect.value : '';
        const datetime = datetimeInput ? datetimeInput.value : '';
        const duration = durationSelect ? parseInt(durationSelect.value) : 15; // по умолчанию 15

        // Проверяем, есть ли форма создания пациента
        const createPatientForm = document.getElementById('create-patient-form-modal-inner');
        const isCreatingPatient = !document.getElementById('create-patient-form-modal').classList.contains('d-none');

        if (isCreatingPatient) {
            // Если создаём нового пациента
            if (!doctorId || !datetime) {
                alert('Выберите врача и время');
                return;
            }

            const formData = new FormData(createPatientForm);
            const patientData = Object.fromEntries(formData.entries());

            try {
                // 1. Создаём пациента
                const patientRes = await fetch('/api/patients/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(patientData)
                });

                if (!patientRes.ok) {
                    const err = await patientRes.json();
                    alert('Ошибка создания пациента: ' + err.error);
                    return;
                }

                const patient = await patientRes.json();

                // 2. Создаём запись
                const appointmentRes = await fetch('/api/appointments/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        patient_id: patient.id,
                        doctor_id: doctorId,
                        datetime: datetime,
                        status: 'scheduled',
                        duration: duration  // ✅ Передаём выбранную длительность
                    })
                });

                if (appointmentRes.ok) {
                    alert('Пациент и запись созданы!');
                    new bootstrap.Modal(document.getElementById('addPatientAndAppointmentModal')).hide();
                    loadSchedule(currentDate, ''); // ✅ Обновляем расписание с текущей датой
                } else {
                    const err = await appointmentRes.json();
                    alert('Ошибка создания записи: ' + err.error);
                }
            } catch (err) {
                alert('Ошибка сети: ' + err.message);
            }
        } else {
            // Если выбран существующий пациент
            if (!selectedPatientId || !doctorId || !datetime) {
                alert('Заполните все поля');
                return;
            }

            try {
                const res = await fetch('/api/appointments/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        patient_id: selectedPatientId,
                        doctor_id: doctorId,
                        datetime: datetime,
                        status: 'scheduled',
                        duration: duration  // ✅ Передаём выбранную длительность
                    })
                });

                if (res.ok) {
                    alert('Запись создана!');
                    new bootstrap.Modal(document.getElementById('addPatientAndAppointmentModal')).hide();
                    loadSchedule(currentDate, ''); // ✅ Обновляем расписание с текущей датой
                } else {
                    const err = await res.json();
                    alert('Ошибка: ' + err.error);
                }
            } catch (err) {
                alert('Ошибка сети: ' + err.message);
            }
        }
    });

    // ✅ Функция получения токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // скрытое поле для выбранной даты
    if (!document.getElementById('selected-date')) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.id = 'selected-date';
        document.body.appendChild(input);
    }

    // ✅ Устанавливаем текущую дату в hidden input
    document.getElementById('selected-date').value = currentDate;

    // Инициализация событий
    setupEventListeners();

    // ✅ Загружаем расписание для текущей даты при старте
    loadSchedule(currentDate, '');
});