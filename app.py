import re
import sqlite3
from datetime import date, datetime

from flask import Flask, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

PRIORIDADES = ("alta", "media", "baja")
ESTADOS = ("pendiente", "completada")
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tareas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT    NOT NULL,
    descripcion  TEXT    NOT NULL DEFAULT '',
    prioridad    TEXT    NOT NULL DEFAULT 'media',
    fecha_limite TEXT,
    completada   INTEGER NOT NULL DEFAULT 0,
    creada_en    TEXT    NOT NULL
)
"""


class ErrorAPI(Exception):
    """Error controlado de la API: se responde como {"error": mensaje}."""

    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


# ---------------------------------------------------------------- validaciones
def validar_titulo(valor):
    if not isinstance(valor, str):
        raise ErrorAPI(400, "El título es obligatorio y debe ser texto")
    valor = valor.strip()
    if not 3 <= len(valor) <= 100:
        raise ErrorAPI(400, "El título debe tener entre 3 y 100 caracteres")
    return valor


def validar_descripcion(valor):
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise ErrorAPI(400, "La descripción debe ser texto")
    valor = valor.strip()
    if len(valor) > 500:
        raise ErrorAPI(400, "La descripción puede tener como máximo 500 caracteres")
    return valor


def validar_prioridad(valor):
    if not isinstance(valor, str) or valor not in PRIORIDADES:
        raise ErrorAPI(400, "La prioridad debe ser 'alta', 'media' o 'baja'")
    return valor


def validar_fecha(valor):
    if valor is None:
        return None
    if not isinstance(valor, str) or not PATRON_FECHA.match(valor):
        raise ErrorAPI(400, "La fecha límite debe tener el formato AAAA-MM-DD")
    try:
        fecha = date.fromisoformat(valor)
    except ValueError:
        raise ErrorAPI(400, "La fecha límite no es una fecha real del calendario")
    if fecha < date.today():
        raise ErrorAPI(400, "La fecha límite no puede ser anterior a hoy")
    return valor


def leer_cuerpo_objeto():
    cuerpo = request.get_json(force=True, silent=True)
    if not isinstance(cuerpo, dict):
        raise ErrorAPI(400, "El cuerpo debe ser un objeto JSON válido")
    return cuerpo


def tarea_a_dict(fila):
    return {
        "id": fila["id"],
        "titulo": fila["titulo"],
        "descripcion": fila["descripcion"],
        "prioridad": fila["prioridad"],
        "fecha_limite": fila["fecha_limite"],
        "completada": bool(fila["completada"]),
        "creada_en": fila["creada_en"],
    }


# ------------------------------------------------------------------- aplicación
def create_app(db_path: str = "tareas.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path

    def obtener_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def cerrar_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Crear las tablas al construir la aplicación (R13: sin pasos manuales)
    conexion = sqlite3.connect(db_path)
    conexion.execute(ESQUEMA)
    conexion.commit()
    conexion.close()

    def buscar_tarea(tarea_id):
        fila = obtener_db().execute(
            "SELECT * FROM tareas WHERE id = ?", (tarea_id,)
        ).fetchone()
        if fila is None:
            raise ErrorAPI(404, "La tarea no existe")
        return fila

    # ----------------------------------------------------------- manejo errores
    @app.errorhandler(ErrorAPI)
    def manejar_error_api(e):
        return jsonify({"error": e.mensaje}), e.codigo

    @app.errorhandler(HTTPException)
    def manejar_http(e):
        if request.path.startswith("/api"):
            return jsonify({"error": e.description or e.name}), e.code
        return e

    # ------------------------------------------------------------------- página
    @app.get("/")
    def index():
        return render_template("index.html")

    # ---------------------------------------------------------------------- API
    @app.post("/api/tareas")
    def crear_tarea():
        datos = leer_cuerpo_objeto()
        titulo = validar_titulo(datos.get("titulo"))
        descripcion = validar_descripcion(datos.get("descripcion"))
        prioridad = validar_prioridad(datos["prioridad"]) if "prioridad" in datos else "media"
        fecha = validar_fecha(datos.get("fecha_limite"))
        creada_en = datetime.now().isoformat(timespec="seconds")

        db = obtener_db()
        cursor = db.execute(
            "INSERT INTO tareas (titulo, descripcion, prioridad, fecha_limite, completada, creada_en) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (titulo, descripcion, prioridad, fecha, creada_en),
        )
        db.commit()
        return jsonify(tarea_a_dict(buscar_tarea(cursor.lastrowid))), 201

    @app.get("/api/tareas")
    def listar_tareas():
        estado = request.args.get("estado")
        if estado is not None and estado not in ESTADOS:
            raise ErrorAPI(400, "El estado debe ser 'pendiente' o 'completada'")
        q = (request.args.get("q") or "").strip().casefold()

        filas = obtener_db().execute("SELECT * FROM tareas ORDER BY id ASC").fetchall()
        resultado = []
        for fila in filas:
            if estado == "pendiente" and fila["completada"]:
                continue
            if estado == "completada" and not fila["completada"]:
                continue
            if q and q not in fila["titulo"].casefold() and q not in fila["descripcion"].casefold():
                continue
            resultado.append(tarea_a_dict(fila))
        return jsonify(resultado), 200

    @app.get("/api/tareas/<int:tarea_id>")
    def obtener_tarea(tarea_id):
        return jsonify(tarea_a_dict(buscar_tarea(tarea_id))), 200

    @app.put("/api/tareas/<int:tarea_id>")
    def editar_tarea(tarea_id):
        fila = buscar_tarea(tarea_id)                      # 404 primero
        if fila["completada"]:                             # 409 después
            raise ErrorAPI(409, "Una tarea completada no se puede editar")
        datos = leer_cuerpo_objeto()                       # 400 al final
        campos = ("titulo", "descripcion", "prioridad", "fecha_limite")
        if not any(c in datos for c in campos):
            raise ErrorAPI(400, "Debe enviar al menos un campo editable")

        nuevos = {}
        if "titulo" in datos:
            nuevos["titulo"] = validar_titulo(datos["titulo"])
        if "descripcion" in datos:
            nuevos["descripcion"] = validar_descripcion(datos["descripcion"])
        if "prioridad" in datos:
            nuevos["prioridad"] = validar_prioridad(datos["prioridad"])
        if "fecha_limite" in datos:
            nuevos["fecha_limite"] = validar_fecha(datos["fecha_limite"])

        asignaciones = ", ".join(f"{c} = ?" for c in nuevos)
        db = obtener_db()
        db.execute(
            f"UPDATE tareas SET {asignaciones} WHERE id = ?",
            (*nuevos.values(), tarea_id),
        )
        db.commit()
        return jsonify(tarea_a_dict(buscar_tarea(tarea_id))), 200

    @app.post("/api/tareas/<int:tarea_id>/completar")
    def completar_tarea(tarea_id):
        fila = buscar_tarea(tarea_id)
        if fila["completada"]:
            raise ErrorAPI(409, "La tarea ya estaba completada")
        db = obtener_db()
        db.execute("UPDATE tareas SET completada = 1 WHERE id = ?", (tarea_id,))
        db.commit()
        return jsonify(tarea_a_dict(buscar_tarea(tarea_id))), 200

    @app.delete("/api/tareas/<int:tarea_id>")
    def eliminar_tarea(tarea_id):
        buscar_tarea(tarea_id)
        db = obtener_db()
        db.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        db.commit()
        return "", 204

    return app