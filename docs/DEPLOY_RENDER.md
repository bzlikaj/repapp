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

- **Piano Free:** i dischi persistenti non sono supportati. In questa configurazione l’app usa `REPAPP_DATA_DIR=/tmp/repapp-data`.
   - I dati (config/ferie/rotazioni/export) possono andare persi in caso di redeploy o reset dell’istanza.
- **Piani che supportano dischi:** puoi aggiungere un disk (es. mount `/data`) e impostare `REPAPP_DATA_DIR=/data` in `render.yaml` per avere persistenza.

## Aggiornamenti

- Ogni push su GitHub fa partire un nuovo deploy automatico.

## Note

- Se ti serve un dominio personalizzato, puoi aggiungerlo dal pannello Render.
