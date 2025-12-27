# Deploy online (Render)

Questi passi ti danno un link pubblico (HTTPS) in pochi minuti.

## Prerequisiti

- Account Render
- Repository GitHub con questo progetto (Render fa deploy dal repo)

## Passi (veloci)

1. **Carica il progetto su GitHub**
   - Crea un nuovo repo su GitHub
   - Copia dentro il contenuto della cartella `repapp/`

2. **Crea il servizio su Render**
   - Render → **New** → **Blueprint**
   - Seleziona il repo GitHub
   - Render rileverà `render.yaml` e configurerà tutto automaticamente

3. **Apri il link**
   - A deploy completato, Render ti mostrerà l’URL del servizio
   - Apri l’URL: l’app PWA è già servita dal backend

## Dati persistenti (config/ferie/stati rotazione)

- Render monta un disco su `/data`.
- L’app usa la variabile `REPAPP_DATA_DIR=/data` (già configurata in `render.yaml`).
- In questo modo `pwa_data/config.json` e gli export rimangono persistenti tra riavvii e deploy.

## Aggiornamenti

- Ogni push su GitHub fa partire un nuovo deploy automatico.

## Note

- Se ti serve un dominio personalizzato, puoi aggiungerlo dal pannello Render.
