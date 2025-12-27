# Calendario di Reperibilità 2026

Generatore di calendario di reperibilità lavorativa per 9 tecnici con rotazione equa e vincoli di blocco temporale.

## Requisiti

- Python 3.8+
- reportlab (per generazione PDF)
- python-dateutil

## Installazione

```bash
pip install -r requirements.txt
```

## Utilizzo

```bash
python main.py
```

Genererà automaticamente il file PDF `calendario_reperibilita_2026.pdf` nella cartella `output/`.

## Link online (deploy rapido)

Per pubblicare l’app online con un URL condivisibile (HTTPS) usa Render:

- Config pronta: `render.yaml`
- Guida passo-passo: [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md)

### Output

- **PDF Calendario**: 12 pagine (una per ogni mese) con:
  - Date e giorni della settimana
  - Nome del tecnico assegnato
  - Tipo di reperibilità (F=Feriale, WE=Weekend, HH=Holiday/Festivo)
  - Colori distinti per tipologia

- **Report Validazione**: Controllo automatico delle regole
- **Statistiche**: Distribuzione equa dei turni

## Regole Implementate

### Personale (9 tecnici)
- Likaj
- Ferraris
- Zanotto
- Casazza
- Mancin
- Dardha
- Franchini
- Giraldin
- Terazzi

### Tipologie di Reperibilità

1. **Feriale** (F): Dal lunedì al venerdì
   - Un solo giorno per volta
   - Rotazione continua tra i 9 tecnici
   - Assegnato solo se il tecnico non è in blocco

2. **Weekend** (WE): Sabato + domenica insieme
   - Assegnato a una sola persona
   - Attiva il blocco di ±7 giorni
   - Distribuito a rotazione

3. **Festivo** (HH): Giorni festivi nazionali
   - Riguarda 11 festività italiane
   - Una festività per una sola persona
   - Attiva il blocco di ±7 giorni
  - Nel solo 2026, il 1 gennaio è assegnato obbligatoriamente a Dardha

### Festività 2026

- 1 gennaio - Capodanno (Dardha, solo 2026)
- 6 gennaio - Epifania
- 12 aprile - Pasqua
- 13 aprile - Lunedì dell'Angelo
- 25 aprile - Festa della Liberazione
- 1 maggio - Festa del Lavoro
- 2 giugno - Festa della Repubblica
- 15 agosto - Ferragosto
- 1 novembre - Ognissanti
- 8 dicembre - Immacolata Concezione
- 25 dicembre - Natale
- 26 dicembre - Santo Stefano

### Regola Principale dei 7 Giorni

La regola più importante del sistema:

Quando una persona è reperibile per:
- Un giorno **festivo**
- Un **weekend**

➡️ **NON può essere reperibile in alcun modo**:
- Nei **7 giorni precedenti**
- Nei **7 giorni successivi**

❌ Durante il blocco NON sono permessi:
- Giorni feriali
- Altri weekend
- Altri festivi

📌 In pratica: un turno "importante" genera **15 giorni consecutivi di esclusione totale** per quella persona.

### Rotazione Equa

- Le assegnazioni seguono l'ordine della lista del personale
- Se il turno "tocca" a una persona ma è in blocco:
  - ➡️ il sistema salta automaticamente alla persona successiva disponibile
- Nessuna forzatura: le regole hanno sempre priorità sulla rotazione
- Il sistema garantisce:
  - Distribuzione bilanciata nel tempo
  - Nessuna sovrapposizione ravvicinata
  - Recupero automatico se una persona viene saltata
  - Carico di reperibilità più sostenibile

## Struttura del Progetto

```
repapp/
├── src/
│   ├── calendar_generator.py       # Logica principale del calendario
│   ├── pdf_generator.py            # Generazione PDF con reportlab
│   └── validatore.py               # Validazione regole e reporting
├── main.py                          # Punto di ingresso
├── requirements.txt                 # Dipendenze Python
├── README.md                        # Questo file
└── output/                          # Cartella di output PDF
    └── calendario_reperibilita_2026.pdf
```

## Validazioni Implementate

Il sistema valida automaticamente:

1. ✅ **Regola dei 7 giorni**: Nessun conflitto di blocco temporale
2. ✅ **Assegnazione unica per data**: Ogni giorno assegnato a una sola persona
3. ✅ **Capodanno (solo 2026)**: Il 1 gennaio è assegnato a Dardha
4. ✅ **Equità turni**: Distribuzione bilanciata (tolleranza ±2 turni)

## Statistica di Distribuzione

La distribuzione media è di **~35 turni per tecnico** (328 giorni / 9 tecnici).

Con la tolleranza di ±2 turni, tutti i tecnici ricevono tra 33-37 turni, garantendo equità.

## Esecuzione

```bash
python main.py
```

Output previsto:
```
============================================================
GENERATORE CALENDARIO DI REPERIBILITÀ 2026
============================================================

1️⃣ Generazione calendario...
✅ Calendario generato con successo!

2️⃣ Validazione calendario...
============================================================
REPORT DI VALIDAZIONE CALENDARIO 2026
============================================================
✅ Regola 7 giorni: PASSATO
✅ Assegnazione unica per data: PASSATO
✅ Capodanno a Dardha (solo 2026): PASSATO
✅ Equità turni: PASSATO
============================================================
✅ TUTTE LE VALIDAZIONI PASSATE
============================================================

3️⃣ Statistiche assegnazioni...
4️⃣ Esempi di assegnazioni...
5️⃣ Generazione PDF...
✅ PDF generato con successo!
```

## Personalizzazione

Per modificare i parametri:

1. **Tecnici**: Modifica la lista `TECNICI` in `calendar_generator.py`
2. **Festività**: Modifica `get_festivi(anno)` in `calendar_generator.py`
3. **Giorni di blocco**: Modifica `GIORNI_BLOCCO` in `calendar_generator.py`
4. **Tecnico Capodanno**: Modifica nel metodo `genera_calendario()`

## Licenza

Progetto interno aziendale.

