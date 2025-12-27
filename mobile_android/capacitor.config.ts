import type { CapacitorConfig } from '@capacitor/cli';

// Wrapper che punta alla tua app online.
// Dopo il deploy, sostituisci server.url con il tuo URL pubblico.
const config: CapacitorConfig = {
  appId: 'com.repapp.calendario',
  appName: 'Calendario Reperibilita',
  webDir: 'www',
  server: {
    url: 'https://TUO_URL_APP',
    cleartext: false
  }
};

export default config;
