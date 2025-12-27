# App installabili (Windows + Android)

Obiettivo: generare file da scaricare e installare direttamente:
- Windows: installer `.exe`
- Android: `.apk`

Questi pacchetti sono wrapper che aprono la tua app online (stesso URL pubblico del backend Flask + frontend PWA).

## 1) Prima: metti l'app online
Devi avere un URL pubblico (es. Render).

Suggerimento: usa storage persistente e imposta:
- `REPAPP_DATA_DIR=/data`

## 2) Windows (EXE)
Cartella: `desktop_windows/`

Comandi:
```bash
cd desktop_windows
npm install
set REPAPP_URL=https://TUO_URL_APP
npm run dist
```
Risultato: un installer in `desktop_windows/dist/`.

## 3) Android (APK)
Cartella: `mobile_android/`

1) Modifica `mobile_android/capacitor.config.ts` e imposta `server.url`.
2) Comandi:
```bash
cd mobile_android
npm install
npx cap init
npx cap add android
npx cap open android
```
3) In Android Studio genera un APK firmato.

## Distribuzione tramite link
Carica i file su:
- GitHub Releases
- Google Drive / OneDrive
- Un tuo sito

Poi condividi il link di download.
