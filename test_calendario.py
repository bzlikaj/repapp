"""
Modulo di test per la validazione dettagliata del calendario.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from calendar_generator import CalendarioReperibilita
from validatore import ValidatoreCalendario


def test_blocco_7_giorni():
    """Test della regola dei 7 giorni."""
    print("\n" + "="*60)
    print("TEST: REGOLA DEI 7 GIORNI")
    print("="*60)
    
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    
    # Verifica un tecnico con turno importante
    dardha = calendario.tecnici["Dardha"]
    
    print(f"\nTurni importanti di Dardha:")
    for data_str, tipo in dardha.turni_importanti:
        print(f"  - {data_str} ({tipo})")
        
        # Mostra il blocco
        data = datetime.strptime(data_str, "%Y-%m-%d")
        giorni_bloccati = []
        
        for i in range(-7, 8):
            if i != 0:
                data_bloccata = data + timedelta(days=i)
                data_bloccata_str = data_bloccata.strftime("%Y-%m-%d")
                if data_bloccata_str in dardha.giorni_bloccati:
                    giorni_bloccati.append(f"{data_bloccata_str}")
        
        print(f"    Giorni bloccati: {len(giorni_bloccati)}")
    
    # Validazione
    validatore = ValidatoreCalendario(calendario)
    ok, errori = validatore.valida_regola_7_giorni()
    
    if ok:
        print("\n✅ PASSATO: Nessun conflitto di blocco")
    else:
        print("\n❌ FALLITO:")
        for errore in errori:
            print(f"   {errore}")


def test_rotazione_equa():
    """Test della rotazione equa tra tecnici."""
    print("\n" + "="*60)
    print("TEST: ROTAZIONE EQUA")
    print("="*60)
    
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    
    turni = sorted(calendario.contatori_turni.items(), key=lambda x: x[1], reverse=True)
    
    print("\nDistribuzione turni:")
    for tecnico, contatore in turni:
        barra = "█" * (contatore // 2)
        print(f"  {tecnico:15} [{barra:<20}] {contatore}")
    
    # Verifica equità
    max_turni = max(calendario.contatori_turni.values())
    min_turni = min(calendario.contatori_turni.values())
    diff = max_turni - min_turni
    
    print(f"\nMax: {max_turni}, Min: {min_turni}, Differenza: {diff}")
    
    # Nota: con vincoli rigidi (blocchi ±7, weekend/festivi, ferie) la diff può arrivare a ~4
    if diff <= 4:
        print("✅ PASSATO: Distribuzione equa (diff ≤ 4)")
    else:
        print(f"❌ FALLITO: Distribuzione non equa (diff = {diff})")


def test_festivi():
    """Test dell'assegnazione dei festivi."""
    print("\n" + "="*60)
    print("TEST: ASSEGNAZIONE FESTIVI")
    print("="*60)
    
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    
    if hasattr(calendario, "get_festivi"):
        festivi = sorted(calendario.get_festivi(2026))
    else:
        festivi = sorted(getattr(calendario, "FESTIVI_2026", []) or [])

    print("\nFestivi assegnati:")
    for festivo_str in festivi:
        tecnico, tipo = calendario.get_reperibile_data(festivo_str)
        data_obj = datetime.strptime(festivo_str, "%Y-%m-%d")
        data_formattata = data_obj.strftime("%d/%m/%Y (%A)")
        
        if tecnico:
            print(f"  {festivo_str} → {tecnico:15}")
        else:
            print(f"  {festivo_str} → [NON ASSEGNATO]")
    
    # Verifica il 1 gennaio
    capodanno_str = "2026-01-01"
    tecnico_capodanno, _ = calendario.get_reperibile_data(capodanno_str)
    
    print(f"\n1 gennaio assegnato a: {tecnico_capodanno}")
    if tecnico_capodanno == "Dardha":
        print("✅ PASSATO: 1 gennaio assegnato correttamente a Dardha")
    else:
        print(f"❌ FALLITO: 1 gennaio assegnato a {tecnico_capodanno}, deve essere Dardha")


def test_weekend():
    """Test dell'assegnazione dei weekend."""
    print("\n" + "="*60)
    print("TEST: ASSEGNAZIONE WEEKEND")
    print("="*60)
    
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    
    print("\nPrimi 5 weekend assegnati:")
    
    data = datetime(2026, 1, 1)
    data_fine = datetime(2026, 12, 31)
    contatore = 0
    
    while data <= data_fine and contatore < 5:
        # Trova il sabato
        while data.weekday() != 5:  # 5 = sabato
            data += timedelta(days=1)
        
        if data <= data_fine:
            sabato_str = data.strftime("%Y-%m-%d")
            domenica_str = (data + timedelta(days=1)).strftime("%Y-%m-%d")
            
            tecnico_sab, tipo_sab = calendario.get_reperibile_data(sabato_str)
            tecnico_dom, tipo_dom = calendario.get_reperibile_data(domenica_str)
            
            print(f"  {sabato_str} (Sab) → {tecnico_sab:15} ({tipo_sab})")
            print(f"  {domenica_str} (Dom) → {tecnico_dom:15} ({tipo_dom})")
            
            if tecnico_sab != tecnico_dom:
                print(f"    ⚠️  ATTENZIONE: Tecnici diversi!")
            
            print()
            contatore += 1
            data += timedelta(days=2)


def test_feriali():
    """Test della distribuzione dei giorni feriali."""
    print("\n" + "="*60)
    print("TEST: DISTRIBUZIONE FERIALI")
    print("="*60)
    
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    
    # Conta i feriali per tecnico
    feriali_per_tecnico = {nome: 0 for nome in calendario.TECNICI}
    
    data = datetime(2026, 1, 1)
    data_fine = datetime(2026, 12, 31)
    
    while data <= data_fine:
        if data.weekday() < 5:  # lunedì-venerdì
            data_str = data.strftime("%Y-%m-%d")
            tecnico, tipo = calendario.get_reperibile_data(data_str)
            if tecnico and tipo == "feriale":
                feriali_per_tecnico[tecnico] += 1
        
        data += timedelta(days=1)
    
    print("\nFeriali per tecnico:")
    for tecnico, contatore in sorted(feriali_per_tecnico.items()):
        barra = "█" * (contatore // 2)
        print(f"  {tecnico:15} [{barra:<20}] {contatore}")


if __name__ == "__main__":
    print("\n" + "🧪 SUITE DI TEST - CALENDARIO REPERIBILITÀ 2026 ".center(60, "="))
    
    test_blocco_7_giorni()
    test_rotazione_equa()
    test_festivi()
    test_weekend()
    test_feriali()
    
    print("\n" + "="*60)
    print("✅ TUTTI I TEST COMPLETATI")
    print("="*60 + "\n")
