// static/js/main.js

// Загрузка расписания по врачу или дате
async function loadSchedule(date = null, doctorId = null) {
    let url = '/api/schedule/';
    const params = [];
    if (date) params.push(`date=${date}`);
    if (doctorId) params.push(`doctor=${doctorId}`);
    if (params.length) url += '?' + params.join('&');

    const res = await fetch(url);
    const data = await res.json();

    // Обновление колонок (адаптируй под твой шаблон)
    const scheduledEl = document.querySelector('[data-section="scheduled"]');
    if (scheduledEl) {
        scheduledEl.innerHTML = data.scheduled.map(a => `
            <div class="patient-card">${a.patient_name} ${a.time}</div>
        `).join('');
    }
}

// Поиск пациентов
document.getElementById('search-patient-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = e.target.elements.full_name.value;
    const res = await fetch(`/api/patients/search/?q=${encodeURIComponent(q)}`);
    const patients = await res.json();
    const resultsEl = document.getElementById('search-results');
    resultsEl.innerHTML = patients.map(p => `
        <div class="card mb-2">
            <div class="card-body">
                <h6>${p.name}</h6>
                <p>${p.phone}</p>
                <button class="btn btn-sm btn-primary edit-patient" data-id="${p.id}">Изменить</button>
                <button class="btn btn-sm btn-danger delete-patient" data-id="${p.id}">Удалить</button>
            </div>
        </div>
    `).join('');
});