"""Sistema web de gestión de tareas. Contrato: ver ESPECIFICACION.md, sección 3."""
from flask import Flask


def create_app(db_path: str = "tareas.db") -> Flask:
    app = Flask(__name__)
    # Implementar aquí (o en otros módulos del repositorio) las reglas R1 a R14.
    return app
