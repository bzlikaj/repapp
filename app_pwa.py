#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backend Flask per PWA Calendario Reperibilita
API REST per gestire calendario, tecnici, e aiutanti
"""

import sys
import os
import io
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime
import json
from pathlib import Path
import uuid
import tempfile
import threading
import webbrowser

def _get_base_dir() -> Path:
    """Directory 'portabile' dove tenere dati e da cui risolvere risorse.

    - In sviluppo: cartella del repository (dove sta questo file).
    - In modalità EXE (PyInstaller): cartella dell'eseguibile.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _get_resource_dir(base_dir: Path) -> Path:
    """Directory da cui leggere asset inclusi (pwa/, src/).

    In PyInstaller onefile, gli asset vivono sotto sys._MEIPASS.
    In onedir, sys._MEIPASS punta tipicamente alla cartella di dist.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    try:
        if meipass:
            return Path(meipass)
    except Exception:
        pass
    return base_dir


BASE_DIR = _get_base_dir()
RESOURCE_DIR = _get_resource_dir(BASE_DIR)
STATIC_DIR = RESOURCE_DIR / "pwa"
SRC_DIR = RESOURCE_DIR / "src"

# Aggiungi il percorso src al path
sys.path.insert(0, str(SRC_DIR))

# Importa i moduli del calendario
from calendar_generator import CalendarioReperibilita
from pdf_generator import PDFCalendarioGenerator
from excel_generator import GeneratoreExcel

# Crea l'app Flask
app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='')
CORS(app)


@app.after_request
def _disable_api_cache(response):
    """Evita risposte stale (browser/proxy)."""
    try:
        path = request.path or ""
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    except Exception:
        pass
    return response

# Configurazione

# Permette di usare storage persistente su cloud (Render/Railway/Fly) montando una directory.
# Esempio: REPAPP_DATA_DIR=/data
DATA_DIR = Path(os.environ.get("REPAPP_DATA_DIR", str(BASE_DIR / "pwa_data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"

# Config predefinita
CONFIG_DEFAULT = {
    "tecnici": [
        "Likaj", "Ferraris", "Zanotto", "Casazza", "Mancin",
        "Dardha", "Franchini", "Giraldin", "Terazzi"
    ],
    "aiutanti": [
        "pavanello",
        "longo",
        "resa",
        "gaspari",
        "de paoli",
        "Morabito",
        "shtinja",
        "fossati",
    ],
    # Lista di date (YYYY-MM-DD) in cui serve l'aiutante
    "date_aiutanti": [],
    # Filtro opzionale giorni settimana (0=lunedi .. 6=domenica). Vuoto = tutti
    "giorni_settimana_aiutanti": [],
    # Ferie tecnici: lista di periodi {id, nome, dal, al} (YYYY-MM-DD)
    "ferie": [],
    # Cache dell'ultimo calendario calcolato (per aggiornamenti parziali)
    "calendario_cache": None,
    # Stato rotazione per continuità tra anni: {"2026": {"next_tecnico_index": 3, "next_aiutante_offset": 1}, ...}
    "rotazione_after_year": {},
    # Stato rotazione per-festività tra anni: {"2026": {"01-06": 4, "EASTER": 2, ...}, ...}
    "rotazione_festivi_after_year": {},
    "anno": 2026
}


def normalizza_config(config: dict) -> dict:
    """Garantisce che la config abbia tutte le chiavi attese (compatibilità)."""
    normalized = CONFIG_DEFAULT.copy()
    normalized.update(config or {})
    # Normalizza tipi
    if not isinstance(normalized.get("tecnici"), list):
        normalized["tecnici"] = CONFIG_DEFAULT["tecnici"]
    if not isinstance(normalized.get("aiutanti"), list):
        normalized["aiutanti"] = CONFIG_DEFAULT["aiutanti"]
    if not isinstance(normalized.get("date_aiutanti"), list):
        normalized["date_aiutanti"] = []
    if not isinstance(normalized.get("giorni_settimana_aiutanti"), list):
        normalized["giorni_settimana_aiutanti"] = []
    if not isinstance(normalized.get("anno"), int):
        try:
            normalized["anno"] = int(normalized.get("anno", CONFIG_DEFAULT["anno"]))
        except Exception:
            normalized["anno"] = CONFIG_DEFAULT["anno"]
    if not isinstance(normalized.get("ferie"), list):
        normalized["ferie"] = []
    else:
        # Backward compat: ferie senza "tipo" => tecnico
        fixed_ferie = []
        for f in normalized.get("ferie", []):
            if not isinstance(f, dict):
                continue
            ff = dict(f)
            if ff.get("tipo") not in ("tecnico", "aiutante"):
                ff["tipo"] = "tecnico"
            fixed_ferie.append(ff)
        normalized["ferie"] = fixed_ferie

    if normalized.get("calendario_cache") is not None and not isinstance(normalized.get("calendario_cache"), dict):
        normalized["calendario_cache"] = None
    if not isinstance(normalized.get("rotazione_after_year"), dict):
        normalized["rotazione_after_year"] = {}
    if not isinstance(normalized.get("rotazione_festivi_after_year"), dict):
        normalized["rotazione_festivi_after_year"] = {}
    return normalized


def _calcola_statistiche_da_assegnazioni(assegnazioni: dict) -> tuple[dict, dict]:
    stats_tecnici: dict = {}
    stats_aiutanti: dict = {}
    if not isinstance(assegnazioni, dict):
        return stats_tecnici, stats_aiutanti

    for arr in assegnazioni.values():
        if not isinstance(arr, list) or len(arr) < 2:
            continue
        tecnico = arr[0]
        aiutante = arr[2] if len(arr) >= 3 else ""
        if tecnico:
            stats_tecnici[tecnico] = stats_tecnici.get(tecnico, 0) + 1
        if aiutante:
            stats_aiutanti[aiutante] = stats_aiutanti.get(aiutante, 0) + 1
    return stats_tecnici, stats_aiutanti


def _parse_date_yyyy_mm_dd(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def leggi_config():
    """Legge la configurazione dal file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return normalizza_config(json.load(f))
    return CONFIG_DEFAULT.copy()


def salva_config(config):
    """Salva la configurazione nel file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(normalizza_config(config), f, indent=2)


def _parse_anno_query(default_anno: int) -> int:
    """Estrae anno dalla query string (se presente), altrimenti usa default."""
    anno_q = request.args.get('anno')
    if not anno_q and request.query_string:
        try:
            qs = request.query_string.decode('utf-8', errors='ignore')
            for part in qs.split('&'):
                if part.startswith('anno='):
                    anno_q = part.split('=', 1)[1]
                    break
        except Exception:
            anno_q = None

    try:
        anno = int(anno_q) if anno_q is not None and str(anno_q).strip() else None
    except Exception:
        anno = None
    return int(anno or default_anno)


def _build_calendario(config: dict, anno: int) -> CalendarioReperibilita:
    """Costruisce e genera un calendario coerente con la config e la continuità di rotazione."""
    # Stato rotazione: per l'anno richiesto, usa i puntatori salvati dall'anno precedente
    rot_state = config.get("rotazione_after_year", {}) or {}
    prev_state = rot_state.get(str(anno - 1), {}) if isinstance(rot_state, dict) else {}
    start_idx = int(prev_state.get("next_tecnico_index", 0) or 0)
    aiut_offset = int(prev_state.get("next_aiutante_offset", 0) or 0)

    fest_state_all = config.get("rotazione_festivi_after_year", {}) or {}
    prev_fest_state = fest_state_all.get(str(anno - 1), {}) if isinstance(fest_state_all, dict) else {}
    if not isinstance(prev_fest_state, dict):
        prev_fest_state = {}

    CalendarioReperibilita.ANNO = anno
    CalendarioReperibilita.TECNICI = config.get("tecnici", CalendarioReperibilita.TECNICI)
    CalendarioReperibilita.AIUTANTI = config.get("aiutanti", [])
    CalendarioReperibilita.DATE_AIUTANTI = config.get("date_aiutanti", [])
    CalendarioReperibilita.FERIE = config.get("ferie", [])
    CalendarioReperibilita.GIORNI_AIUTANTI = []
    CalendarioReperibilita.ROTATION_START_INDEX = start_idx
    CalendarioReperibilita.AIUTANTI_OFFSET = aiut_offset
    CalendarioReperibilita.FESTIVI_ROTATION_START = prev_fest_state

    calendario = CalendarioReperibilita()
    calendario.genera_calendario()
    return calendario


# ============ ROUTE PRINCIPALI ============

@app.route('/')
def index():
    """Restituisce l'app PWA"""
    return send_from_directory(str(STATIC_DIR), 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok"})


@app.route('/api/config', methods=['GET'])
def get_config():
    """Ottiene configurazione"""
    config = leggi_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def update_config():
    """Aggiorna configurazione"""
    data = request.json
    salva_config(data)
    return jsonify({"status": "ok"})


@app.route('/api/tecnici', methods=['GET'])
def get_tecnici():
    """Ottiene lista tecnici"""
    config = leggi_config()
    return jsonify({"tecnici": config["tecnici"]})


@app.route('/api/tecnici', methods=['POST'])
def add_tecnico():
    """Aggiunge un tecnico"""
    data = request.json
    nome = data.get("nome", "").strip()
    
    if not nome:
        return jsonify({"error": "Nome vuoto"}), 400
    
    config = leggi_config()
    if nome in config["tecnici"]:
        return jsonify({"error": "Tecnico gia presente"}), 400
    
    config["tecnici"].append(nome)
    salva_config(config)
    return jsonify({"status": "ok", "tecnici": config["tecnici"]})


@app.route('/api/tecnici/<nome>', methods=['DELETE'])
def remove_tecnico(nome):
    """Rimuove un tecnico"""
    config = leggi_config()
    
    if nome not in config["tecnici"]:
        return jsonify({"error": "Tecnico non trovato"}), 404
    
    if len(config["tecnici"]) < 2:
        return jsonify({"error": "Almeno un tecnico deve rimanere"}), 400
    
    config["tecnici"].remove(nome)
    salva_config(config)
    return jsonify({"status": "ok", "tecnici": config["tecnici"]})


@app.route('/api/aiutanti', methods=['GET'])
def get_aiutanti():
    """Ottiene lista aiutanti"""
    config = leggi_config()
    return jsonify({
        "aiutanti": config.get("aiutanti", []),
        "date_aiutanti": config.get("date_aiutanti", []),
        "giorni_settimana_aiutanti": config.get("giorni_settimana_aiutanti", []),
        "anno": config.get("anno", 2026)
    })


@app.route('/api/aiutanti', methods=['POST'])
def add_aiutante():
    """Aggiunge un aiutante"""
    data = request.json
    nome = data.get("nome", "").strip()
    
    if not nome:
        return jsonify({"error": "Nome vuoto"}), 400
    
    config = leggi_config()
    aiutanti = config.get("aiutanti", [])
    
    if nome in aiutanti:
        return jsonify({"error": "Aiutante gia presente"}), 400
    
    aiutanti.append(nome)
    config["aiutanti"] = aiutanti
    salva_config(config)
    
    return jsonify({"status": "ok", "aiutanti": aiutanti})


@app.route('/api/aiutanti/<nome>', methods=['DELETE'])
def remove_aiutante(nome):
    """Rimuove un aiutante"""
    config = leggi_config()
    aiutanti = config.get("aiutanti", [])
    
    if nome not in aiutanti:
        return jsonify({"error": "Aiutante non trovato"}), 404
    
    aiutanti.remove(nome)
    config["aiutanti"] = aiutanti
    salva_config(config)
    
    return jsonify({"status": "ok", "aiutanti": aiutanti})


@app.route('/api/giorni-aiutanti', methods=['GET'])
def get_giorni_aiutanti():
    """Ottiene giorni dove assegnare aiutanti"""
    config = leggi_config()
    # Endpoint legacy: mantenuto per compatibilità, ma non più usato dalla UI
    return jsonify({})


@app.route('/api/giorni-aiutanti', methods=['POST'])
def update_giorni_aiutanti():
    """Aggiorna giorni aiutanti"""
    # Endpoint legacy: mantenuto per compatibilità, ma non più usato dalla UI
    return jsonify({"status": "ok"})


@app.route('/api/date-aiutanti', methods=['GET'])
def get_date_aiutanti():
    """Ottiene la lista delle date (YYYY-MM-DD) in cui serve l'aiutante."""
    config = leggi_config()
    return jsonify({
        "date_aiutanti": config.get("date_aiutanti", []),
        "giorni_settimana_aiutanti": config.get("giorni_settimana_aiutanti", []),
        "anno": config.get("anno", 2026)
    })


@app.route('/api/date-aiutanti', methods=['POST'])
def update_date_aiutanti():
    """Aggiorna la lista delle date (YYYY-MM-DD) in cui serve l'aiutante."""
    data = request.json
    if not isinstance(data, dict) or not isinstance(data.get("date_aiutanti"), list):
        return jsonify({"error": "Payload non valido"}), 400

    config = leggi_config()
    config["date_aiutanti"] = data.get("date_aiutanti", [])
    if "giorni_settimana_aiutanti" in data:
        if not isinstance(data.get("giorni_settimana_aiutanti"), list):
            return jsonify({"error": "giorni_settimana_aiutanti non valido"}), 400
        config["giorni_settimana_aiutanti"] = data.get("giorni_settimana_aiutanti", [])
    salva_config(config)
    return jsonify({"status": "ok", "date_aiutanti": config["date_aiutanti"]})


@app.route('/api/ferie', methods=['GET'])
def get_ferie():
    """Ottiene la lista ferie."""
    config = leggi_config()
    return jsonify({"ferie": config.get("ferie", [])})


@app.route('/api/ferie', methods=['POST'])
def add_ferie():
    """Aggiunge un periodo di ferie per un tecnico."""
    data = request.json or {}
    tipo = (data.get("tipo") or "tecnico").strip().lower()
    nome = (data.get("nome") or "").strip()
    dal = (data.get("dal") or "").strip()
    al = (data.get("al") or "").strip()

    if tipo not in ("tecnico", "aiutante"):
        return jsonify({"error": "Tipo non valido (usa 'tecnico' o 'aiutante')"}), 400

    if not nome or not dal or not al:
        return jsonify({"error": "Campi obbligatori: tipo, nome, dal, al"}), 400

    try:
        dal_dt = _parse_date_yyyy_mm_dd(dal)
        al_dt = _parse_date_yyyy_mm_dd(al)
    except Exception:
        return jsonify({"error": "Formato data non valido (usa YYYY-MM-DD)"}), 400

    if al_dt < dal_dt:
        return jsonify({"error": "Intervallo non valido: 'al' prima di 'dal'"}), 400

    config = leggi_config()
    if tipo == "tecnico":
        if nome not in config.get("tecnici", []):
            return jsonify({"error": "Tecnico non trovato"}), 404
    else:
        if nome not in config.get("aiutanti", []):
            return jsonify({"error": "Aiutante non trovato"}), 404

    ferie = config.get("ferie", [])
    entry = {
        "id": uuid.uuid4().hex,
        "tipo": tipo,
        "nome": nome,
        "dal": dal,
        "al": al,
    }
    ferie.append(entry)
    config["ferie"] = ferie
    salva_config(config)
    return jsonify({"status": "ok", "ferie": ferie})


@app.route('/api/ferie/<ferie_id>', methods=['DELETE'])
def delete_ferie(ferie_id: str):
    """Rimuove una ferie per id."""
    config = leggi_config()
    ferie = config.get("ferie", [])
    new_ferie = [f for f in ferie if str(f.get("id")) != ferie_id]
    if len(new_ferie) == len(ferie):
        return jsonify({"error": "Ferie non trovata"}), 404
    config["ferie"] = new_ferie
    salva_config(config)
    return jsonify({"status": "ok", "ferie": new_ferie})


@app.route('/api/calendario', methods=['GET'])
def get_calendario():
    """Genera calendario"""
    try:
        config = leggi_config()


        # Configura giorni aiutanti
        giorni_aiutanti = config.get("giorni_aiutanti", {})
        giorni_map = {
            "lunedi": 0, "martedi": 1, "mercoledi": 2, "giovedi": 3,
            "venerdi": 4, "sabato": 5, "domenica": 6
        }
        giorni_aiutanti_num = [
            num for giorno, num in giorni_map.items()
            if giorni_aiutanti.get(giorno, False)
        ]

        anno = _parse_anno_query(int(config.get("anno", 2026)))

        calendario = _build_calendario(config, anno)

        assegnazioni = calendario.assegnazioni

        # Calcola lo stato rotazione per l'anno successivo
        next_tecnico_index = 0
        if calendario.TECNICI:
            next_tecnico_index = int(calendario.indice_rotazione % len(calendario.TECNICI))

        next_aiutante_offset = int(getattr(calendario, 'aiutanti_offset', 0) or 0)
        if calendario.AIUTANTI:
            # Trova l'ultimo aiutante assegnato nell'anno e imposta il successivo come start per l'anno seguente
            last_date = None
            last_name = None
            for d in sorted(calendario.aiutante_per_data.keys()):
                name = calendario.aiutante_per_data.get(d) or ""
                if not name:
                    continue
                if str(d).startswith(str(anno) + "-"):
                    last_date = d
                    last_name = name
            if last_name in calendario.AIUTANTI:
                i = calendario.AIUTANTI.index(last_name)
                next_name = calendario.AIUTANTI[(i + 1) % len(calendario.AIUTANTI)]
                next_aiutante_offset = calendario.AIUTANTI.index(next_name)

        rot_state = config.get("rotazione_after_year") or {}
        if not isinstance(rot_state, dict):
            rot_state = {}
        rot_state[str(anno)] = {
            "next_tecnico_index": int(next_tecnico_index),
            "next_aiutante_offset": int(next_aiutante_offset)
        }
        config["rotazione_after_year"] = rot_state

        # Salva anche lo stato rotazione per-festività
        fest_state = config.get("rotazione_festivi_after_year") or {}
        if not isinstance(fest_state, dict):
            fest_state = {}
        fest_state[str(anno)] = dict(getattr(calendario, "festivi_rotation_next", {}) or {})
        config["rotazione_festivi_after_year"] = fest_state

        # Salva cache per poter fare aggiornamenti parziali (es. ferie inserite dopo)
        config["calendario_cache"] = {
            "anno": calendario.anno,
            "assegnazioni": assegnazioni,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        salva_config(config)
        
        return jsonify({
            "status": "ok",
            "assegnazioni": assegnazioni,
            "statistiche": dict(calendario.contatori_turni),
            "statistiche_aiutanti": dict(calendario.contatori_aiutanti),
            "anno": calendario.anno
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/exports/pdf', methods=['GET'])
def export_pdf():
    """Esporta il calendario in PDF."""
    try:
        config = leggi_config()
        anno = _parse_anno_query(int(config.get("anno", 2026)))
        calendario = _build_calendario(config, anno)

        # Genera su file temporaneo
        tmp_dir = DATA_DIR / "exports"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        # File unico per richiesta: evita problemi di caching e lock su Windows
        req_id = uuid.uuid4().hex
        tmp_path = tmp_dir / f"calendario_reperibilita_{anno}_{req_id}.pdf"

        gen = PDFCalendarioGenerator(calendario, output_path=str(tmp_path))
        gen.anno = anno
        gen.genera_pdf()

        return send_file(
            str(tmp_path),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"calendario_reperibilita_{anno}.pdf",
            conditional=False,
            max_age=0,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/exports/excel', methods=['GET'])
def export_excel():
    """Esporta il calendario in Excel (XLSX) modificabile."""
    try:
        config = leggi_config()
        anno = _parse_anno_query(int(config.get("anno", 2026)))
        calendario = _build_calendario(config, anno)

        buf = io.BytesIO()
        gen = GeneratoreExcel(calendario)
        gen.genera_excel(buf)
        buf.seek(0)

        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"calendario_reperibilita_{anno}.xlsx",
            conditional=False,
            max_age=0,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/exports/config', methods=['GET'])
def export_config():
    """Esporta i salvataggi (config/ferie/rotazioni/cache) in JSON."""
    try:
        config = leggi_config()
        exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "exported_at": exported_at,
            "config": config,
        }
        buf = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        buf.seek(0)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(
            buf,
            mimetype="application/json",
            as_attachment=True,
            download_name=f"repapp_salvataggi_{ts}.json",
            conditional=False,
            max_age=0,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/calendario/rigenerare', methods=['POST'])
def rigenera_calendario():
    """Rigenera il calendario usando la configurazione corrente."""
    # La rigenerazione è equivalente a un GET su /api/calendario (tutto è deterministico)
    return get_calendario()


@app.route('/api/calendario/rigenerare-parziale', methods=['POST'])
def rigenera_calendario_parziale():
    """Rigenera solo un intervallo (tipicamente ferie) mantenendo il resto invariato."""
    try:
        data = request.json or {}
        dal = (data.get("dal") or "").strip()
        al = (data.get("al") or "").strip()
        if not dal or not al:
            return jsonify({"error": "Campi obbligatori: dal, al"}), 400

        # Validazione formato
        _parse_date_yyyy_mm_dd(dal)
        _parse_date_yyyy_mm_dd(al)

        config = leggi_config()
        cache = config.get("calendario_cache") or {}
        assegnazioni_base = cache.get("assegnazioni")
        if not isinstance(assegnazioni_base, dict):
            # Se non c'è una base, fallback a rigenerazione completa
            return get_calendario()

        # Determina anno dall'intervallo (YYYY-MM-DD)
        try:
            anno = int(dal[:4])
        except Exception:
            anno = int(config.get("anno", 2026))

        # Configura class variables
        CalendarioReperibilita.ANNO = anno
        CalendarioReperibilita.TECNICI = config.get("tecnici", CalendarioReperibilita.TECNICI)
        CalendarioReperibilita.AIUTANTI = config.get("aiutanti", [])
        CalendarioReperibilita.DATE_AIUTANTI = config.get("date_aiutanti", [])
        CalendarioReperibilita.FERIE = config.get("ferie", [])
        CalendarioReperibilita.GIORNI_AIUTANTI = []

        merged = CalendarioReperibilita.patch_assegnazioni(assegnazioni_base, dal, al)
        stats_tecnici, stats_aiutanti = _calcola_statistiche_da_assegnazioni(merged)

        config["calendario_cache"] = {
            "anno": anno,
            "assegnazioni": merged,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_patch": {"dal": dal, "al": al}
        }
        salva_config(config)

        return jsonify({
            "status": "ok",
            "assegnazioni": merged,
            "statistiche": stats_tecnici,
            "statistiche_aiutanti": stats_aiutanti,
            "anno": anno
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500





if __name__ == '__main__':
    print("=" * 60)
    print("PWA CALENDARIO - SERVER AVVIATO")
    print("=" * 60)
    print("\nAccedi a: http://localhost:5000")
    print("=" * 60)

    def _open_browser():
        try:
            webbrowser.open("http://localhost:5000", new=1)
        except Exception:
            pass

    # Apri il browser dopo un attimo, così Flask fa in tempo a mettersi in ascolto.
    threading.Timer(0.8, _open_browser).start()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
