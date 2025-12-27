"""
Modulo principale per la generazione del calendario di reperibilità.
Implementa la logica di rotazione equa con vincoli di blocco temporale.
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Set, Tuple
import calendar as cal


class TecnicoReperibilita:
    """Rappresenta un tecnico e il suo stato di reperibilità."""
    
    def __init__(self, nome: str):
        self.nome = nome
        self.giorni_reperibili: Dict[str, str] = {}  # {data: tipo}
        self.giorni_bloccati: Set[str] = set()  # Date in formato YYYY-MM-DD
        self.turni_importanti: List[Tuple[str, str]] = []  # [(data, tipo), ...]
    
    def __repr__(self):
        return f"Tecnico({self.nome})"


class CalendarioReperibilita:
    """
    Generatore del calendario di reperibilità con rotazione equa
    e implementazione della regola dei 7 giorni.
    """
    
    TECNICI = [
        "Likaj", "Ferraris", "Zanotto", "Casazza", "Mancin",
        "Dardha", "Franchini", "Giraldin", "Terazzi"
    ]
    
    # Aiutanti: lista separata dei tecnici
    # Viene configurata dinamicamente dalla PWA
    AIUTANTI = []

    # Nuovo modello: lista di date (YYYY-MM-DD) in cui serve l'aiutante
    # Viene configurata dinamicamente dalla PWA
    DATE_AIUTANTI: List[str] = []

    # Ferie tecnici: lista periodi {id, nome, dal, al} (YYYY-MM-DD)
    FERIE: List[Dict[str, str]] = []
    
    # Giorni della settimana dove assegnare aiutanti (0=lunedi, 6=domenica)
    # Viene configurata dinamicamente dalla PWA
    GIORNI_AIUTANTI = [5, 6]  # Sabato e domenica di default
    
    # Stato (configurabile dall'esterno) per supporto multi-anno e continuità di rotazione
    ANNO = 2026
    ROTATION_START_INDEX = 0
    AIUTANTI_OFFSET = 0

    # Stato rotazione per-festività (chiave -> indice tecnico di partenza)
    # Chiavi tipiche: "01-06" (Epifania), "04-25" (Liberazione), "EASTER", "EASTER_MON", ecc.
    FESTIVI_ROTATION_START: Dict[str, int] = {}
    
    GIORNI_BLOCCO = 7  # giorni prima e dopo

    @staticmethod
    def _pasqua_gregoriana(anno: int) -> date:
        """Calcola la data di Pasqua (calendario gregoriano) per l'anno indicato."""
        a = anno % 19
        b = anno // 100
        c = anno % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(anno, month, day)

    @classmethod
    def get_festivi(cls, anno: int) -> List[str]:
        """Ritorna la lista festività nazionali italiane per l'anno indicato."""
        easter = cls._pasqua_gregoriana(anno)
        easter_monday = easter + timedelta(days=1)
        fissi = [
            (1, 1),   # Capodanno
            (1, 6),   # Epifania
            (4, 25),  # Liberazione
            (5, 1),   # Lavoro
            (6, 2),   # Repubblica
            (8, 15),  # Ferragosto
            (11, 1),  # Ognissanti
            (12, 8),  # Immacolata
            (12, 25), # Natale
            (12, 26), # Santo Stefano
        ]
        out = [f"{anno}-{m:02d}-{d:02d}" for (m, d) in fissi]
        out.append(easter.strftime("%Y-%m-%d"))
        out.append(easter_monday.strftime("%Y-%m-%d"))
        out.sort()
        return out

    @classmethod
    def get_festivi_dettaglio(cls, anno: int) -> List[Tuple[str, str]]:
        """Ritorna una lista ordinata di (data_str, key) per ogni festività.

        La key è stabile tra anni per applicare una rotazione dedicata per-festività.
        """
        easter = cls._pasqua_gregoriana(anno)
        easter_monday = easter + timedelta(days=1)

        fixed: List[Tuple[Tuple[int, int], str]] = [
            ((1, 1), "01-01"),
            ((1, 6), "01-06"),
            ((4, 25), "04-25"),
            ((5, 1), "05-01"),
            ((6, 2), "06-02"),
            ((8, 15), "08-15"),
            ((11, 1), "11-01"),
            ((12, 8), "12-08"),
            ((12, 25), "12-25"),
            ((12, 26), "12-26"),
        ]

        out: List[Tuple[str, str]] = []
        for (m, d), key in fixed:
            out.append((f"{anno}-{m:02d}-{d:02d}", key))

        out.append((easter.strftime("%Y-%m-%d"), "EASTER"))
        out.append((easter_monday.strftime("%Y-%m-%d"), "EASTER_MON"))
        out.sort(key=lambda x: x[0])
        return out
    
    def __init__(self):
        self.anno = int(getattr(self, "ANNO", 2026) or 2026)
        self.tecnici: Dict[str, TecnicoReperibilita] = {
            nome: TecnicoReperibilita(nome) for nome in self.TECNICI
        }
        self.calendario: Dict[str, Dict] = {}  # {data: {tipo, tecnico, aiutante}}
        self.indice_rotazione = int(getattr(self, "ROTATION_START_INDEX", 0) or 0)  # Traccia il prossimo tecnico da assegnare
        self.indice_rotazione_aiutanti = 0  # Traccia il prossimo aiutante da assegnare
        self.contatori_turni: Dict[str, int] = {nome: 0 for nome in self.TECNICI}
        self.contatori_aiutanti: Dict[str, int] = {nome: 0 for nome in self.AIUTANTI}
        self.aiutante_per_data: Dict[str, str] = {}
        self.aiutanti_giorni_bloccati: Dict[str, Set[str]] = {nome: set() for nome in self.AIUTANTI}
        self.aiutanti_offset: int = int(getattr(self, "AIUTANTI_OFFSET", 0) or 0)

        # Rotazione dedicata alle festività (persistita esternamente dalla PWA)
        raw_festivi_rot = getattr(self, "FESTIVI_ROTATION_START", {}) or {}
        self.festivi_rotation_index: Dict[str, int] = {}
        if isinstance(raw_festivi_rot, dict):
            for k, v in raw_festivi_rot.items():
                try:
                    self.festivi_rotation_index[str(k)] = int(v)
                except Exception:
                    self.festivi_rotation_index[str(k)] = 0
        self.festivi_rotation_next: Dict[str, int] = {}

        # Precalcola mapping date -> indice (deterministico) per la rotazione aiutanti
        date_aiutanti_raw = getattr(self, "DATE_AIUTANTI", []) or []
        self.date_aiutanti: List[str] = sorted(set(date_aiutanti_raw))
        self._date_aiutanti_index: Dict[str, int] = {
            data_str: idx for idx, data_str in enumerate(self.date_aiutanti)
        }

    def _avanza_rotazione_festivo(self, key: str, base_index: int):
        """Avanza di una posizione la rotazione per una specifica festività."""
        if not self.TECNICI:
            return
        self.festivi_rotation_index[key] = (int(base_index) + 1) % len(self.TECNICI)

    def _assegna_festivo_con_rotazione(self, data_str: str, key: str) -> str:
        """Assegna una festività feriale con rotazione dedicata per-festività."""
        if not self.TECNICI:
            return "ERRORE: Nessun tecnico disponibile"

        start = int(self.festivi_rotation_index.get(key, 0) or 0) % len(self.TECNICI)
        for offset in range(len(self.TECNICI)):
            tecnico_nome = self.TECNICI[(start + offset) % len(self.TECNICI)]
            tecnico = self.tecnici[tecnico_nome]
            if not self._tecnico_disponibile(tecnico, data_str):
                continue

            tecnico.giorni_reperibili[data_str] = "festivo"
            self.contatori_turni[tecnico_nome] += 1
            tecnico.turni_importanti.append((data_str, "festivo"))
            self._aggiungi_blocco(tecnico, data_str)
            self.aiutante_per_data[data_str] = self._assegna_aiutante(data_str)

            # Mantieni coerente anche la rotazione generale
            self.indice_rotazione = (self.TECNICI.index(tecnico_nome) + 1) % len(self.TECNICI)
            return tecnico_nome

        return "ERRORE: Nessun tecnico disponibile"

    def _assegna_weekend_con_rotazione_festivo(self, sabato_str: str, key: str) -> str:
        """Assegna un weekend (sab+dom) usando la rotazione del festivo che cade nel weekend."""
        if not self.TECNICI:
            return "ERRORE: Nessun tecnico disponibile"

        sabato = self._str_to_data(sabato_str)
        domenica_str = self._data_to_str(sabato + timedelta(days=1))

        start = int(self.festivi_rotation_index.get(key, 0) or 0) % len(self.TECNICI)
        for offset in range(len(self.TECNICI)):
            tecnico_nome = self.TECNICI[(start + offset) % len(self.TECNICI)]
            tecnico = self.tecnici[tecnico_nome]
            if not (self._tecnico_disponibile(tecnico, sabato_str) and self._tecnico_disponibile(tecnico, domenica_str)):
                continue

            tecnico.giorni_reperibili[sabato_str] = "weekend"
            tecnico.giorni_reperibili[domenica_str] = "weekend"
            self.contatori_turni[tecnico_nome] += 2
            tecnico.turni_importanti.append((sabato_str, "weekend"))
            self._aggiungi_blocco_weekend(tecnico, sabato_str)
            self.aiutante_per_data[sabato_str] = self._assegna_aiutante(sabato_str)
            self.aiutante_per_data[domenica_str] = self._assegna_aiutante(domenica_str)

            self.indice_rotazione = (self.TECNICI.index(tecnico_nome) + 1) % len(self.TECNICI)
            return tecnico_nome

        return "ERRORE: Nessun tecnico disponibile"
    
    def _data_to_str(self, data: datetime) -> str:
        """Converte datetime a stringa YYYY-MM-DD."""
        return data.strftime("%Y-%m-%d")
    
    def _str_to_data(self, data_str: str) -> datetime:
        """Converte stringa YYYY-MM-DD a datetime."""
        return datetime.strptime(data_str, "%Y-%m-%d")
    
    def _aggiungi_blocco(self, tecnico: TecnicoReperibilita, data_str: str):
        """Aggiunge il blocco di 7 giorni prima e dopo una data."""
        data = self._str_to_data(data_str)
        
        # Blocco 7 giorni prima
        for i in range(1, self.GIORNI_BLOCCO + 1):
            data_bloccata = data - timedelta(days=i)
            tecnico.giorni_bloccati.add(self._data_to_str(data_bloccata))
        
        # Blocco 7 giorni dopo
        for i in range(1, self.GIORNI_BLOCCO + 1):
            data_bloccata = data + timedelta(days=i)
            tecnico.giorni_bloccati.add(self._data_to_str(data_bloccata))
    
    def _aggiungi_blocco_weekend(self, tecnico: TecnicoReperibilita, sabato_str: str):
        """
        Aggiunge il blocco per un weekend.
        Blocca 7 giorni prima del sabato e 8 giorni dopo (per saltare domenica e lunedì).
        """
        sabato = self._str_to_data(sabato_str)
        
        # Blocco 7 giorni prima del sabato
        for i in range(1, self.GIORNI_BLOCCO + 1):
            data_bloccata = sabato - timedelta(days=i)
            tecnico.giorni_bloccati.add(self._data_to_str(data_bloccata))
        
        # Blocco 8 giorni dopo (da martedì in poi, escludendo domenica e lunedì che sono parte del weekend)
        for i in range(2, self.GIORNI_BLOCCO + 2):
            data_bloccata = sabato + timedelta(days=i)
            tecnico.giorni_bloccati.add(self._data_to_str(data_bloccata))
    
    def _tecnico_disponibile(self, tecnico: TecnicoReperibilita, data_str: str) -> bool:
        """Verifica se un tecnico è disponibile per una data."""
        return data_str not in tecnico.giorni_bloccati
    
    def _assegna_aiutante(self, data_str: str) -> str:
        """
        Assegna un aiutante a una data specifica.
        Ritorna il nome dell'aiutante (o vuoto se non assegnato).
        """
        # Se non ci sono aiutanti configurati, non assegnare nulla
        if not self.AIUTANTI:
            return ""

        # Nuovo modello: assegnazione solo sulle date selezionate
        idx = self._date_aiutanti_index.get(data_str)
        if idx is None:
            return ""

        start_pos = (idx + self.aiutanti_offset) % len(self.AIUTANTI)
        aiutante_nome = ""
        for offset in range(len(self.AIUTANTI)):
            candidate = self.AIUTANTI[(start_pos + offset) % len(self.AIUTANTI)]
            blocked = self.aiutanti_giorni_bloccati.get(candidate)
            if blocked and data_str in blocked:
                continue
            aiutante_nome = candidate
            break

        if not aiutante_nome:
            return ""
        # In caso di cambi dinamici della lista aiutanti, garantisci che il contatore esista
        if aiutante_nome not in self.contatori_aiutanti:
            self.contatori_aiutanti[aiutante_nome] = 0
        self.contatori_aiutanti[aiutante_nome] += 1
        
        return aiutante_nome
    
    def _assegna_turno(self, data_str: str, tipo: str) -> str:
        """
        Assegna un turno a un tecnico seguendo la rotazione.
        Ritorna il nome del tecnico assegnato.
        """
        tentativi = 0
        while tentativi < len(self.TECNICI):
            tecnico_nome = self.TECNICI[self.indice_rotazione % len(self.TECNICI)]
            tecnico = self.tecnici[tecnico_nome]
            
            if self._tecnico_disponibile(tecnico, data_str):
                # Assegna il turno
                tecnico.giorni_reperibili[data_str] = tipo
                self.contatori_turni[tecnico_nome] += 1
                
                # Se è un turno importante, aggiunge il blocco
                if tipo in ["weekend", "festivo"]:
                    tecnico.turni_importanti.append((data_str, tipo))
                    self._aggiungi_blocco(tecnico, data_str)
                
                # Assegna aiutante se necessario (e memorizza per la UI)
                self.aiutante_per_data[data_str] = self._assegna_aiutante(data_str)
                
                # Passa al prossimo tecnico per la prossima assegnazione
                self.indice_rotazione += 1
                return tecnico_nome
            
            # Tecnico non disponibile, passa al prossimo
            self.indice_rotazione += 1
            tentativi += 1
        
        # Nessun tecnico disponibile (non dovrebbe accadere con le regole corrette)
        return "ERRORE: Nessun tecnico disponibile"
    
    def _assegna_weekend(self, sabato_str: str) -> str:
        """
        Assegna un weekend completo (sabato + domenica) a un tecnico.
        Ritorna il nome del tecnico assegnato.
        """
        sabato = self._str_to_data(sabato_str)
        domenica_str = self._data_to_str(sabato + timedelta(days=1))
        
        tentativi = 0
        while tentativi < len(self.TECNICI):
            tecnico_nome = self.TECNICI[self.indice_rotazione % len(self.TECNICI)]
            tecnico = self.tecnici[tecnico_nome]
            
            # Controlla se entrambi i giorni sono disponibili
            if (self._tecnico_disponibile(tecnico, sabato_str) and 
                self._tecnico_disponibile(tecnico, domenica_str)):
                
                # Assegna entrambi i giorni
                tecnico.giorni_reperibili[sabato_str] = "weekend"
                tecnico.giorni_reperibili[domenica_str] = "weekend"
                self.contatori_turni[tecnico_nome] += 2  # Conteggia come 2 turni
                
                # Aggiunge il blocco usando il sabato come riferimento
                # MA esclude domenica e lunedì dal blocco (sono parte del weekend)
                tecnico.turni_importanti.append((sabato_str, "weekend"))
                self._aggiungi_blocco_weekend(tecnico, sabato_str)
                
                # Passa al prossimo tecnico
                # Assegna aiutante per sabato/domenica se necessario (e memorizza per la UI)
                self.aiutante_per_data[sabato_str] = self._assegna_aiutante(sabato_str)
                self.aiutante_per_data[domenica_str] = self._assegna_aiutante(domenica_str)
                self.indice_rotazione += 1
                return tecnico_nome
            
            # Tecnico non disponibile, passa al prossimo
            self.indice_rotazione += 1
            tentativi += 1
        
        return "ERRORE: Nessun tecnico disponibile"
    
    def _get_prossimo_lunedi(self, data: datetime) -> datetime:
        """Ritorna il prossimo lunedì (o lo stesso se è già lunedì)."""
        giorni_to_monday = (0 - data.weekday()) % 7
        if giorni_to_monday == 0 and data.weekday() != 0:
            giorni_to_monday = 7
        return data + timedelta(days=giorni_to_monday)
    
    def genera_calendario(self):
        """Genera il calendario completo per l'anno impostato."""
        data_inizio = datetime(self.anno, 1, 1)
        data_fine = datetime(self.anno, 12, 31)

        festivi = set(self.get_festivi(self.anno))
        festivi_dettaglio = self.get_festivi_dettaglio(self.anno)

        # Applica ferie (blocca i tecnici nelle date indicate)
        self._applica_ferie()
        
        # Assegna il 1 gennaio a Dardha SOLO per il 2026 (regola storica).
        # Negli altri anni, il 1 gennaio segue la rotazione normale come qualsiasi festivo.
        data_str = self._data_to_str(data_inizio)
        if self.anno == 2026:
            # Allinea la rotazione del Capodanno: se non c'è stato precedente, parte da Dardha.
            if "01-01" not in self.festivi_rotation_index and "Dardha" in self.TECNICI:
                self.festivi_rotation_index["01-01"] = self.TECNICI.index("Dardha")
            base_0101 = int(self.festivi_rotation_index.get("01-01", 0) or 0)
            tecnico = self.tecnici["Dardha"]
            if data_str in tecnico.giorni_bloccati:
                raise ValueError(f"Conflitto ferie: Dardha è in ferie il {data_str} (obbligatorio)")
            tecnico.giorni_reperibili[data_str] = "festivo"
            self.contatori_turni["Dardha"] += 1
            tecnico.turni_importanti.append((data_str, "festivo"))
            self._aggiungi_blocco(tecnico, data_str)
            # Assegna aiutante anche per il 1 gennaio se previsto
            self.aiutante_per_data[data_str] = self._assegna_aiutante(data_str)
            # Avanza di un anno la rotazione del Capodanno
            self._avanza_rotazione_festivo("01-01", base_0101)
        
        # Assegna le festività con una rotazione dedicata per ciascuna festività.
        for festivo_str, key in festivi_dettaglio:
            # Capodanno 2026 già forzato
            if self.anno == 2026 and festivo_str == data_str:
                continue

            base_idx = int(self.festivi_rotation_index.get(key, 0) or 0)

            tecnico_gia, _ = self.get_reperibile_data(festivo_str)
            if tecnico_gia:
                # Se già assegnato (es. weekend già assegnato), considera la festività "consumata" per l'anno
                self._avanza_rotazione_festivo(key, base_idx)
                continue

            festivo_data = self._str_to_data(festivo_str)
            if festivo_data.weekday() in [5, 6]:
                # Festivo nel weekend: assegna (se non già assegnato) l'intero weekend usando la rotazione del festivo
                sabato_str = festivo_str if festivo_data.weekday() == 5 else self._data_to_str(festivo_data - timedelta(days=1))
                tecnico_sab, _ = self.get_reperibile_data(sabato_str)
                if tecnico_sab:
                    self._avanza_rotazione_festivo(key, base_idx)
                else:
                    self._assegna_weekend_con_rotazione_festivo(sabato_str, key)
                    self._avanza_rotazione_festivo(key, base_idx)
            else:
                self._assegna_festivo_con_rotazione(festivo_str, key)
                self._avanza_rotazione_festivo(key, base_idx)

        # Esponi lo stato rotazione per-festività per persistenza esterna
        self.festivi_rotation_next = dict(self.festivi_rotation_index)
        
        # Assegna i weekend
        data_corrente = data_inizio
        while data_corrente <= data_fine:
            # Trova il sabato
            while data_corrente.weekday() != 5:  # 5 = sabato
                data_corrente += timedelta(days=1)
            
            if data_corrente <= data_fine:
                sabato_str = self._data_to_str(data_corrente)
                domenica_str = self._data_to_str(data_corrente + timedelta(days=1))
                
                # Verifica che non sia già assegnato e che non sia un giorno festivo
                sabato_assegnato = False
                domenica_assegnato = False
                sabato_festivo = sabato_str in festivi
                domenica_festivo = domenica_str in festivi
                
                for tecnico_iter in self.tecnici.values():
                    if sabato_str in tecnico_iter.giorni_reperibili:
                        sabato_assegnato = True
                    if domenica_str in tecnico_iter.giorni_reperibili:
                        domenica_assegnato = True
                
                # Assegna solo se nessuno dei due giorni è festivo o già assegnato
                if (not sabato_assegnato and not domenica_assegnato and 
                    not sabato_festivo and not domenica_festivo):
                    # Assegna il weekend completo (sabato + domenica)
                    self._assegna_weekend(sabato_str)
                
                data_corrente += timedelta(days=2)  # Salta a lunedì
            else:
                break
        
        # Assegna i feriali (lunedì-venerdì, escludendo festivi e fine settimana)
        data_corrente = datetime(self.anno, 1, 1)
        while data_corrente <= data_fine:
            data_str = self._data_to_str(data_corrente)
            
            # Controlla se è feriale (lun-ven, non festivo che non sia nel weekend)
            if data_corrente.weekday() < 5:  # lunedì-venerdì
                # Verifica se è una festività feriale (non nel weekend)
                è_festivo_feriale = (data_str in festivi and data_corrente.weekday() < 5)
                
                if not è_festivo_feriale:
                    # Verifica che non sia già assegnato
                    if not any(
                        data_str in tecnico.giorni_reperibili 
                        for tecnico in self.tecnici.values()
                    ):
                        self._assegna_turno(data_str, "feriale")
            
            data_corrente += timedelta(days=1)

    def _applica_ferie(self):
        """Blocca i tecnici nei periodi di ferie (inibisce assegnazioni)."""
        ferie_list = getattr(self, "FERIE", []) or []
        for entry in ferie_list:
            tipo = (entry.get("tipo") or "tecnico").strip().lower()
            nome = (entry.get("nome") or "").strip()
            dal = entry.get("dal")
            al = entry.get("al")
            if not nome or not dal or not al:
                continue
            try:
                dal_dt = self._str_to_data(dal)
                al_dt = self._str_to_data(al)
            except Exception:
                continue
            if al_dt < dal_dt:
                continue

            cur = dal_dt
            if tipo == "aiutante":
                if nome not in self.aiutanti_giorni_bloccati:
                    self.aiutanti_giorni_bloccati[nome] = set()
                while cur <= al_dt:
                    self.aiutanti_giorni_bloccati[nome].add(self._data_to_str(cur))
                    cur += timedelta(days=1)
            else:
                if nome not in self.tecnici:
                    continue
                tecnico = self.tecnici[nome]
                while cur <= al_dt:
                    tecnico.giorni_bloccati.add(self._data_to_str(cur))
                    cur += timedelta(days=1)
        
        return self.tecnici
    
    def get_reperibile_data(self, data_str: str) -> Tuple[str, str]:
        """Ritorna (tecnico, tipo) per una data specifica."""
        for tecnico_nome, tecnico in self.tecnici.items():
            if data_str in tecnico.giorni_reperibili:
                return (tecnico_nome, tecnico.giorni_reperibili[data_str])
        return ("", "")
    
    def get_aiutante_data(self, data_str: str) -> str:
        """Ritorna l'aiutante per una data specifica."""
        return self.aiutante_per_data.get(data_str, "")
    
    @property
    def assegnazioni(self) -> Dict:
        """Restituisce un dict di tutte le assegnazioni con tecnici e aiutanti."""
        risultato = {}
        anno_start = datetime(self.anno, 1, 1)
        anno_end = datetime(self.anno, 12, 31)

        aiutanti_attivi = bool(self.AIUTANTI) and bool(self.date_aiutanti)
        
        data_corrente = anno_start
        while data_corrente <= anno_end:
            data_str = self._data_to_str(data_corrente)
            tecnico, tipo = self.get_reperibile_data(data_str)
            
            if tecnico:
                # Calcola l'aiutante per questo giorno (se configurato)
                aiutante = ""
                if aiutanti_attivi:
                    aiutante = self.aiutante_per_data.get(data_str, "")
                
                risultato[data_str] = [tecnico, tipo, aiutante]
            
            data_corrente += timedelta(days=1)
        
        return risultato
    
    def get_mese(self, anno: int, mese: int) -> Dict[str, Tuple[str, str]]:
        """Ritorna il calendario per un mese specifico."""
        mese_calendario = {}
        anno_mese = datetime(anno, mese, 1)
        
        # Iterate attraverso tutti i giorni del mese
        for giorno in range(1, cal.monthrange(anno, mese)[1] + 1):
            data = datetime(anno, mese, giorno)
            data_str = self._data_to_str(data)
            tecnico, tipo = self.get_reperibile_data(data_str)
            mese_calendario[data_str] = (tecnico, tipo)
        
        return mese_calendario

    @classmethod
    def patch_assegnazioni(cls, assegnazioni_base: Dict[str, List], dal: str, al: str) -> Dict[str, List]:
        """
        Rigenera solo un intervallo di date (dal/al) mantenendo il resto del calendario invariato.

        Nota: per rispettare la regola dei blocchi, l'intervallo viene automaticamente esteso
        di +/- GIORNI_BLOCCO e normalizzato per includere weekend completi.
        """

        if not isinstance(assegnazioni_base, dict):
            raise ValueError("assegnazioni_base non valido")

        tmp = cls()
        try:
            year = int(str(dal)[:4])
        except Exception:
            year = tmp.anno
        tmp.anno = year
        dal_dt = tmp._str_to_data(dal)
        al_dt = tmp._str_to_data(al)
        if al_dt < dal_dt:
            raise ValueError("Intervallo non valido: 'al' prima di 'dal'")

        # Estendi finestra per minimizzare propagazione oltre il periodo richiesto
        start_dt = dal_dt - timedelta(days=tmp.GIORNI_BLOCCO)
        end_dt = al_dt + timedelta(days=tmp.GIORNI_BLOCCO)

        # Normalizza per includere weekend completi (se include domenica -> includi sabato; se include sabato -> includi domenica)
        if start_dt.weekday() == 6:  # domenica
            start_dt = start_dt - timedelta(days=1)
        if end_dt.weekday() == 5:  # sabato
            end_dt = end_dt + timedelta(days=1)

        # Limita all'anno
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)
        if start_dt < year_start:
            start_dt = year_start
        if end_dt > year_end:
            end_dt = year_end

        start_str = tmp._data_to_str(start_dt)
        end_str = tmp._data_to_str(end_dt)

        cal = cls()
        cal.anno = year
        festivi = set(cls.get_festivi(year))
        cal._applica_ferie()

        # Carica assegnazioni base fuori finestra (lock)
        for data_str, arr in assegnazioni_base.items():
            if not isinstance(arr, list) or len(arr) < 2:
                continue
            if start_str <= data_str <= end_str:
                continue

            tecnico_nome = arr[0]
            tipo = arr[1]
            aiutante = arr[2] if len(arr) >= 3 else ""
            if tecnico_nome not in cal.tecnici:
                continue
            tecnico = cal.tecnici[tecnico_nome]
            tecnico.giorni_reperibili[data_str] = tipo
            if aiutante:
                cal.aiutante_per_data[data_str] = aiutante

            # Ricrea i blocchi per i turni importanti già fissati
            try:
                weekday = cal._str_to_data(data_str).weekday()
            except Exception:
                weekday = None

            if tipo == "festivo":
                cal._aggiungi_blocco(tecnico, data_str)
            elif tipo == "weekend" and weekday == 5:
                cal._aggiungi_blocco_weekend(tecnico, data_str)

        # Imposta l'indice rotazione in modo coerente (approssimazione: prossimo dopo ultimo evento prima della finestra)
        last_event_tecnico = None
        cur = year_start
        while cur < start_dt:
            d = tmp._data_to_str(cur)
            arr = assegnazioni_base.get(d)
            if isinstance(arr, list) and len(arr) >= 2:
                tecnico_nome = arr[0]
                tipo = arr[1]
                if tipo != "weekend" or cur.weekday() == 5:
                    last_event_tecnico = tecnico_nome
            cur += timedelta(days=1)

        if last_event_tecnico in cal.TECNICI:
            cal.indice_rotazione = (cal.TECNICI.index(last_event_tecnico) + 1) % max(1, len(cal.TECNICI))

        # Pulisci (nel caso) le assegnazioni dentro finestra
        for tecnico in cal.tecnici.values():
            for data_str in list(tecnico.giorni_reperibili.keys()):
                if start_str <= data_str <= end_str:
                    tecnico.giorni_reperibili.pop(data_str, None)
        for data_str in list(cal.aiutante_per_data.keys()):
            if start_str <= data_str <= end_str:
                cal.aiutante_per_data.pop(data_str, None)

        # 1) Gestisci 1 gennaio SOLO per il 2026 (obbligatorio)
        obbligatorio = f"{year}-01-01"
        if year == 2026 and start_str <= obbligatorio <= end_str:
            data_str = obbligatorio
            tecnico = cal.tecnici.get("Dardha")
            if tecnico is None:
                raise ValueError("Tecnico obbligatorio 'Dardha' mancante")
            if data_str in tecnico.giorni_bloccati:
                raise ValueError(f"Conflitto ferie: Dardha è in ferie il {data_str} (obbligatorio)")
            tecnico.giorni_reperibili[data_str] = "festivo"
            cal._aggiungi_blocco(tecnico, data_str)
            cal.aiutante_per_data[data_str] = cal._assegna_aiutante(data_str)

        # 2) Festivi nella finestra (replica la logica principale)
        for festivo_str in festivi:
            if not (start_str <= festivo_str <= end_str):
                continue
            if year == 2026 and festivo_str == obbligatorio:
                continue

            festivo_data = cal._str_to_data(festivo_str)
            # Se già assegnato (es. da weekend/fisso), salta
            if any(festivo_str in t.giorni_reperibili for t in cal.tecnici.values()):
                continue

            if festivo_data.weekday() in [5, 6]:
                # Festivo in weekend: assegna weekend completo sul sabato
                sabato_str = festivo_str if festivo_data.weekday() == 5 else cal._data_to_str(festivo_data - timedelta(days=1))
                domenica_str = cal._data_to_str(cal._str_to_data(sabato_str) + timedelta(days=1))
                if not (start_str <= sabato_str <= end_str and start_str <= domenica_str <= end_str):
                    continue
                # Se già assegnato, salta
                if any(sabato_str in t.giorni_reperibili for t in cal.tecnici.values()):
                    continue
                cal._assegna_weekend(sabato_str)
            else:
                cal._assegna_turno(festivo_str, "festivo")

        # 3) Weekend nella finestra (solo se non festivo)
        cur = start_dt
        while cur <= end_dt:
            if cur.weekday() == 5:
                sabato_str = tmp._data_to_str(cur)
                domenica_str = tmp._data_to_str(cur + timedelta(days=1))
                if sabato_str in festivi or domenica_str in festivi:
                    cur += timedelta(days=1)
                    continue
                if any(sabato_str in t.giorni_reperibili for t in cal.tecnici.values()):
                    cur += timedelta(days=1)
                    continue
                if start_str <= sabato_str <= end_str and start_str <= domenica_str <= end_str:
                    cal._assegna_weekend(sabato_str)
            cur += timedelta(days=1)

        # 4) Feriali nella finestra
        cur = start_dt
        while cur <= end_dt:
            data_str = tmp._data_to_str(cur)
            if cur.weekday() < 5:
                è_festivo_feriale = (data_str in festivi and cur.weekday() < 5)
                if not è_festivo_feriale:
                    if not any(data_str in t.giorni_reperibili for t in cal.tecnici.values()):
                        cal._assegna_turno(data_str, "feriale")
            cur += timedelta(days=1)

        # Merge: sostituisci solo le date nella finestra
        merged: Dict[str, List] = dict(assegnazioni_base)
        cur = start_dt
        while cur <= end_dt:
            data_str = tmp._data_to_str(cur)
            tecnico_nome, tipo = cal.get_reperibile_data(data_str)
            if tecnico_nome:
                merged[data_str] = [tecnico_nome, tipo, cal.aiutante_per_data.get(data_str, "")]
            cur += timedelta(days=1)

        return merged
