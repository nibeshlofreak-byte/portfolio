"""
FormIA - Flask + MySQL (PyMySQL) + Faker + Qwen2.5 via Ollama
=============================================================
Base de datos: MySQL en 127.0.1.0  /  formulario
IA local     : Qwen2.5 via Ollama  (se instala automáticamente si falta)
"""

import json
import re
import subprocess
import sys
import threading
import time

import pymysql
import pymysql.cursors
import requests
from faker import Faker
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, url_for)

# ══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = "formia_secret_2025_formulario"

fake = Faker("es_AR")

# ── MySQL ────────────────────────────────────────────────────
# Parámetros base de conexión (sin cursorclass, para poder clonar fácilmente)
_DB_BASE = {
    "host":       "127.0.1.0",
    "port":       3306,
    "user":       "root",
    "password":   "admin",
    "database":   "formulario",
    "charset":    "utf8mb4",
    "autocommit": True,
}
# Alias compatible con código que lea DB_CONFIG["db"] y DB_CONFIG["database"]
DB_CONFIG = {**_DB_BASE, "db": _DB_BASE["database"]}

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
#  CAPA DE BASE DE DATOS
# ══════════════════════════════════════════════════════════════

_db_ok = False   # flag global: True cuando la DB está lista
_db_error = ""   # mensaje de error de conexión


def get_conn():
    """Devuelve una conexión fresca a MySQL."""
    return pymysql.connect(
        **_DB_BASE,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )


def init_db():
    """
    Crea la base de datos si no existe y luego crea las tablas
    necesarias. Llama a esto UNA VEZ al arrancar la app.
    """
    global _db_ok, _db_error

    # Conectar sin especificar DB para poder crearla si hace falta
    cfg_sin_db = {k: v for k, v in DB_CONFIG.items() if k not in {"db", "database"}}

    try:
        conn_init = pymysql.connect(
            **cfg_sin_db,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )
        with conn_init.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn_init.close()

        # Ahora conectar a la DB y crear tablas
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `personas` (
                    `id`             INT AUTO_INCREMENT PRIMARY KEY,
                    `nombre`         VARCHAR(100)  NOT NULL,
                    `apellido`       VARCHAR(100)  NOT NULL,
                    `dni`            VARCHAR(8)    NOT NULL UNIQUE,
                    `estado_laboral` ENUM('Trabaja','No trabaja','Estudia') NOT NULL,
                    `obra_social`    VARCHAR(100)  NOT NULL,
                    `creado_en`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `ia_conversaciones` (
                    `id`         INT AUTO_INCREMENT PRIMARY KEY,
                    `rol`        ENUM('user','assistant') NOT NULL,
                    `mensaje`    TEXT NOT NULL,
                    `creado_en`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.close()
        _db_ok = True
        print("[DB] Conectado a MySQL y tablas verificadas.")

    except Exception as exc:
        _db_error = str(exc)
        _db_ok = False
        print(f"[DB] ERROR al inicializar: {exc}")


def db_insert_persona(nombre, apellido, dni, estado, obra):
    """Inserta una persona. Devuelve el id generado."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO personas (nombre, apellido, dni, estado_laboral, obra_social) "
                "VALUES (%s, %s, %s, %s, %s)",
                (nombre, apellido, dni, estado, obra),
            )
            return cur.lastrowid
    finally:
        conn.close()


def db_get_all():
    """Devuelve todos los registros ordenados por id desc."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, apellido, dni, estado_laboral, obra_social, "
                "DATE_FORMAT(creado_en, '%d/%m/%Y %H:%i') AS fecha "
                "FROM personas ORDER BY id DESC"
            )
            return cur.fetchall()
    finally:
        conn.close()


def db_delete_all():
    """Borra todos los registros de la tabla personas."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM personas")
            cur.execute("ALTER TABLE personas AUTO_INCREMENT = 1")
    finally:
        conn.close()


def db_bulk_insert(registros):
    """Inserta múltiples personas en un solo batch."""
    if not registros:
        return
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT IGNORE INTO personas "
                "(nombre, apellido, dni, estado_laboral, obra_social) "
                "VALUES (%(nombre)s, %(apellido)s, %(dni)s, %(estado_laboral)s, %(obra_social)s)",
                registros,
            )
    finally:
        conn.close()


def db_count():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM personas")
            return cur.fetchone()["total"]
    finally:
        conn.close()


def db_estado_counts():
    """Devuelve los conteos por estado laboral."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado_laboral, COUNT(*) AS total FROM personas GROUP BY estado_laboral"
            )
            rows = cur.fetchall()
            counts = {"Trabaja": 0, "No trabaja": 0, "Estudia": 0}
            for row in rows:
                estado = row["estado_laboral"]
                if estado in counts:
                    counts[estado] = int(row["total"])
            return counts
    finally:
        conn.close()


def db_obra_social_mas_comun():
    """Devuelve la obra social más frecuente."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT obra_social, COUNT(*) AS total FROM personas "
                "GROUP BY obra_social ORDER BY total DESC, obra_social ASC LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return None, 0
            return row["obra_social"], int(row["total"])
    finally:
        conn.close()


def _normalizar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", texto)
    return " ".join(texto.split())


def _pregunta_de_estado(mensaje_lower):
    trabajos = ("trabaja", "trabajan", "trabajando", "trabajo", "trabajos", "empleado", "empleados", "empleada", "empleadas")
    estudios = ("estudia", "estudian", "estudiando", "estudio", "estudios", "estudiante", "estudiantes")
    no_trabajos = ("no trabaja", "no trabajan", "sin trabajo", "desocupado", "desempleado", "no trabajo", "no estudia", "no estudian")
    return any(p in mensaje_lower for p in trabajos) or any(p in mensaje_lower for p in estudios) or any(p in mensaje_lower for p in no_trabajos)


def _pregunta_de_resumen(mensaje_lower):
    resumen_terms = ("resumen", "resume", "resumir", "resumen general", "analisis", "análisis", "descripcion general", "descripcion", "overview", "informe", "estadisticas", "estadísticas")
    return any(p in mensaje_lower for p in resumen_terms)


def _build_status_summary(counts, total):
    trabaja = counts.get("Trabaja", 0)
    no_trabaja = counts.get("No trabaja", 0)
    estudia = counts.get("Estudia", 0)

    if total == 0:
        return "Todavia no hay registros cargados en la base de datos."

    mayor = max(("Trabaja", trabaja), ("No trabaja", no_trabaja), ("Estudia", estudia), key=lambda x: x[1])
    return (
        f"Hay {total} personas registradas. "
        f"Trabajan: {trabaja}. No trabajan: {no_trabaja}. Estudian: {estudia}. "
        f"La categoria mas frecuente es {mayor[0]} ({mayor[1]})."
    )


# ══════════════════════════════════════════════════════════════
#  OLLAMA — instalación automática y gestión del modelo
# ══════════════════════════════════════════════════════════════

_ollama_status = {
    "online":    False,
    "modelos":   [],
    "instalando": False,
    "log":       "",
}


def _ollama_check():
    """Verifica si Ollama responde en localhost:11434."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=4)
        modelos = [m["name"] for m in r.json().get("models", [])]
        _ollama_status["online"]  = True
        _ollama_status["modelos"] = modelos
        return True
    except Exception:
        _ollama_status["online"]  = False
        _ollama_status["modelos"] = []
        return False


def _download_and_install_ollama():
    """
    Descarga el instalador de Ollama para Windows y lo ejecuta silenciosamente.
    Corre en un hilo separado para no bloquear Flask.
    """
    import urllib.request
    import os
    import tempfile

    _ollama_status["instalando"] = True
    _ollama_status["log"] = "Descargando instalador de Ollama..."
    print("[Ollama] Iniciando descarga del instalador...")

    try:
        url = "https://ollama.com/download/OllamaSetup.exe"
        tmp = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")
        urllib.request.urlretrieve(url, tmp)
        _ollama_status["log"] = "Instalando Ollama (puede tardar unos segundos)..."
        print("[Ollama] Instalando...")
        subprocess.run([tmp, "/S"], check=True)   # /S = instalación silenciosa
        time.sleep(5)

        # Intentar iniciar ollama serve en background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        if _ollama_check():
            _ollama_status["log"] = "Ollama instalado y corriendo."
            print("[Ollama] Instalado y funcionando.")
            # Descargar modelo
            _pull_model(OLLAMA_MODEL)
        else:
            _ollama_status["log"] = "Instalado. Reinicia la app para usarlo."

    except Exception as e:
        _ollama_status["log"] = f"Error al instalar Ollama: {e}"
        print(f"[Ollama] Error instalando: {e}")
    finally:
        _ollama_status["instalando"] = False


def _pull_model(model_name):
    """Descarga un modelo de Ollama si no está disponible."""
    if model_name in _ollama_status["modelos"]:
        return
    _ollama_status["log"] = f"Descargando modelo {model_name}..."
    print(f"[Ollama] Descargando modelo {model_name}...")
    try:
        requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name, "stream": False},
            timeout=600,
        )
        _ollama_check()
        _ollama_status["log"] = f"Modelo {model_name} listo."
        print(f"[Ollama] Modelo {model_name} descargado.")
    except Exception as e:
        _ollama_status["log"] = f"Error descargando modelo: {e}"


def _startup_ollama():
    """
    Lógica de arranque de Ollama en background:
    1. Verificar si ya está corriendo.
    2. Si no → intentar ejecutar 'ollama serve' (si Ollama está instalado).
    3. Si tampoco → descargar e instalar Ollama automáticamente.
    4. Una vez online, verificar/descargar el modelo.
    """
    time.sleep(2)   # Esperar a que Flask arranque
    print("[Ollama] Verificando estado...")

    if _ollama_check():
        print("[Ollama] Ya estaba corriendo.")
        if OLLAMA_MODEL not in _ollama_status["modelos"]:
            _pull_model(OLLAMA_MODEL)
        return

    # Intentar levantar Ollama si está instalado pero no activo
    print("[Ollama] No responde. Intentando iniciar 'ollama serve'...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        if _ollama_check():
            print("[Ollama] Servicio iniciado.")
            if OLLAMA_MODEL not in _ollama_status["modelos"]:
                _pull_model(OLLAMA_MODEL)
            return
    except FileNotFoundError:
        print("[Ollama] No instalado. Iniciando descarga automática...")

    # Ollama no instalado → instalación automática
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
        total = len(registros)
    except Exception as e:
        registros, total = [], 0
        flash(f"Error leyendo la base de datos: {e}", "error")
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
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not apellido:
            errores.append("El apellido es obligatorio.")
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
            flash(f"Registro de {nombre} {apellido} guardado en MySQL.", "success")
        except pymysql.err.IntegrityError:
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
    """Genera N registros falsos con Faker e inserta en MySQL."""
    data = request.get_json()
    cantidad = max(1, min(int(data.get("cantidad", 10)), 500))

    if not _db_ok:
        return jsonify({"ok": False, "error": "Base de datos no disponible."}), 503

    nuevos = []
    seen_dni = set()
    for _ in range(cantidad):
        dni = str(fake.random_int(min=10_000_000, max=49_999_999))
        while dni in seen_dni:
            dni = str(fake.random_int(min=10_000_000, max=49_999_999))
        seen_dni.add(dni)
        nuevos.append({
            "nombre":         fake.first_name(),
            "apellido":       fake.last_name(),
            "dni":            dni,
            "estado_laboral": fake.random_element(ESTADOS_LABORALES),
            "obra_social":    fake.random_element(OBRAS_SOCIALES),
        })

    try:
        db_bulk_insert(nuevos)
        total = db_count()
        return jsonify({"ok": True, "generados": len(nuevos), "total": total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/limpiar", methods=["POST"])
def limpiar():
    try:
        db_delete_all()
        flash("Todos los registros fueron eliminados de MySQL.", "info")
    except Exception as e:
        flash(f"Error al limpiar: {e}", "error")
    return redirect(url_for("index"))


@app.route("/exportar")
def exportar():
    try:
        registros = db_get_all()
        # Convertir a lista de dicts serializables
        data = [dict(r) for r in registros]
    except Exception as e:
        data = {"error": str(e)}
    response = app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2,
                            default=str),
        status=200,
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = "attachment; filename=formulario_personas.json"
    return response


# ── DB status API ─────────────────────────────────────────────

@app.route("/db/status")
def db_status():
    if not _db_ok:
        return jsonify({"online": False, "error": _db_error, "total": 0})
    try:
        total = db_count()
        return jsonify({"online": True, "error": "", "total": total,
                        "host": DB_CONFIG["host"], "db": DB_CONFIG["database"]})
    except Exception as e:
        return jsonify({"online": False, "error": str(e), "total": 0})


# ══════════════════════════════════════════════════════════════
#  RUTAS DE IA
# ══════════════════════════════════════════════════════════════

@app.route("/ia")
def ia_page():
    return render_template("ia.html")


@app.route("/ia/chat", methods=["POST"])
def ia_chat():
    data = request.get_json()
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
            if _pregunta_de_estado(mensaje_lower):
                counts = db_estado_counts()
                return jsonify({"respuesta": _build_status_summary(counts, total)})

            consulta_total = (
                any(p in mensaje_lower for p in ("cuanto", "cuantos", "cuantas", "cantidad", "numero", "total"))
                and any(p in mensaje_lower for p in ("registro", "registros", "persona", "personas", "datos"))
            )
            if consulta_total:
                return jsonify({"respuesta": f"Hay {total} registros en total en la base de datos."})

            if _pregunta_de_resumen(mensaje_lower):
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
                    f"\n\nLa base de datos tiene {total} registros en total. "
                    "A continuacion se incluyen todos los registros, no solo una muestra.\n"
                    + json.dumps([dict(r) for r in registros],
                                 ensure_ascii=False, default=str)
                )
        except Exception:
            pass

    prompt = (
        "Sos un asistente util que ayuda con analisis de datos de un formulario de personas.\n"
        f"Respondes siempre en espanol argentino, de forma clara y concisa.{contexto}\n\n"
        f"Usuario: {mensaje}\nAsistente:"
    )

    if not _ollama_status["online"]:
        return jsonify({
            "respuesta": (
                "Ollama todavia no esta listo. "
                + (_ollama_status["log"] or "Esperando instalacion...")
            )
        })

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        resp.raise_for_status()
        respuesta = resp.json().get("response", "Sin respuesta.")
    except requests.exceptions.ConnectionError:
        _ollama_status["online"] = False
        respuesta = "Ollama se desconecto. Intenta de nuevo en unos segundos."
    except Exception as e:
        respuesta = f"Error al consultar Ollama: {e}"

    return jsonify({"respuesta": respuesta})


@app.route("/ia/status")
def ia_status():
    _ollama_check()   # refrescar en cada consulta
    return jsonify({
        "online":     _ollama_status["online"],
        "modelos":    _ollama_status["modelos"],
        "instalando": _ollama_status["instalando"],
        "log":        _ollama_status["log"],
    })


@app.route("/ia/pull", methods=["POST"])
def ia_pull():
    """Fuerza la descarga del modelo desde el frontend."""
    if not _ollama_status["online"]:
        return jsonify({"ok": False, "msg": "Ollama no esta activo."})
    t = threading.Thread(target=_pull_model, args=(OLLAMA_MODEL,), daemon=True)
    t.start()
    return jsonify({"ok": True, "msg": f"Descargando {OLLAMA_MODEL}..."})


# ══════════════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Inicializar DB en el hilo principal antes de levantar Flask
    print("[DB] Conectando a MySQL en 127.0.1.0 / formulario ...")
    init_db()

    # Ollama en background (no bloquea el arranque de Flask)
    t_ollama = threading.Thread(target=_startup_ollama, daemon=True)
    t_ollama.start()

    print("=" * 60)
    print("  FormIA  |  Flask + MySQL + Faker + Qwen2.5")
    print("  URL: http://localhost:5000")
    print(f"  DB:  {'OK - MySQL conectado' if _db_ok else 'ERROR - ' + _db_error}")
    print("=" * 60)

    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
