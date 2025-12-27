"""
Modulo di utilità per la validazione e reporting del calendario.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from calendar_generator import CalendarioReperibilita


class ValidatoreCalendario:
    """Valida il calendario rispetto alle regole stabilite."""
    
    def __init__(self, calendario: CalendarioReperibilita):
        self.calendario = calendario
    
    def valida_regola_7_giorni(self) -> Tuple[bool, List[str]]:
        """
        Valida che nessun tecnico sia assegnato nei 7 giorni prima/dopo
        un turno importante (weekend o festivo).
        NOTA: Per i weekend, sabato e domenica sono considerati come un unico turno,
        quindi non si considerano violazioni tra sabato e domenica o tra domenica e lunedì.
        Le festività nel weekend contano come weekend, non come festivo.
        """
        errori = []
        
        for tecnico_nome, tecnico in self.calendario.tecnici.items():
            # Per ogni turno importante
            for data_importante_str, tipo in tecnico.turni_importanti:
                data_importante = datetime.strptime(data_importante_str, "%Y-%m-%d")
                
                if tipo == "weekend":
                    # Per i weekend, il blocco è da lunedì 8 giorni prima a martedì 8 giorni dopo
                    # (escludendo sabato e domenica che sono il turno stesso)
                    
                    # Controlla i 7 giorni precedenti (da -7 a -1)
                    for i in range(1, 8):
                        data_bloccata = data_importante - timedelta(days=i)
                        data_bloccata_str = data_bloccata.strftime("%Y-%m-%d")
                        
                        if data_bloccata_str in tecnico.giorni_reperibili:
                            tipo_bloccato = tecnico.giorni_reperibili[data_bloccata_str]
                            if tipo_bloccato not in ["weekend"]:
                                errori.append(
                                    f"ERRORE: {tecnico_nome} assegnato il {data_bloccata_str} ({tipo_bloccato}) "
                                    f"ma ha weekend il {data_importante_str} (violazione -7 giorni)"
                                )
                    
                    # Controlla i 7 giorni successivi (da +2 a +8, saltando domenica)
                    for i in range(2, 9):  # +2 (lunedì) a +8
                        data_bloccata = data_importante + timedelta(days=i)
                        data_bloccata_str = data_bloccata.strftime("%Y-%m-%d")
                        
                        if data_bloccata_str in tecnico.giorni_reperibili:
                            tipo_bloccato = tecnico.giorni_reperibili[data_bloccata_str]
                            if tipo_bloccato not in ["weekend"]:
                                errori.append(
                                    f"ERRORE: {tecnico_nome} assegnato il {data_bloccata_str} ({tipo_bloccato}) "
                                    f"ma ha weekend il {data_importante_str} (violazione +7 giorni)"
                                )
                
                else:
                    # Per i festivi feriali (non nel weekend), il blocco è pieno ±7 giorni
                    data_importante_dt = datetime.strptime(data_importante_str, "%Y-%m-%d")
                    
                    # Se il festivo è nel weekend, non applicare il blocco (conta come weekend)
                    if data_importante_dt.weekday() not in [5, 6]:
                        # È un festivo feriale - blocco pieno ±7 giorni
                        
                        # Controlla i 7 giorni precedenti
                        for i in range(1, 8):
                            data_bloccata = data_importante - timedelta(days=i)
                            data_bloccata_str = data_bloccata.strftime("%Y-%m-%d")
                            
                            if data_bloccata_str in tecnico.giorni_reperibili:
                                tipo_bloccato = tecnico.giorni_reperibili[data_bloccata_str]
                                errori.append(
                                    f"ERRORE: {tecnico_nome} assegnato il {data_bloccata_str} ({tipo_bloccato}) "
                                    f"ma ha festivo il {data_importante_str} (violazione -7 giorni)"
                                )
                        
                        # Controlla i 7 giorni successivi
                        for i in range(1, 8):
                            data_bloccata = data_importante + timedelta(days=i)
                            data_bloccata_str = data_bloccata.strftime("%Y-%m-%d")
                            
                            if data_bloccata_str in tecnico.giorni_reperibili:
                                tipo_bloccato = tecnico.giorni_reperibili[data_bloccata_str]
                                errori.append(
                                    f"ERRORE: {tecnico_nome} assegnato il {data_bloccata_str} ({tipo_bloccato}) "
                                    f"ma ha festivo il {data_importante_str} (violazione +7 giorni)"
                                )
        
        return len(errori) == 0, errori
    
    def valida_assegnazione_unica_per_data(self) -> Tuple[bool, List[str]]:
        """Valida che ogni data sia assegnata a una sola persona."""
        errori = []
        assegnazioni_per_data: Dict[str, List[str]] = {}
        
        for tecnico_nome, tecnico in self.calendario.tecnici.items():
            for data_str, tipo in tecnico.giorni_reperibili.items():
                if data_str not in assegnazioni_per_data:
                    assegnazioni_per_data[data_str] = []
                assegnazioni_per_data[data_str].append(tecnico_nome)
        
        for data_str, tecnici in assegnazioni_per_data.items():
            if len(tecnici) > 1:
                errori.append(
                    f"ERRORE: Data {data_str} assegnata a {len(tecnici)} tecnici: {', '.join(tecnici)}"
                )
        
        return len(errori) == 0, errori
    
    def valida_capodanno(self) -> Tuple[bool, List[str]]:
        """Valida che il 1 gennaio sia assegnato a Dardha SOLO per il 2026."""
        errori = []

        anno = int(getattr(self.calendario, "anno", 2026) or 2026)
        if anno != 2026:
            # Negli altri anni il 1 gennaio segue la rotazione normale.
            return True, []

        capodanno_str = "2026-01-01"
        
        assegnato = False
        for tecnico_nome, tecnico in self.calendario.tecnici.items():
            if capodanno_str in tecnico.giorni_reperibili:
                if tecnico_nome != "Dardha":
                    errori.append(f"ERRORE: 1 gennaio assegnato a {tecnico_nome}, deve essere Dardha")
                else:
                    assegnato = True
        
        if not assegnato:
            errori.append("ERRORE: 1 gennaio non assegnato a nessuno")
        
        return len(errori) == 0, errori
    
    def valida_equita_turni(self) -> Tuple[bool, List[str]]:
        """Valida che i turni siano distribuiti equamente."""
        errori = []
        
        turni = list(self.calendario.contatori_turni.values())
        media = sum(turni) / len(turni)
        max_diff = 2  # Tolleranza di 2 turni
        
        for tecnico_nome, contatore in self.calendario.contatori_turni.items():
            diff = abs(contatore - media)
            if diff > max_diff:
                errori.append(
                    f"AVVISO: {tecnico_nome} ha {contatore} turni (media: {media:.1f}, differenza: {diff:.1f})"
                )
        
        return len(errori) == 0, errori
    
    def esegui_tutte_validazioni(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Esegue tutte le validazioni."""
        risultati = {
            "Regola 7 giorni": self.valida_regola_7_giorni(),
            "Assegnazione unica per data": self.valida_assegnazione_unica_per_data(),
            "Capodanno a Dardha (solo 2026)": self.valida_capodanno(),
            "Equità turni": self.valida_equita_turni(),
        }
        return risultati


def genera_report_validazione(calendario: CalendarioReperibilita) -> str:
    """Genera un report di validazione del calendario."""
    validatore = ValidatoreCalendario(calendario)
    risultati = validatore.esegui_tutte_validazioni()
    
    report = "\n" + "=" * 60 + "\n"
    anno = int(getattr(calendario, "anno", 2026) or 2026)
    report += f"REPORT DI VALIDAZIONE CALENDARIO {anno}\n"
    report += "=" * 60 + "\n"
    
    tutto_ok = True
    
    for nome_test, (ok, errori) in risultati.items():
        if ok:
            report += f"\n✅ {nome_test}: PASSATO\n"
        else:
            report += f"\n❌ {nome_test}: FALLITO\n"
            tutto_ok = False
            for errore in errori:
                report += f"   {errore}\n"
    
    report += "\n" + "=" * 60 + "\n"
    if tutto_ok:
        report += "✅ TUTTE LE VALIDAZIONI PASSATE\n"
    else:
        report += "❌ ALCUNE VALIDAZIONI FALLITE\n"
    report += "=" * 60 + "\n"
    
    return report
