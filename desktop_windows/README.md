# Desktop Windows (EXE) – Wrapper

Questo progetto crea un installer Windows (.exe) che apre la tua app online in una finestra desktop.

## Prerequisiti
- Node.js LTS (consigliato)

## Build installer
Da questa cartella:

```bash
npm install
set REPAPP_URL=https://TUO_URL_APP
npm run dist
```

Output tipico:
- `dist/Calendario Reperibilita Setup *.exe`

## Nota
Questo wrapper richiede che la tua app sia online (REPAPP_URL). Se vuoi un'app completamente offline, serve un approccio diverso (es. bundling backend), più complesso.
