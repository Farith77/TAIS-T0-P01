# Especificación del sistema web de gestión de tareas

**Experimento:** Desarrollo tradicional frente a desarrollo asistido por un agente de IA de terminal
**Versión:** 1.0 (congelada el 07/11/2026; no cambia durante la sesión)

> La especificación es el oráculo. Cuando el código y este documento no coincidan, manda este documento. Lo que no está escrito aquí no se exige.

---

## 1. Qué hace el sistema

Una aplicación web, para un solo usuario y sin inicio de sesión, que permite registrar tareas, editarlas, eliminarlas, buscarlas y marcarlas como completadas. Tiene dos partes:

- una **API JSON** bajo `/api/tareas`, que es la que evalúa la batería de pruebas de aceptación;
- una **página web** en `/`, que usa esa funcionalidad y se revisa con una lista de verificación manual (R14).

## 2. Stack obligatorio

| Elemento | Decisión |
|---|---|
| Lenguaje | Python 3.11 o superior |
| Framework web | Flask 3.x |
| Base de datos | SQLite, con el módulo `sqlite3` de la biblioteca estándar (no se permite un ORM) |
| Interfaz | Plantillas Jinja de Flask, HTML, CSS y JavaScript sin frameworks ni CDN |
| Dependencias | Solo las de `requirements.txt` (Flask). No se instalan otras |

## 3. Contrato técnico (obligatorio para que el sistema pueda evaluarse)

1. En la raíz del repositorio existe el archivo `app.py`.
2. `app.py` define la función `create_app(db_path)`, que recibe la ruta del archivo SQLite y devuelve la aplicación Flask.
3. `create_app` crea las tablas si no existen. No se necesita ningún paso manual antes de usar el sistema.
4. Todos los datos se guardan en el archivo `db_path`. No se usan variables globales para guardar tareas.
5. El sistema se arranca con `flask --app app run` (puede usar un `db_path` por defecto, por ejemplo `tareas.db`).

```python
# Firma exigida
def create_app(db_path: str = "tareas.db") -> Flask: ...
```

Si `app.py` no existe o `create_app` no tiene esa firma, la batería no puede ejecutarse y la entrega cuenta con 0 pruebas aprobadas.

## 4. Modelo de datos: la tarea

| Campo | Tipo en JSON | Regla |
|---|---|---|
| `id` | entero | Lo asigna el sistema. Empieza en 1, crece de uno en uno y **no se reutiliza** aunque se eliminen tareas (R11). |
| `titulo` | texto | Obligatorio (R2). |
| `descripcion` | texto | Opcional, por defecto `""` (R3). |
| `prioridad` | texto | Opcional, por defecto `"media"` (R4). |
| `fecha_limite` | texto `"AAAA-MM-DD"` o `null` | Opcional, por defecto `null` (R5). |
| `completada` | booleano | La asigna el sistema: `false` al crear; cambia solo con R10. |
| `creada_en` | texto | Fecha y hora de creación en formato ISO 8601, asignada por el sistema. |

Toda respuesta que devuelve una tarea incluye **los siete campos** con esos nombres exactos.

## 5. Reglas

### R1. Crear una tarea
`POST /api/tareas` con un cuerpo JSON. Si los datos cumplen R2 a R5, responde **201** con la tarea creada (los siete campos). Los campos opcionales que no se envían toman su valor por defecto. Los campos desconocidos se ignoran. Si el cliente envía `id`, `completada` o `creada_en`, se ignoran.

### R2. Título
- Debe estar presente y ser texto.
- Se eliminan los espacios al inicio y al final, y **se guarda recortado**.
- Después de recortar, debe tener **entre 3 y 100 caracteres, ambos incluidos**.
- Si falta, no es texto o su longitud queda fuera de ese rango, responde **400**.

### R3. Descripción
- Es opcional. Si no se envía o se envía `null`, se guarda `""`.
- Si se envía, debe ser texto. Se eliminan los espacios al inicio y al final y se guarda recortada.
- Después de recortar, puede tener **como máximo 500 caracteres**. Si tiene más, o no es texto, responde **400**.

### R4. Prioridad
- Es opcional. Si no se envía, vale `"media"`.
- Solo se aceptan exactamente `"alta"`, `"media"` o `"baja"`, en minúsculas. Cualquier otro valor (incluidos `"Alta"`, `""` o `null`) responde **400**.

### R5. Fecha límite
- Es opcional. Si no se envía o se envía `null`, se guarda `null`.
- Si se envía, debe ser un texto con formato `AAAA-MM-DD` que corresponda a una fecha real del calendario (`"2026-02-30"` no es válida).
- **No puede ser anterior a la fecha actual del servidor.** La fecha de hoy sí es válida.
- Si no cumple, responde **400**. Esta regla se aplica al crear (R1) y al editar (R9).

### R6. Listar tareas
`GET /api/tareas` responde **200** con una lista JSON de tareas **ordenada por `id` ascendente**. Si no hay tareas, responde `[]`.

### R7. Buscar y filtrar
`GET /api/tareas` acepta dos parámetros opcionales que se pueden combinar (se deben cumplir ambos):
- `q`: devuelve solo las tareas cuyo `titulo` **o** `descripcion` contienen el texto de `q`, **sin distinguir mayúsculas de minúsculas**. Se eliminan los espacios al inicio y al final de `q`; si queda vacío, no se filtra.
- `estado`: `pendiente` devuelve las tareas con `completada = false`; `completada` devuelve las de `completada = true`. Cualquier otro valor responde **400**.

El resultado mantiene el orden de R6.

### R8. Consultar una tarea
`GET /api/tareas/<id>` responde **200** con la tarea, o **404** si no existe.

### R9. Editar una tarea
`PUT /api/tareas/<id>` con un cuerpo JSON que contiene **uno o más** de estos campos: `titulo`, `descripcion`, `prioridad`, `fecha_limite`.
- Cada campo enviado se valida con su regla (R2 a R5). Los campos que no se envían conservan su valor.
- Si todo es válido, responde **200** con la tarea actualizada.
- Si el cuerpo no trae ninguno de esos cuatro campos, responde **400**.
- Si algún campo es inválido, responde **400** y **no se modifica ningún campo**.
- Una tarea completada no se puede editar: responde **409**.
- Si se cumplen varias condiciones de error, se responde la primera de este orden: **404** (no existe), **409** (completada), **400** (datos inválidos).

### R10. Marcar como completada
`POST /api/tareas/<id>/completar` (sin cuerpo).
- Si la tarea está pendiente, la marca como completada y responde **200** con la tarea (`completada: true`).
- Si ya estaba completada, responde **409** y la tarea no cambia.
- Si no existe, responde **404**.

### R11. Eliminar una tarea
`DELETE /api/tareas/<id>` responde **204** sin cuerpo y la tarea deja de existir: después, `GET /api/tareas/<id>` responde 404 y no aparece en la lista. Si no existe, responde **404**. Los `id` eliminados no se vuelven a asignar.

### R12. Formato de los errores
- Toda respuesta **400, 404 o 409** de la API tiene un cuerpo JSON con la forma `{"error": "<mensaje>"}`. El texto del mensaje es libre.
- Si en `POST` o `PUT` el cuerpo no es JSON válido o no es un objeto JSON (por ejemplo, una lista), responde **400**.

### R13. Persistencia
Los datos se guardan en el archivo SQLite indicado en `create_app(db_path)`. Si se crea una segunda aplicación con la misma ruta, ve las mismas tareas.

### R14. Página web
`GET /` responde **200** con una página HTML que permite, sin usar herramientas externas:
1. ver la lista de tareas con título, prioridad, fecha límite y estado;
2. crear una tarea (título, descripción, prioridad y fecha límite);
3. buscar por texto (R7);
4. editar una tarea pendiente;
5. marcar una tarea como completada;
6. eliminar una tarea.

Cuando una operación falla por validación, la página muestra el mensaje de error al usuario. El diseño visual no se evalúa.

## 6. Ejemplos

```http
POST /api/tareas
{"titulo": "  Preparar informe  ", "prioridad": "alta", "fecha_limite": "2026-12-01"}

201
{"id": 1, "titulo": "Preparar informe", "descripcion": "", "prioridad": "alta",
 "fecha_limite": "2026-12-01", "completada": false, "creada_en": "2026-11-08T09:15:02"}
```

```http
POST /api/tareas
{"titulo": "ab"}

400
{"error": "El título debe tener entre 3 y 100 caracteres"}
```

```http
GET /api/tareas?q=INFORME&estado=pendiente

200
[{"id": 1, "titulo": "Preparar informe", ...}]
```

## 7. Cómo se evalúa

1. Cuando el participante declara que terminó (**entrega 1**), se ejecuta la batería de pruebas de aceptación sobre el commit entregado. La batería verifica R1 a R13 y la existencia de la página (R14). El participante no ve el código de las pruebas: recibe la lista de reglas y nombres de prueba que fallaron.
2. El participante corrige y vuelve a entregar (entrega 2, 3, …) hasta aprobar el 100 % o llegar al tope de 6 horas de sesión.
3. La página web (R14) se revisa con la lista de verificación de la hoja de registro.
