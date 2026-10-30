"""
FormIA App2 — Flask + SQL Server (pyodbc) + Faker + Qwen2.5
=============================================================
Servidor  : SQL Server en 192.168.1.10
Base de datos : Nikoly
Driver    : {SQL Server}  (ODBC nativo de Windows)
"""

import json
import re
import subprocess
import sys
import threading
import time

import pyodbc
import requests
from faker import Faker
from flask import (Flask, flash, jsonify, redirect, render_template,  
                   request, url_for)

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

app = Flask(__name__, template_folder="app2/templates",
            static_folder="app2/static")
app.secret_key = "formia_app2_sqlserver_2025"

fake = Faker("es_AR")

# ── SQL Server ───────────────────────────────────────────────
SQL_CONN_STR = (
    "Driver={SQL Server};"
    "Server=192.168.1.10;"
    "Database=Nikoly;"
    "UID=Nikoly_sa;"
    "PWD=NIKOLYbe4;"
)

# ── Ollama ───────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:3b"

# ── Datos de dominio ─────────────────────────────────────────
OBRAS_SOCIALES = [
    "IOMA", "OSDE", "Swiss Medical", "Galeno", "Medicus",
    "OMINT", "PAMI", "Accord Salud", "Union Personal",
    "DOSEP", "Sin obra social",
]
ESTADOS_LABORALES = ["Trabaja", "No trabaja", "Estudia"]


# ══════════════════════════════════════════════════════════════
#  CAPA DE BASE DE DATOS — SQL Server via pyodbc
# ══════════════════════════════════════════════════════════════

_db_ok    = False
_db_error = ""


def get_conn():
    """Devuelve una conexión fresca a SQL Server."""
    return pyodbc.connect(SQL_CONN_STR, timeout=10)


def init_db():
    """
    Crea las tablas en SQL Server si no existen.
    En SQL Server no se puede crear la DB desde la conexión misma
    (ya debe existir 'Nikoly'), pero sí creamos las tablas.
    """
    global _db_ok, _db_error
    try:
        conn = get_conn()
        cur  = conn.cursor()

        # Tabla personas
        cur.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects
                WHERE name='personas' AND xtype='U'
            )
            CREATE TABLE personas (
                id             INT IDENTITY(1,1) PRIMARY KEY,
                nombre         NVARCHAR(100) NOT NULL,
                apellido       NVARCHAR(100) NOT NULL,
                dni            NVARCHAR(8)   NOT NULL,
                estado_laboral NVARCHAR(20)  NOT NULL
                                CHECK (estado_laboral IN ('Trabaja','No trabaja','Estudia')),
                obra_social    NVARCHAR(100) NOT NULL,
                creado_en      DATETIME2     DEFAULT GETDATE()
            );
        """)

        # Índice único en DNI (evita duplicados)
        cur.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.indexes
                WHERE name='UQ_personas_dni' AND object_id = OBJECT_ID('personas')
            )
            CREATE UNIQUE INDEX UQ_personas_dni ON personas(dni);
        """)

        # Tabla historial de chat IA
        cur.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects
                WHERE name='ia_conversaciones' AND xtype='U'
            )
            CREATE TABLE ia_conversaciones (
                id        INT IDENTITY(1,1) PRIMARY KEY,
                rol       NVARCHAR(20)  NOT NULL,
                mensaje   NVARCHAR(MAX) NOT NULL,
                creado_en DATETIME2     DEFAULT GETDATE()
            );
        """)

        conn.commit()
        cur.close()
        conn.close()

        _db_ok    = True
        _db_error = ""
        print("[DB] Conectado a SQL Server y tablas verificadas.")

    except Exception as exc:
        _db_ok    = False
        _db_error = str(exc)
        print(f"[DB] ERROR: {exc}")


# ── CRUD helpers ─────────────────────────────────────────────

def db_insert_persona(nombre, apellido, dni, estado, obra):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO personas (nombre, apellido, dni, estado_laboral, obra_social) "
        "VALUES (?, ?, ?, ?, ?)",
        nombre, apellido, dni, estado, obra,
    )
    conn.commit()
    cur.close()
    conn.close()


def db_get_all():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id, nombre, apellido, dni, estado_laboral, obra_social, "
        "CONVERT(NVARCHAR, creado_en, 103) + ' ' + "
        "CONVERT(NVARCHAR, creado_en, 108) AS fecha "
        "FROM personas ORDER BY id DESC"
    )
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def db_delete_all():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM personas")
    cur.execute("DBCC CHECKIDENT ('personas', RESEED, 0)")
    conn.commit()
    cur.close()
    conn.close()


def db_bulk_insert(registros):
    if not registros:
        return 0
    conn = get_conn()
    cur  = conn.cursor()
    inserted = 0
    for r in registros:
        try:
            cur.execute(
                "INSERT INTO personas (nombre, apellido, dni, estado_laboral, obra_social) "
                "VALUES (?, ?, ?, ?, ?)",
                r["nombre"], r["apellido"], r["dni"],
                r["estado_laboral"], r["obra_social"],
            )
            inserted += 1
        except pyodbc.IntegrityError:
            pass   # DNI duplicado, se ignora
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def db_count():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM personas")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


def db_estado_counts():
    """Devuelve los conteos por estado laboral."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT estado_laboral, COUNT(*) AS total "
        "FROM personas GROUP BY estado_laboral"
    )
    rows = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return {
        "Trabaja": rows.get("Trabaja", 0),
        "No trabaja": rows.get("No trabaja", 0),
        "Estudia": rows.get("Estudia", 0),
    }


def db_obra_social_mas_comun():
    """Devuelve la obra social más frecuente."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT obra_social, COUNT(*) AS total FROM personas "
        "GROUP BY obra_social ORDER BY total DESC, obra_social ASC"
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None, 0
    return row[0], int(row[1])


def _normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", texto)
    return " ".join(texto.split())


def _pregunta_de_estado(mensaje_lower):
    palabras_trabajo = (
        "trabaja", "trabajan", "trabajando", "trabajo", "trabajos",
        "empleado", "empleados", "empleada", "empleadas"
    )
    palabras_estudio = (
        "estudia", "estudian", "estudiando", "estudio", "estudios",
        "estudiante", "estudiantes"
    )
    palabras_no_trabajo = (
        "no trabaja", "no trabajan", "sin trabajo", "desocupado",
        "desempleado", "no trabajo", "no trabajan", "no estudia",
        "no estudian"
    )
    return (
        any(p in mensaje_lower for p in palabras_trabajo)
        or any(p in mensaje_lower for p in palabras_estudio)
        or any(p in mensaje_lower for p in palabras_no_trabajo)
    )


def _pregunta_de_resumen(mensaje_lower):
    resumen_terms = (
        "resumen", "resume", "resumir", "resumen general", "analisis",
        "análisis", "descripcion general", "descripcion", "overview",
        "informe", "estadisticas", "estadísticas"
    )
    return any(p in mensaje_lower for p in resumen_terms)


def _build_status_summary(counts, total):
    trabaja = counts.get("Trabaja", 0)
    no_trabaja = counts.get("No trabaja", 0)
    estudia = counts.get("Estudia", 0)

    if total == 0:
        return "Todavia no hay registros cargados en la base de datos."

    partes = [
        f"En total hay {total} personas registradas.",
        f"Trabajan: {trabaja}.",
        f"No trabajan: {no_trabaja}.",
        f"Estudian: {estudia}.",
    ]
    if trabaja > 0 or no_trabaja > 0 or estudia > 0:
        mayor = max([("Trabaja", trabaja), ("No trabaja", no_trabaja), ("Estudia", estudia)], key=lambda x: x[1])
        partes.append(f"La categoria con mas personas es {mayor[0]} ({mayor[1]}).")
    return " ".join(partes)


# ══════════════════════════════════════════════════════════════
#  OLLAMA — arranque automático + descarga de modelo
# ══════════════════════════════════════════════════════════════

_ollama_status = {
    "online":     False,
    "modelos":    [],
    "instalando": False,
    "log":        "",
}


def _ollama_check():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=4)
        _ollama_status["online"]  = True
        _ollama_status["modelos"] = [m["name"] for m in r.json().get("models", [])]
        return True
    except Exception:
        _ollama_status["online"]  = False
        _ollama_status["modelos"] = []
        return False


def _pull_model(name):
    if name in _ollama_status["modelos"]:
        return
    _ollama_status["log"] = f"Descargando {name}..."
    print(f"[Ollama] Descargando {name}...")
    try:
        requests.post(f"{OLLAMA_URL}/api/pull",
                      json={"name": name, "stream": False}, timeout=600)
        _ollama_check()
        _ollama_status["log"] = f"Modelo {name} listo."
    except Exception as e:
        _ollama_status["log"] = f"Error descargando modelo: {e}"


def _download_and_install_ollama():
    import urllib.request, os, tempfile
    _ollama_status["instalando"] = True
    _ollama_status["log"] = "Descargando instalador de Ollama..."
    try:
        url = "https://ollama.com/download/OllamaSetup.exe"
        tmp = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")
        urllib.request.urlretrieve(url, tmp)
        _ollama_status["log"] = "Instalando Ollama..."
        subprocess.run([tmp, "/S"], check=True)
        time.sleep(5)
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        if _ollama_check():
            _pull_model(OLLAMA_MODEL)
        else:
            _ollama_status["log"] = "Instalado. Reiniciá la app para usar la IA."
    except Exception as e:
        _ollama_status["log"] = f"Error instalando Ollama: {e}"
    finally:
        _ollama_status["instalando"] = False


def _startup_ollama():
    time.sleep(2)
    if _ollama_check():
        if OLLAMA_MODEL not in _ollama_status["modelos"]:
            _pull_model(OLLAMA_MODEL)
        return
    try:
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        if _ollama_check():
            if OLLAMA_MODEL not in _ollama_status["modelos"]:
                _pull_model(OLLAMA_MODEL)
            return
    except FileNotFoundError:
        pass
    _download_and_install_ollama()


# ══════════════════════════════════════════════════════════════
#  RUTAS FLASK
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if not _db_ok:
        return render_template("index.html",
                               registros=[], db_error=_db_error,
                               total=0, db_ok=False)
    try:
        registros = db_get_all()
        total     = len(registros)
    except Exception as e:
        registros, total = [], 0
        flash(f"Error leyendo SQL Server: {e}", "error")
    return render_template("index.html",
                           registros=registros, db_error="",
                           total=total, db_ok=_db_ok)


@app.route("/formulario", methods=["GET", "POST"])
def formulario():
    if request.method == "POST":
        nombre        = request.form.get("nombre", "").strip()
        apellido      = request.form.get("apellido", "").strip()
        dni           = request.form.get("dni", "").strip()
        estado_laboral = request.form.get("estado_laboral", "").strip()
        obra_social   = request.form.get("obra_social", "").strip()

        errores = []
        if not nombre:    errores.append("El nombre es obligatorio.")
        if not apellido:  errores.append("El apellido es obligatorio.")
        if not dni or not dni.isdigit() or not (7 <= len(dni) <= 8):
            errores.append("El DNI debe tener 7 u 8 digitos numericos.")
        if estado_laboral not in ESTADOS_LABORALES:
            errores.append("Estado laboral invalido.")
        if obra_social not in OBRAS_SOCIALES:
            errores.append("Obra social invalida.")

        if errores:
            return render_template(
                "formulario.html",
                errores=errores,
                obras_sociales=OBRAS_SOCIALES,
                estados_laborales=ESTADOS_LABORALES,
                form_data=request.form,
            )

        try:
            db_insert_persona(nombre, apellido, dni, estado_laboral, obra_social)
            flash(f"Registro de {nombre} {apellido} guardado en SQL Server.", "success")
        except pyodbc.IntegrityError:
            flash(f"El DNI {dni} ya existe en la base de datos.", "error")
        except Exception as e:
            flash(f"Error al guardar: {e}", "error")

        return redirect(url_for("index"))

    return render_template(
        "formulario.html",
        obras_sociales=OBRAS_SOCIALES,
        estados_laborales=ESTADOS_LABORALES,
        errores=[],
        form_data={},
    )


@app.route("/generar-faker", methods=["POST"])
def generar_faker():
    data     = request.get_json()
    cantidad = max(1, min(int(data.get("cantidad", 10)), 500))

    if not _db_ok:
        return jsonify({"ok": False, "error": "SQL Server no disponible."}), 503

    seen  = set()
    batch = []
    for _ in range(cantidad):
        dni = str(fake.random_int(min=10_000_000, max=49_999_999))
        while dni in seen:
            dni = str(fake.random_int(min=10_000_000, max=49_999_999))
        seen.add(dni)
        batch.append({
            "nombre":         fake.first_name(),
            "apellido":       fake.last_name(),
            "dni":            dni,
            "estado_laboral": fake.random_element(ESTADOS_LABORALES),
            "obra_social":    fake.random_element(OBRAS_SOCIALES),
        })

    try:
        insertados = db_bulk_insert(batch)
        total      = db_count()
        return jsonify({"ok": True, "generados": insertados, "total": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/limpiar", methods=["POST"])
def limpiar():
    try:
        db_delete_all()
        flash("Todos los registros fueron eliminados de SQL Server.", "info")
    except Exception as e:
        flash(f"Error al limpiar: {e}", "error")
    return redirect(url_for("index"))


@app.route("/exportar")
def exportar():
    try:
        data = db_get_all()
    except Exception as e:
        data = [{"error": str(e)}]
    resp = app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Content-Disposition"] = "attachment; filename=nikoly_personas.json"
    return resp


@app.route("/db/status")
def db_status():
    if not _db_ok:
        return jsonify({"online": False, "error": _db_error, "total": 0})
    try:
        return jsonify({
            "online": True, "error": "",
            "total": db_count(),
            "server": "192.168.1.10",
            "db": "Nikoly",
        })
    except Exception as e:
        return jsonify({"online": False, "error": str(e), "total": 0})


# ── IA ────────────────────────────────────────────────────────

@app.route("/ia")
def ia_page():
    return render_template("ia.html")


@app.route("/ia/chat", methods=["POST"])
def ia_chat():
    data    = request.get_json()
    mensaje = data.get("mensaje", "").strip()
    if not mensaje:
        return jsonify({"error": "Mensaje vacio"}), 400

    mensaje_lower = _normalizar_texto(mensaje)
    datos_preguntas = (
        "total", "cuantos", "cuantas", "cantidad", "numero", "registro", "registros",
        "persona", "personas", "trabaja", "trabajan", "trabajo", "estudia", "estudian",
        "no trabaja", "sin trabajo", "resumen", "resume", "descripcion general"
    )

    if not _db_ok and any(p in mensaje_lower for p in datos_preguntas):
        return jsonify({
            "respuesta": "La base de datos no está disponible en este momento. No puedo responder con datos exactos hasta que vuelva a conectarse."
        })

    if _db_ok:
        try:
            total = db_count()
            pregunta_estado = _pregunta_de_estado(mensaje_lower)
            if pregunta_estado:
                counts = db_estado_counts()
                return jsonify({"respuesta": _build_status_summary(counts, total)})

            consulta_total = (
                any(p in mensaje_lower for p in ("cuanto", "cuantos", "cuantas", "cantidad", "numero", "total"))
                and any(p in mensaje_lower for p in ("registro", "registros", "persona", "personas", "datos"))
            )
            if consulta_total:
                return jsonify({"respuesta": f"Hay {total} registros en total en la base de datos Nikoly."})

            resumen = _pregunta_de_resumen(mensaje_lower)
            if resumen:
                counts = db_estado_counts()
                obra, cant_obra = db_obra_social_mas_comun()
                if obra:
                    respuesta = (
                        f"Resumen de los datos: hay {total} registros en total. "
                        f"Trabajan {counts['Trabaja']}, no trabajan {counts['No trabaja']} y estudian {counts['Estudia']}. "
                        f"La obra social más frecuente es {obra} ({cant_obra} personas)."
                    )
                else:
                    respuesta = _build_status_summary(counts, total)
                return jsonify({"respuesta": respuesta})
        except Exception as e:
            print(f"[IA] Error al consultar datos estructurados: {e}")

    contexto = ""
    if _db_ok:
        try:
            total = db_count()
            registros = db_get_all()
            if registros:
                contexto = (
                    f"\n\nLa tabla de SQL Server 'Nikoly' tiene {total} registros en total. "
                    "A continuacion se incluyen todos los registros, no solo una muestra.\n"
                    + json.dumps(registros, ensure_ascii=False, default=str)
                )
        except Exception:
            pass

    prompt = (
        "Sos un asistente util que ayuda con analisis de datos de un formulario de personas.\n"
        f"Respondes en espanol argentino, de forma clara y concisa.{contexto}\n\n"
        f"Usuario: {mensaje}\nAsistente:"
    )

    if not _ollama_status["online"]:
        return jsonify({
            "respuesta": "Ollama todavia no esta listo. " +
                         (_ollama_status["log"] or "Esperando...")
        })

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        r.raise_for_status()
        return jsonify({"respuesta": r.json().get("response", "Sin respuesta.")})
    except requests.exceptions.ConnectionError:
        _ollama_status["online"] = False
        return jsonify({"respuesta": "Ollama se desconecto. Intenta de nuevo."})
    except Exception as e:
        return jsonify({"respuesta": f"Error: {e}"})


@app.route("/ia/status")
def ia_status():
    _ollama_check()
    return jsonify(_ollama_status)


@app.route("/ia/pull", methods=["POST"])
def ia_pull():
    if not _ollama_status["online"]:
        return jsonify({"ok": False, "msg": "Ollama no esta activo."})
    threading.Thread(target=_pull_model, args=(OLLAMA_MODEL,), daemon=True).start()
    return jsonify({"ok": True, "msg": f"Descargando {OLLAMA_MODEL}..."})


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("[DB] Conectando a SQL Server 192.168.1.10 / Nikoly ...")
    init_db()

    threading.Thread(target=_startup_ollama, daemon=True).start()

    print("=" * 60)
    print("  FormIA App2  |  Flask + SQL Server + Faker + Qwen2.5")
    print("  URL  : http://localhost:5001")
    print(f"  DB   : {'OK - SQL Server conectado' if _db_ok else 'ERROR - ' + _db_error}")
    print("=" * 60)

    app.run(debug=False, host="0.0.0.0", port=5001, use_reloader=False)
