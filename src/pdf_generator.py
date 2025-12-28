"""
Modulo per la generazione del PDF del calendario di reperibilità.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black, lightgrey
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime, timedelta
import calendar as cal
from typing import Dict, Tuple


class PDFCalendarioGenerator:
    """Genera un PDF del calendario di reperibilità."""

    # Impostazioni layout (solo estetica)
    PAGE_MARGIN_CM = 0.8
    COL_WIDTH_CM = 2.75  # 7 colonne -> 19.25 cm, entra con margini
    HEADER_HEIGHT_CM = 0.55
    CELL_HEIGHT_CM = 1.9

    # Colori per le tipologie - palette più sobria/leggibile
    COLORI = {
        "festivo": HexColor("#E74C3C"),       # Rosso
        "weekend": HexColor("#3498DB"),       # Blu
        "feriale": HexColor("#F4F6F7"),       # Grigio molto chiaro
        "": HexColor("#FFFFFF")               # Bianco (nessun turno)
    }
    
    # Colori del testo
    COLORI_TESTO = {
        "festivo": HexColor("#FFFFFF"),       # Bianco su rosso
        "weekend": HexColor("#FFFFFF"),       # Bianco su blu
        "feriale": HexColor("#2C3E50"),       # Grigio scuro su grigio
        "": HexColor("#7F8C8D")               # Grigio su bianco
    }
    
    def __init__(self, calendario, output_path: str = "output/calendario_reperibilita_2026.pdf"):
        self.calendario = calendario
        self.output_path = output_path
        self.anno = int(getattr(calendario, "anno", 2026) or 2026)
        self._generated_at = datetime.now()
        # Cache delle assegnazioni per allineare il PDF alla stessa fonte dati dell'API/UI
        try:
            self._assegnazioni = dict(getattr(calendario, "assegnazioni", {}) or {})
        except Exception:
            self._assegnazioni = {}
        # Festività per anno (fallback compatibilità)
        if hasattr(calendario, "get_festivi"):
            try:
                self.festivi = set(calendario.get_festivi(self.anno))
            except Exception:
                self.festivi = set()
        else:
            self.festivi = set(getattr(calendario, "FESTIVI_2026", []) or [])
    
    def genera_pdf(self):
        """Genera il PDF completo con 12 pagine (una per mese)."""
        import os
        import time
        
        # Usa un nome temporaneo con timestamp
        timestamp = str(int(time.time() * 1000))
        temp_path = self.output_path.replace('.pdf', f'_{timestamp}.pdf')
        
        doc = SimpleDocTemplate(
            temp_path,
            pagesize=A4,
            rightMargin=self.PAGE_MARGIN_CM * cm,
            leftMargin=self.PAGE_MARGIN_CM * cm,
            topMargin=self.PAGE_MARGIN_CM * cm,
            bottomMargin=self.PAGE_MARGIN_CM * cm,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Titolo
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=black,
            spaceAfter=4,
            alignment=1  # Centrato
        )
        
        elements.append(Paragraph(f"CALENDARIO DI REPERIBILITÀ {self.anno}", title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Legenda (più pulita, senza emoji)
        legenda_text_style = ParagraphStyle(
            'LegendaText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=10,
        )

        legenda_table_data = [
            ["", Paragraph("<b>FESTIVO</b>: Giorni festivi nazionali (blocco ±7 giorni)", legenda_text_style)],
            ["", Paragraph("<b>WEEKEND</b>: Sabato + Domenica insieme (blocco ±7 giorni)", legenda_text_style)],
            ["", Paragraph("<b>FERIALE</b>: Lunedì–Venerdì (nessun blocco)", legenda_text_style)],
        ]
        legenda_table = Table(legenda_table_data, colWidths=[0.55 * cm, 18.2 * cm])
        legenda_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),

            ('BACKGROUND', (0, 0), (0, 0), self.COLORI['festivo']),
            ('BACKGROUND', (0, 1), (0, 1), self.COLORI['weekend']),
            ('BACKGROUND', (0, 2), (0, 2), self.COLORI['feriale']),
            ('BOX', (0, 0), (-1, -1), 0.75, HexColor('#2C3E50')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#BDC3C7')),
        ]))
        
        elements.append(legenda_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Genera una pagina per ogni mese
        for mese in range(1, 13):
            if mese > 1:
                elements.append(PageBreak())
            
            pagina_mese = self._crea_pagina_mese(mese, styles)
            elements.extend(pagina_mese)
        
        # Build del documento con footer
        doc.build(elements, onFirstPage=self._draw_page_decorations, onLaterPages=self._draw_page_decorations)
        
        # Sposta il file temporaneo al percorso finale
        import shutil
        try:
            if os.path.exists(self.output_path):
                os.remove(self.output_path)
        except:
            pass
        
        try:
            shutil.move(temp_path, self.output_path)
        except:
            # Se move fallisce, copia e rimuovi
            try:
                shutil.copy(temp_path, self.output_path)
                os.remove(temp_path)
            except:
                # Se copia fallisce, usa comunque il temporaneo
                pass
        
        print(f"PDF generato: {self.output_path}")

    def _draw_page_decorations(self, c: canvas.Canvas, doc: SimpleDocTemplate):
        """Disegna footer (pagina + data generazione) su ogni pagina."""
        c.saveState()
        page_num = c.getPageNumber()
        total_pages = 12

        footer_y = self.PAGE_MARGIN_CM * cm * 0.55
        left_x = doc.leftMargin
        right_x = doc.pagesize[0] - doc.rightMargin

        c.setStrokeColor(HexColor('#BDC3C7'))
        c.setLineWidth(0.5)
        c.line(left_x, footer_y + 6, right_x, footer_y + 6)

        c.setFont('Helvetica', 8)
        c.setFillColor(HexColor('#7F8C8D'))
        c.drawString(left_x, footer_y, f"Calendario reperibilità {self.anno}")

        gen = self._generated_at.strftime('%d/%m/%Y')
        c.drawRightString(right_x, footer_y, f"Generato il {gen}  ·  Pagina {page_num}/{total_pages}")
        c.restoreState()

    def _crea_cella_giorno(self, giorno: int, tecnico: str, aiutante: str) -> object:
        """Crea il contenuto della cella con giorno in alto e nomi centrati."""
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.styles import ParagraphStyle

        tecnico_up = (tecnico or "").strip().upper()
        aiutante_up = (aiutante or "").strip().upper()
        righe_nomi = [r for r in (tecnico_up, aiutante_up) if r]

        style_day = ParagraphStyle(
            'CellDay',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=10,
            alignment=1,  # center
        )
        style_names = ParagraphStyle(
            'CellNames',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            alignment=1,  # center
        )

        day_par = Paragraph(str(giorno), style_day)
        if righe_nomi:
            names_par = Paragraph('<br/>'.join(righe_nomi), style_names)
        else:
            names_par = Paragraph('', style_names)

        # La riga del giorno resta in alto; i nomi sono centrati verticalmente nel resto.
        inner = Table(
            [[day_par], [names_par]],
            colWidths=[self.COL_WIDTH_CM * cm],
            rowHeights=[0.45 * cm, (self.CELL_HEIGHT_CM - 0.45) * cm],
        )
        inner.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0, white),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),
        ]))
        return inner
    
    def _crea_pagina_mese(self, mese: int, styles) -> list:
        """Crea la tabella per un mese specifico."""
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.units import cm
        
        # Nome del mese
        nome_mese = self._nome_mese_italiano(mese)
        title_style = ParagraphStyle(
            'MonthTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=black,
            spaceAfter=10,
            alignment=1
        )
        
        elements = []
        elements.append(Paragraph(f"{nome_mese} {self.anno}", title_style))
        
        # Crea la tabella del mese
        data = self._crea_dati_mese(mese)
        
        # Altezza righe: header + righe calendario
        row_heights = [self.HEADER_HEIGHT_CM * cm] + [self.CELL_HEIGHT_CM * cm] * (len(data) - 1)
        table = Table(data, colWidths=[self.COL_WIDTH_CM * cm] * 7, rowHeights=row_heights)
        
        # Stile della tabella
        table.setStyle(self._stile_tabella(mese))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _crea_dati_mese(self, mese: int) -> list:
        """Crea i dati della tabella per un mese."""
        # Intestazione con giorni della settimana
        data = [["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]]
        
        # Ottiene il calendario del mese
        primo_giorno = datetime(self.anno, mese, 1)
        giorni_mese = cal.monthrange(self.anno, mese)[1]
        
        # Calcola il giorno della settimana del primo giorno (0=lunedì, 6=domennica)
        giorno_settimana_inizio = primo_giorno.weekday()
        
        # Riempie la prima riga con spazi vuoti se necessario
        settimana = [""] * giorno_settimana_inizio
        
        # Traccia i dati per applicare i colori in seguito
        self.dati_colori = []
        
        for giorno in range(1, giorni_mese + 1):
            data_obj = datetime(self.anno, mese, giorno)
            data_str = data_obj.strftime("%Y-%m-%d")

            tecnico = ""
            tipo = ""
            aiutante = ""

            assegnazione = self._assegnazioni.get(data_str)
            if isinstance(assegnazione, (list, tuple)) and len(assegnazione) >= 2:
                tecnico = assegnazione[0] or ""
                tipo = assegnazione[1] or ""
                if len(assegnazione) >= 3:
                    aiutante = assegnazione[2] or ""
            else:
                tecnico, tipo = self.calendario.get_reperibile_data(data_str)
                if hasattr(self.calendario, "get_aiutante_data"):
                    try:
                        aiutante = self.calendario.get_aiutante_data(data_str) or ""
                    except Exception:
                        aiutante = ""
            
            # Determina il colore da mostrare (allineato alla logica di assegnazione)
            # Se una festività cade di sab/dom, rimane "weekend".
            tipo_colore = tipo
            if data_str in self.festivi and tipo != "weekend":
                tipo_colore = "festivo"
            
            # Crea il contenuto della cella (include aiutante se presente)
            if tecnico or aiutante:
                contenuto = self._crea_cella_giorno(giorno, tecnico, aiutante)
                self.dati_colori.append((tipo_colore, giorno))
            else:
                contenuto = self._crea_cella_giorno(giorno, "", "")
                self.dati_colori.append(("", giorno))
            
            settimana.append(contenuto)
            
            # Se è domenica o ultimo giorno del mese, aggiunge la settimana
            if data_obj.weekday() == 6 or giorno == giorni_mese:
                # Completa la settimana con spazi vuoti se necessario
                while len(settimana) < 7:
                    settimana.append("")
                data.append(settimana)
                settimana = []
        
        return data
    
    def _stile_tabella(self, mese: int) -> TableStyle:
        """Crea lo stile della tabella."""
        from reportlab.platypus import TableStyle
        from reportlab.lib.colors import HexColor, black, lightgrey
        
        stile = TableStyle([
            # Bordi: esterno più marcato, griglia interna leggera
            ('BOX', (0, 0), (-1, -1), 0.9, HexColor('#2C3E50')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#BDC3C7')),

            # Header
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),

            # Celle dati
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ])
        
        # Applica colori alle celle in base al tipo di reperibilità
        if hasattr(self, 'dati_colori'):
            row = 1
            col = 0
            primo_giorno = datetime(self.anno, mese, 1)
            giorno_settimana_inizio = primo_giorno.weekday()
            
            col = giorno_settimana_inizio
            
            for tipo, giorno in self.dati_colori:
                if tipo == "festivo":
                    # Festivo: rosso vivace con testo bianco
                    stile.add('BACKGROUND', (col, row), (col, row), self.COLORI["festivo"])
                    stile.add('TEXTCOLOR', (col, row), (col, row), self.COLORI_TESTO["festivo"])
                    stile.add('FONTNAME', (col, row), (col, row), 'Helvetica-Bold')
                    stile.add('FONTSIZE', (col, row), (col, row), 9)
                    
                elif tipo == "weekend":
                    # Weekend: blu vivace con testo bianco
                    stile.add('BACKGROUND', (col, row), (col, row), self.COLORI["weekend"])
                    stile.add('TEXTCOLOR', (col, row), (col, row), self.COLORI_TESTO["weekend"])
                    stile.add('FONTNAME', (col, row), (col, row), 'Helvetica-Bold')
                    stile.add('FONTSIZE', (col, row), (col, row), 9)
                    
                elif tipo == "feriale":
                    # Feriale: grigio molto chiaro
                    stile.add('BACKGROUND', (col, row), (col, row), self.COLORI["feriale"])
                    stile.add('TEXTCOLOR', (col, row), (col, row), self.COLORI_TESTO["feriale"])
                    
                else:
                    # Nessun turno: bianco
                    stile.add('BACKGROUND', (col, row), (col, row), self.COLORI[""])
                    stile.add('TEXTCOLOR', (col, row), (col, row), self.COLORI_TESTO[""])
                
                # Avanza alla colonna successiva
                col += 1
                if col >= 7:
                    col = 0
                    row += 1
        
        # Padding a 0: la mini-tabella interna gestisce layout e spaziatura
        stile.add('LEFTPADDING', (0, 1), (-1, -1), 0)
        stile.add('RIGHTPADDING', (0, 1), (-1, -1), 0)
        stile.add('TOPPADDING', (0, 1), (-1, -1), 0)
        stile.add('BOTTOMPADDING', (0, 1), (-1, -1), 0)
        
        return stile
    
    def _nome_mese_italiano(self, mese: int) -> str:
        """Ritorna il nome del mese in italiano."""
        mesi = {
            1: "GENNAIO", 2: "FEBBRAIO", 3: "MARZO", 4: "APRILE",
            5: "MAGGIO", 6: "GIUGNO", 7: "LUGLIO", 8: "AGOSTO",
            9: "SETTEMBRE", 10: "OTTOBRE", 11: "NOVEMBRE", 12: "DICEMBRE"
        }
        return mesi.get(mese, "")
    
    def _tipo_abbreviato(self, tipo: str) -> str:
        """Ritorna l'abbreviazione del tipo di reperibilità."""
        abbr = {
            "feriale": "F",
            "weekend": "WE",
            "festivo": "HH"
        }
        return abbr.get(tipo, "?")
