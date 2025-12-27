# Android (APK) – Wrapper

Questo progetto crea un'app Android (APK) che apre la tua app online.

## Prerequisiti
- Node.js LTS
- Android Studio (con SDK Android)

## Passi
1) Installa dipendenze:
```bash
npm install
```

2) Imposta l'URL della tua app online:
- Modifica `capacitor.config.ts` e sostituisci `https://TUO_URL_APP` con l'URL reale.

3) Inizializza Capacitor e genera progetto Android:
```bash
npx cap init
npx cap add android
npx cap open android
```

4) In Android Studio:
- Build → Generate Signed Bundle / APK

Output:
- APK installabile su Android e distribuibile con un link.

## Nota
Questo wrapper richiede che la tua app sia online. Per un APK completamente offline servirebbe incorporare anche il backend (molto più complesso).
