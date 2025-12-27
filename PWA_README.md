# 📅 PWA - Calendario di Reperibilità 2026

Progressive Web App per gestire il calendario di reperibilità con tecnici e aiutanti.

## 🚀 Come Avviare

### 1️⃣ Avvia il server Flask

```bash
python app_pwa.py
```

Il server partirà su: **http://localhost:5000**

### 2️⃣ Accedi all'app dal browser

Apri il browser e vai a: **http://localhost:5000**

L'app è accessibile da:
- 💻 Windows (browser)
- 📱 Android (PWA installabile)
- 🍎 iPhone (PWA via browser)

## 📋 Funzionalità

### 📊 Tab Calendario
- Visualizza il calendario mensile con assegnazioni
- Scorri tra i mesi di gennaio-dicembre 2026
- Colori: Rosso (festivi), Blu (weekend), Grigio (feriali)
- Statistiche: numero turni per tecnico
- Rigenera il calendario con le configurazioni attuali

### 👥 Tab Tecnici
- Aggiungi nuovi tecnici
- Rimuovi tecnici dal roster
- Lista dinamica e aggiornabile
- Minimo 1 tecnico obbligatorio

### 🤝 Tab Aiutanti
- Assegna aiutanti per ogni giorno della settimana
- Es: Sabato -> Likaj reperibile + Aiutante1
- Configurazione salvata automaticamente
- Aiutanti facoltativi

### 💾 Tab Esporta
- **PDF**: Calendario stampabile con layout mensile
- **Excel**: Foglio di calcolo modificabile

## 🔧 Struttura del Progetto

```
repapp/
├── app_pwa.py              # Backend Flask
├── pwa/                    # Frontend PWA
│   ├── index.html         # Interfaccia principale
│   ├── app.js             # Logica JavaScript
│   ├── styles.css         # Styling
│   ├── manifest.json      # Config PWA
│   └── service-worker.js  # Offline support
├── src/
│   ├── calendar_generator.py
│   ├── pdf_generator.py
│   ├── excel_generator.py
│   └── validatore.py
└── pwa_data/              # Dati persistenti
    └── config.json        # Configurazione salvata
```

## 🎯 Workflow Tipico

1. **Accedi all'app** → http://localhost:5000
2. **Vai al tab Tecnici** → Aggiungi/rimuovi persone
3. **Vai al tab Aiutanti** → Configura aiutanti per giorni
4. **Torna al tab Calendario** → Clicca "Rigenera Calendario"
5. **Vai al tab Esporta** → Scarica PDF o Excel

## 📱 Installa come App (PWA)

### Su Android:
1. Apri Chrome
2. Vai a http://localhost:5000
3. Tocca il menu (⋮) → "Installa l'app"
4. Conferma → L'app sarà nel launcher

### Su Windows:
1. Apri Edge/Chrome
2. Vai a http://localhost:5000
3. Clicca sull'icona "Installa" nella barra
4. Conferma → L'app sarà nel menu Start

### Su iPhone:
1. Apri Safari
2. Vai a http://localhost:5000
3. Clicca Condividi → "Aggiungi a Home"
4. L'app sarà nella Home Screen

## 🔄 API Endpoints

### Config
- `GET /api/config` - Leggi configurazione
- `POST /api/config` - Salva configurazione

### Tecnici
- `GET /api/tecnici` - Lista tecnici
- `POST /api/tecnici` - Aggiungi tecnico
- `DELETE /api/tecnici/<nome>` - Rimuovi tecnico

### Aiutanti
- `GET /api/aiutanti` - Leggi aiutanti
- `POST /api/aiutanti` - Salva aiutanti

### Calendario
- `GET /api/calendario` - Leggi calendario
- `POST /api/calendario/rigenerare` - Rigenera

### Export
- `GET /api/exports/pdf` - Scarica PDF
- `GET /api/exports/excel` - Scarica Excel

## 🛠️ Dipendenze

```
flask==2.3.0
flask-cors==4.0.0
openpyxl==3.10.0
reportlab==4.0.9
python-dateutil==2.8.2
```

Installa con:
```bash
pip install -r requirements.txt
```

## 🌍 Mettere l'app online (Internet)

Puoi pubblicarla su un hosting (es. Render) e usarla ovunque.

### Render (consigliato)

1. Carica questo progetto su GitHub.
2. Su Render: **New → Web Service** e collega il repository.
3. Imposta:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn wsgi:app`
4. Aggiungi un **Persistent Disk** (es. mount path `/data`).
5. Aggiungi variabile d'ambiente:
  - `REPAPP_DATA_DIR=/data`

Nota: senza Persistent Disk, le modifiche (tecnici/ferie/config) potrebbero perdersi ad ogni redeploy.

### Sicurezza (modalità prova)

Al momento non c'è login: chiunque conosca l'URL può vedere/modificare i dati.
Per una prova va bene, ma per uso reale conviene aggiungere almeno una password/token.

## 📦 App installabili (Windows + Android)

Se vuoi un file da scaricare e installare direttamente:
- Windows: installer `.exe` (wrapper desktop)
- Android: `.apk` (wrapper Android)

I progetti di build sono già pronti:
- `desktop_windows/`
- `mobile_android/`

Guida: vedi `docs/INSTALLABILI_WINDOWS_ANDROID.md`.

## 💡 Suggerimenti

- **Offline**: L'app mantiene i dati in cache (funziona offline)
- **Dati**: Salvati in `pwa_data/config.json`
- **Responsive**: UI ottimizzata per mobile e desktop
- **PWA**: Installabile come app nativa

## ⚙️ Configurazione Predefinita

Nel file `pwa_data/config.json`:
```json
{
  "tecnici": [
    "Likaj", "Ferraris", "Zanotto", "Casazza", "Mancin",
    "Dardha", "Franchini", "Giraldin", "Terazzi"
  ],
  "aiutanti_per_giorno": {
    "lunedi": "",
    "martedi": "",
    ...
    "sabato": "aiutante_1",
    "domenica": "aiutante_1"
  },
  "anno": 2026
}
```

## 🐛 Troubleshooting

### App non si carica
- Verifica che Flask stia girando: `python app_pwa.py`
- Controlla la console del browser (F12)
- Assicurati che la porta 5000 sia libera

### Export non funziona
- Verifica che i file PDF/Excel vengono generati in `pwa_data/`
- Controlla i permessi di scrittura della cartella

### PWA non si installa
- Usa Chrome/Edge/Chromium
- L'app deve essere servita da HTTPS (o localhost)
- Attendi qualche secondo dopo aver aperto la pagina

## 📝 Note

- Il calendario si rigenera automaticamente dopo modifiche
- I dati sono persistenti (salvati su disco)
- L'app funziona anche offline per le pagine in cache
- Supporta sia mobile che desktop
