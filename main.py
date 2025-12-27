"""
Script principale per generare il calendario di reperibilità 2026.
"""

import sys
import os
from pathlib import Path

# Aggiungi il percorso src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from calendar_generator import CalendarioReperibilita
from pdf_generator import PDFCalendarioGenerator
from excel_generator import GeneratoreExcel
from validatore import genera_report_validazione


def main():
    """Funzione principale."""
    print("=" * 60)
    print("GENERATORE CALENDARIO DI REPERIBILITÀ 2026")
    print("=" * 60)
    
    # Crea le cartelle di output se non esistono
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Genera il calendario
    print("\n1️⃣ Generazione calendario...")
    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    print("✅ Calendario generato con successo!")
    
    # Validazione
    print("\n2️⃣ Validazione calendario...")
    report = genera_report_validazione(calendario)
    print(report)
    
    # Mostra statistiche
    print("3️⃣ Statistiche assegnazioni:")
    print("-" * 40)
    for tecnico_nome, contatore in sorted(calendario.contatori_turni.items()):
        print(f"  {tecnico_nome:15} : {contatore:2} turni")
    
    # Mostra alcuni esempi
    print("\n4️⃣ Esempi di assegnazioni:")
    print("-" * 40)
    for mese in [1, 6, 12]:
        print(f"\n  Primo giorno assegnato a {mese}/{calendario.anno}:")
        data_str = f"{calendario.anno}-{mese:02d}-01"
        tecnico, tipo = calendario.get_reperibile_data(data_str)
        if tecnico:
            print(f"    → {tecnico} ({tipo})")
    
    # Genera il PDF
    print("\n5️⃣ Generazione PDF...")
    pdf_path = str(output_dir / "calendario_reperibilita_2026.pdf")
    pdf_generator = PDFCalendarioGenerator(calendario, pdf_path)
    pdf_generator.genera_pdf()
    print("✅ PDF generato con successo!")
    
    # Genera l'Excel
    print("\n6️⃣ Generazione Excel...")
    excel_path = str(output_dir / "calendario_reperibilita_2026.xlsx")
    excel_generator = GeneratoreExcel(calendario)
    excel_generator.genera_excel(excel_path)
    print("✅ Excel generato con successo!")
    
    print("\n" + "=" * 60)
    print(f"📄 File PDF salvato in: {pdf_path}")
    print(f"📊 File Excel salvato in: {excel_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
