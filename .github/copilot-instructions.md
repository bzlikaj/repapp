# Copilot Instructions - Calendario di Reperibilità 2026

## Descrizione del Progetto

Sistema Python per la generazione automatica di un calendario di reperibilità lavorativa per 9 tecnici con rotazione equa e vincoli complessi di blocco temporale.

## Obiettivi

- Generare un calendario PDF annuale (2026) con assegnazioni di reperibilità
- Garantire rotazione equa tra 9 tecnici
- Implementare regola rigida dei 7 giorni di blocco per turni importanti
- Validare automaticamente tutte le regole
- Fornire statistiche e report

## Regole Principali

1. **Tre tipologie di reperibilità**:
   - Feriale (lunedì-venerdì): 1 giorno per volta
   - Weekend (sabato+domenica): assegnato insieme
   - Festivo: giorni festivi nazionali

2. **Regola fondamentale dei 7 giorni**:
   - Weekend/festivi causano blocco di 7 giorni prima e dopo
   - Durante blocco: nessuna assegnazione possibile
   - Validazione rigorosa

3. **Rotazione equa**:
   - 9 tecnici in ordine fisso
   - Se tecnico non disponibile: salta al prossimo
   - Distribuzione bilanciata (~38-42 turni per tecnico)

4. **Vincoli specifici**:
   - 1 gennaio obbligatoriamente a Dardha (solo per il 2026)
   - Weekend non assegnati su giorni festivi
   - Ogni data assegnata a una sola persona

## Struttura del Codice

```
src/
├── calendar_generator.py    # Logica principale
├── pdf_generator.py         # Generazione PDF
└── validatore.py           # Validazione regole

main.py                      # Entry point
test_calendario.py           # Suite di test
config.json                  # Configurazione
```

## Come Usare

```bash
# Installa dipendenze
pip install -r requirements.txt

# Genera calendario
python main.py

# Esegui test
python test_calendario.py
```

## Output Atteso

- PDF: 12 pagine, una per mese
- Validazione: tutte le regole devono passare
- Statistiche: distribuzione turni per tecnico

## Note di Sviluppo

- La differenza massima tra tecnici può essere ~4 turni dovuto ai vincoli rigidi
- La domenica è sempre assegnata allo stesso tecnico del sabato
- Il blocco per i weekend è da -7 giorni a +8 giorni (escludendo domenica e lunedì dal conteggio)

## Personalizzazione

Modificare in `calendar_generator.py`:
- `TECNICI`: lista dei 9 tecnici
- `FESTIVI_2026`: lista festività
- `GIORNI_BLOCCO`: estensione blocco (attualmente 7)

