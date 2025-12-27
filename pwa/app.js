/* ============================================
   APP PWA - JAVASCRIPT LOGIC
   ============================================ */

const API_BASE = `${window.location.origin}/api`;
let currentCalendario = null;
let currentConfig = null;

const STORAGE_SELECTED_YEAR_KEY = 'repapp_selected_year';

function getSelectedYear() {
    const el = document.getElementById('year-input');
    if (!el) return 2026;
    const y = parseInt(el.value, 10);
    return Number.isFinite(y) ? y : 2026;
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', async () => {
    console.log('App avviato');
    
    // Setup tabs
    setupTabs();

    // Load initial data
    await loadConfig();

    // Setup anno calendario (dopo loadConfig per poter usare config.anno)
    const yearInput = document.getElementById('year-input');
    if (yearInput) {
        const saved = localStorage.getItem(STORAGE_SELECTED_YEAR_KEY);
        const cfgYear = (currentConfig && Number.isFinite(parseInt(currentConfig.anno, 10)))
            ? parseInt(currentConfig.anno, 10)
            : null;
        const fallbackYear = Math.max(2026, new Date().getFullYear());

        if (saved && String(saved).trim()) {
            yearInput.value = String(saved);
        } else if (cfgYear) {
            yearInput.value = String(cfgYear);
        } else {
            yearInput.value = String(fallbackYear);
        }

        yearInput.addEventListener('change', async () => {
            localStorage.setItem(STORAGE_SELECTED_YEAR_KEY, String(getSelectedYear()));
            await loadCalendario();
        });
    }

    await loadCalendario();
    await loadTecnici();
    await loadAiutanti();
    await loadFerie();
    
    // Setup event listeners
    setupEventListeners();
});

// ============ TAB NAVIGATION ============
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class
            btn.classList.add('active');
            document.getElementById(tab).classList.add('active');
        });
    });
}

// ============ EVENT LISTENERS ============
function setupEventListeners() {
    // Calendario
    document.getElementById('month-select').addEventListener('change', renderCalendar);
    document.getElementById('regenerate-calendar').addEventListener('click', regenerateCalendario);
    
    // Tecnici
    document.getElementById('add-tecnico').addEventListener('click', addTecnico);
    document.getElementById('new-tecnico').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addTecnico();
    });
    
    // Aiutanti
    document.getElementById('add-aiutante').addEventListener('click', addAiutante);
    document.getElementById('new-aiutante').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addAiutante();
    });
    document.getElementById('save-date-aiutanti').addEventListener('click', saveDateAiutanti);
    document.querySelectorAll('input[name="mode-aiutanti"]').forEach(r => {
        r.addEventListener('change', updateModeAiutantiUI);
    });
    
    // Export
    document.getElementById('export-pdf').addEventListener('click', exportPDF);
    document.getElementById('export-excel').addEventListener('click', exportExcel);

    // Ferie
    document.getElementById('add-ferie').addEventListener('click', addFerie);
    document.querySelectorAll('input[name="ferie-tipo"]').forEach(r => {
        r.addEventListener('change', renderFerieTecniciSelect);
    });
}

// ============ FERIE ============
async function loadFerie() {
    // Popola dropdown tecnici dalla config corrente
    renderFerieTecniciSelect();

    const data = await apiCall('/ferie');
    if (data) {
        renderFerie(data.ferie || []);
    }
}

function renderFerieTecniciSelect() {
    const select = document.getElementById('ferie-tecnico');
    if (!select) return;
    const tipo = document.querySelector('input[name="ferie-tipo"]:checked')?.value || 'tecnico';
    const tecnici = (currentConfig && Array.isArray(currentConfig.tecnici)) ? currentConfig.tecnici : [];
    const aiutanti = (currentConfig && Array.isArray(currentConfig.aiutanti)) ? currentConfig.aiutanti : [];
    const persone = (tipo === 'aiutante') ? aiutanti : tecnici;
    select.innerHTML = '';
    persone.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        select.appendChild(opt);
    });
}

function renderFerie(ferie) {
    const lista = document.getElementById('ferie-lista');
    lista.innerHTML = '';

    if (!ferie || ferie.length === 0) {
        lista.innerHTML = '<li style="color:#999; text-align:center; padding:20px;">Nessuna ferie inserita</li>';
        return;
    }

    ferie.forEach(f => {
        const item = document.createElement('li');
        item.className = 'tecnico-item';
        const nome = f.nome || '';
        const dal = f.dal || '';
        const al = f.al || '';
        const tipo = (f.tipo || 'tecnico');
        const id = f.id || '';
        item.innerHTML = `
            <span class="tecnico-name">${tipo}: ${nome} — ${dal} → ${al}</span>
            <button class="btn-remove" onclick="removeFerie('${id}','${dal}','${al}')">Rimuovi</button>
        `;
        lista.appendChild(item);
    });
}

async function rigeneraCalendarioParziale(dal, al) {
    if (!dal || !al) return;
    const result = await apiCall('/calendario/rigenerare-parziale', 'POST', { dal, al });
    if (result) {
        currentCalendario = result;
        renderCalendar();
        renderStats();
    }
}

async function addFerie() {
    const tipo = document.querySelector('input[name="ferie-tipo"]:checked')?.value || 'tecnico';
    const nome = document.getElementById('ferie-tecnico').value;
    const dal = document.getElementById('ferie-dal').value;
    const al = document.getElementById('ferie-al').value;

    if (!nome || !dal || !al) {
        showToast('Seleziona tecnico e date (dal/al)', 'error');
        return;
    }

    showLoading(true);
    const result = await apiCall('/ferie', 'POST', { tipo, nome, dal, al });
    if (result) {
        showToast('Ferie aggiunte', 'success');
        renderFerie(result.ferie || []);
        await rigeneraCalendarioParziale(dal, al);
    }
    showLoading(false);
}

async function removeFerie(id, dal, al) {
    if (!id) return;
    if (!confirm('Rimuovere questo periodo di ferie?')) return;

    showLoading(true);
    const result = await apiCall(`/ferie/${id}`, 'DELETE');
    if (result) {
        showToast('Ferie rimosse', 'success');
        renderFerie(result.ferie || []);
        await rigeneraCalendarioParziale(dal, al);
    }
    showLoading(false);
}

// ============ API CALLS ============
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(`Errore: ${error.message}`, 'error');
        return null;
    }
}

// ============ LOAD CONFIG ============
async function loadConfig() {
    showLoading(true);
    const config = await apiCall('/config');
    if (config) {
        currentConfig = config;
    }
    showLoading(false);
}

// ============ CALENDARIO ============
async function loadCalendario() {
    showLoading(true);
    const anno = getSelectedYear();
    const data = await apiCall(`/calendario?anno=${encodeURIComponent(String(anno))}`);
    if (data) {
        currentCalendario = data;
        renderCalendar();
        renderStats();
    }
    showLoading(false);
}

async function regenerateCalendario() {
    showLoading(true);
    const anno = getSelectedYear();
    const result = await apiCall(`/calendario/rigenerare?anno=${encodeURIComponent(String(anno))}`, 'POST');
    if (result) {
        showToast('✅ Calendario rigenerato', 'success');
        await loadCalendario();
    }
    showLoading(false);
}

function renderCalendar() {
    if (!currentCalendario) return;
    
    const mese = parseInt(document.getElementById('month-select').value);
    const nomiMesi = [
        'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
        'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
    ];
    
    const container = document.getElementById('month-calendar');
    container.innerHTML = '';
    
    // Header giorni della settimana
    const giorni = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'];
    giorni.forEach(g => {
        const header = document.createElement('div');
        header.className = 'day-cell header';
        header.textContent = g;
        header.style.fontWeight = 'bold';
        header.style.background = '#2C3E50';
        header.style.color = 'white';
        container.appendChild(header);
    });
    
    // Calcola primo e ultimo giorno del mese
    const year = (currentCalendario && currentCalendario.anno)
        ? parseInt(currentCalendario.anno, 10)
        : getSelectedYear();
    const firstDay = new Date(year, mese - 1, 1);
    const lastDay = new Date(year, mese, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1; // 0=lunedì
    
    // Aggiungi celle vuote all'inizio
    for (let i = 0; i < startingDayOfWeek; i++) {
        const empty = document.createElement('div');
        empty.className = 'day-cell';
        empty.style.background = 'transparent';
        container.appendChild(empty);
    }
    
    // Aggiungi i giorni del mese
    for (let giorno = 1; giorno <= daysInMonth; giorno++) {
        const dataStr = `${year}-${String(mese).padStart(2, '0')}-${String(giorno).padStart(2, '0')}`;
        const assegnazione = currentCalendario.assegnazioni[dataStr];
        
        const dayCell = document.createElement('div');
        dayCell.className = 'day-cell';
        
        if (assegnazione) {
            const [tecnico, tipo, aiutante] = assegnazione;
            dayCell.classList.add(tipo);
            let html = `<div class="day-number">${giorno}</div><div class="day-tecnico">${tecnico}</div>`;
            if (aiutante) {
                html += `<div class="day-aiutante">+ ${aiutante}</div>`;
            }
            html += `<div class="day-type">${tipo}</div>`;
            dayCell.innerHTML = html;
        } else {
            dayCell.innerHTML = `<div class="day-number">${giorno}</div>`;
        }
        
        container.appendChild(dayCell);
    }
}

function renderStats() {
    if (!currentCalendario || !currentCalendario.statistiche) return;
    
    const container = document.getElementById('stats-table');
    container.innerHTML = '';
    
    const stats = currentCalendario.statistiche;
    const tecnici = Object.keys(stats).sort((a, b) => stats[b] - stats[a]);
    
    tecnici.forEach(tecnico => {
        const count = stats[tecnico];
        const item = document.createElement('div');
        item.className = 'stat-item';
        item.innerHTML = `
            <div class="stat-name">${tecnico}</div>
            <div class="stat-value">${count}</div>
        `;
        container.appendChild(item);
    });
}

// ============ TECNICI ============
async function loadTecnici() {
    const data = await apiCall('/tecnici');
    if (data) {
        if (currentConfig && Array.isArray(data.tecnici)) {
            currentConfig.tecnici = data.tecnici;
        }
        renderTecnici(data.tecnici);
        renderFerieTecniciSelect();
    }
}

function renderTecnici(tecnici) {
    const lista = document.getElementById('tecnici-lista');
    lista.innerHTML = '';
    
    tecnici.forEach(tecnico => {
        const item = document.createElement('li');
        item.className = 'tecnico-item';
        item.innerHTML = `
            <span class="tecnico-name">${tecnico}</span>
            <button class="btn-remove" onclick="removeTecnico('${tecnico}')">❌ Rimuovi</button>
        `;
        lista.appendChild(item);
    });
}

async function addTecnico() {
    const input = document.getElementById('new-tecnico');
    const nome = input.value.trim();
    
    if (!nome) {
        showToast('Inserisci il nome del tecnico', 'error');
        return;
    }
    
    showLoading(true);
    const result = await apiCall('/tecnici', 'POST', { nome });
    if (result) {
        showToast(`✅ ${nome} aggiunto`, 'success');
        input.value = '';
        await loadTecnici();
    }
    showLoading(false);
}

async function removeTecnico(nome) {
    if (!confirm(`Rimuovere ${nome}?`)) return;
    
    showLoading(true);
    const result = await apiCall(`/tecnici/${nome}`, 'DELETE');
    if (result) {
        showToast(`✅ ${nome} rimosso`, 'success');
        await loadTecnici();
    }
    showLoading(false);
}
// ============ AIUTANTI ============
async function loadAiutanti() {
    const data = await apiCall('/aiutanti');
    if (data) {
        renderAiutanti(data.aiutanti);
        renderPianificazioneAiutanti(
            data.date_aiutanti || [],
            data.anno || getSelectedYear() || 2026,
            data.giorni_settimana_aiutanti || []
        );
    }
}

function renderAiutanti(aiutanti) {
    const lista = document.getElementById('aiutanti-lista');
    lista.innerHTML = '';
    
    if (aiutanti.length === 0) {
        lista.innerHTML = '<li style="color: #999; text-align: center; padding: 20px;">Nessun aiutante aggiunto</li>';
        return;
    }
    
    aiutanti.forEach(aiutante => {
        const item = document.createElement('li');
        item.className = 'tecnico-item';
        item.innerHTML = `
            <span class="tecnico-name">${aiutante}</span>
            <button class="btn-remove" onclick="removeAiutante('${aiutante}')">Rimuovi</button>
        `;
        lista.appendChild(item);
    });
}

function renderPianificazioneAiutanti(dateAiutanti, anno, giorniSettimanaSel) {
    const mesiSet = new Set();
    const giorniSet = new Set();

    (dateAiutanti || []).forEach(d => {
        const parts = String(d).split('-');
        if (parts.length !== 3) return;
        const m = parseInt(parts[1], 10);
        const g = parseInt(parts[2], 10);
        if (!Number.isNaN(m)) mesiSet.add(m);
        if (!Number.isNaN(g)) giorniSet.add(g);
    });

    renderMesiCheckbox(mesiSet);
    renderSettimanaCheckbox(new Set((giorniSettimanaSel || []).map(n => parseInt(n, 10)).filter(n => !Number.isNaN(n))));
    renderGiorniMeseCheckbox(giorniSet);

    // Inferisci modalità (all vs specific) in modo semplice
    const modeAll = mesiSet.size > 0 && Array.from(mesiSet).every(m => isFullMonthSelected(dateAiutanti, anno, m));
    setModeAiutanti(modeAll ? 'all' : 'specific');
    updateModeAiutantiUI();

    renderDateAiutantiSummary(dateAiutanti);
}

function renderSettimanaCheckbox(selectedWeekSet) {
    const container = document.getElementById('settimana-checkbox');
    container.innerHTML = '';
    const items = [
        { n: 0, label: 'Lunedi' },
        { n: 1, label: 'Martedi' },
        { n: 2, label: 'Mercoledi' },
        { n: 3, label: 'Giovedi' },
        { n: 4, label: 'Venerdi' },
        { n: 5, label: 'Sabato' },
        { n: 6, label: 'Domenica' },
    ];

    items.forEach(it => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `dow-${it.n}`;
        checkbox.value = String(it.n);
        checkbox.checked = selectedWeekSet.has(it.n);

        const text = document.createElement('span');
        text.textContent = it.label;

        label.appendChild(checkbox);
        label.appendChild(text);
        container.appendChild(label);
    });
}

function renderMesiCheckbox(selectedMesiSet) {
    const container = document.getElementById('mesi-checkbox');
    container.innerHTML = '';
    const mesi = [
        'Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
        'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'
    ];
    mesi.forEach((nome, idx) => {
        const m = idx + 1;
        const label = document.createElement('label');
        label.className = 'checkbox-label';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `month-${m}`;
        checkbox.value = String(m);
        checkbox.checked = selectedMesiSet.has(m);

        const text = document.createElement('span');
        text.textContent = nome;

        label.appendChild(checkbox);
        label.appendChild(text);
        container.appendChild(label);
    });
}

function renderGiorniMeseCheckbox(selectedGiorniSet) {
    const container = document.getElementById('giorni-mese-checkbox');
    container.innerHTML = '';
    for (let day = 1; day <= 31; day++) {
        const label = document.createElement('label');
        label.className = 'checkbox-label';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `dom-${day}`;
        checkbox.value = String(day);
        checkbox.checked = selectedGiorniSet.has(day);

        const text = document.createElement('span');
        text.textContent = String(day);

        label.appendChild(checkbox);
        label.appendChild(text);
        container.appendChild(label);
    }
}

function isFullMonthSelected(dateAiutanti, anno, mese1based) {
    const set = new Set((dateAiutanti || []).filter(d => String(d).startsWith(String(anno) + '-' + String(mese1based).padStart(2, '0') + '-')));
    const dim = daysInMonth(anno, mese1based);
    return set.size === dim;
}

function daysInMonth(year, month1based) {
    return new Date(year, month1based, 0).getDate();
}

function setModeAiutanti(mode) {
    const el = document.querySelector(`input[name="mode-aiutanti"][value="${mode}"]`);
    if (el) el.checked = true;
}

function updateModeAiutantiUI() {
    const mode = document.querySelector('input[name="mode-aiutanti"]:checked')?.value || 'all';
    const wrapper = document.getElementById('giorni-mese-wrapper');
    wrapper.style.display = (mode === 'specific') ? 'block' : 'none';
}

function renderDateAiutantiSummary(dateAiutanti) {
    const box = document.getElementById('date-aiutanti-summary');
    const count = (dateAiutanti || []).length;
    if (count === 0) {
        box.innerHTML = '<strong>ℹ️</strong> Nessuna data selezionata per gli aiutanti.';
        return;
    }
    box.innerHTML = `<strong>✅</strong> Date selezionate: ${count}`;
}

async function addAiutante() {
    const input = document.getElementById('new-aiutante');
    const nome = input.value.trim();
    
    if (!nome) {
        showToast('Inserisci il nome dell\'aiutante', 'error');
        return;
    }
    
    showLoading(true);
    const result = await apiCall('/aiutanti', 'POST', { nome });
    if (result) {
        showToast(`Aiutante '${nome}' aggiunto`, 'success');
        input.value = '';
        await loadAiutanti();
    }
    showLoading(false);
}

async function removeAiutante(nome) {
    if (!confirm(`Rimuovere ${nome}?`)) return;
    
    showLoading(true);
    const result = await apiCall(`/aiutanti/${nome}`, 'DELETE');
    if (result) {
        showToast(`${nome} rimosso`, 'success');
        await loadAiutanti();
    }
    showLoading(false);
}

async function saveDateAiutanti() {
    const anno = getSelectedYear();
    let mesiSel = Array.from(document.querySelectorAll('#mesi-checkbox input[type="checkbox"]:checked'))
        .map(el => parseInt(el.value, 10))
        .filter(n => !Number.isNaN(n));

    // Se non selezioni mesi, interpreta come "tutto l'anno"
    if (mesiSel.length === 0) {
        mesiSel = Array.from({ length: 12 }, (_, i) => i + 1);
    }

    const mode = document.querySelector('input[name="mode-aiutanti"]:checked')?.value || 'all';
    const date_aiutanti = [];

    const giorni_settimana_aiutanti = Array.from(document.querySelectorAll('#settimana-checkbox input[type="checkbox"]:checked'))
        .map(el => parseInt(el.value, 10))
        .filter(n => !Number.isNaN(n));
    const weekFilterActive = giorni_settimana_aiutanti.length > 0;

    if (mesiSel.length > 0) {
        if (mode === 'all') {
            mesiSel.forEach(m => {
                const dim = daysInMonth(anno, m);
                for (let g = 1; g <= dim; g++) {
                    const dt = new Date(anno, m - 1, g);
                    // JS: getDay() => 0=Dom..6=Sab, convertiamo a 0=Lun..6=Dom
                    const dow = (dt.getDay() + 6) % 7;
                    if (!weekFilterActive || giorni_settimana_aiutanti.includes(dow)) {
                        date_aiutanti.push(`${anno}-${String(m).padStart(2, '0')}-${String(g).padStart(2, '0')}`);
                    }
                }
            });
        } else {
            const giorniSel = Array.from(document.querySelectorAll('#giorni-mese-checkbox input[type="checkbox"]:checked'))
                .map(el => parseInt(el.value, 10))
                .filter(n => !Number.isNaN(n));

            // UX: se hai selezionato SOLO il giorno della settimana (es. Sabato)
            // e la modalità è rimasta su "specific", interpreta come "all" filtrato.
            if (giorniSel.length === 0) {
                if (weekFilterActive) {
                    mesiSel.forEach(m => {
                        const dim = daysInMonth(anno, m);
                        for (let g = 1; g <= dim; g++) {
                            const dt = new Date(anno, m - 1, g);
                            const dow = (dt.getDay() + 6) % 7;
                            if (giorni_settimana_aiutanti.includes(dow)) {
                                date_aiutanti.push(`${anno}-${String(m).padStart(2, '0')}-${String(g).padStart(2, '0')}`);
                            }
                        }
                    });
                } else {
                    showToast('Seleziona almeno un giorno del mese', 'error');
                    showLoading(false);
                    return;
                }
            }

            if (giorniSel.length > 0) {
                mesiSel.forEach(m => {
                    const dim = daysInMonth(anno, m);
                    giorniSel.forEach(g => {
                        if (g >= 1 && g <= dim) {
                            const dt = new Date(anno, m - 1, g);
                            const dow = (dt.getDay() + 6) % 7;
                            if (!weekFilterActive || giorni_settimana_aiutanti.includes(dow)) {
                                date_aiutanti.push(`${anno}-${String(m).padStart(2, '0')}-${String(g).padStart(2, '0')}`);
                            }
                        }
                    });
                });
            }
        }
    }

    date_aiutanti.sort();

    showLoading(true);
    const result = await apiCall('/date-aiutanti', 'POST', { date_aiutanti, giorni_settimana_aiutanti });
    if (result) {
        showToast('Programmazione aiutanti salvata', 'success');
        renderDateAiutantiSummary(result.date_aiutanti || date_aiutanti);
    }
    showLoading(false);
}


// ============ EXPORT ============
async function exportPDF() {
    showLoading(true);
    const anno = getSelectedYear();
        window.location.href = `${API_BASE}/exports/pdf?anno=${encodeURIComponent(String(anno))}&ts=${Date.now()}`;
    setTimeout(() => showLoading(false), 2000);
}

async function exportExcel() {
    showLoading(true);
    const anno = getSelectedYear();
        window.location.href = `${API_BASE}/exports/excel?anno=${encodeURIComponent(String(anno))}&ts=${Date.now()}`;
    setTimeout(() => showLoading(false), 2000);
}

// ============ UTILITIES ============
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showLoading(show) {
    const loader = document.getElementById('loading');
    if (show) {
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}
