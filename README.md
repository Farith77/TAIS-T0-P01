# Repositorio inicial del participante

Cada participante recibe una copia idéntica de este repositorio (`P01` a `P04`) y construye el sistema descrito en `ESPECIFICACION.md`.

## Antes de empezar (preparar el sábado, no el domingo)

```bash
python --version                      # 3.11 o superior
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run                   # debe arrancar sin errores (la página aún no existe)
```

- **T0 (tradicional):** desactiven todo asistente de IA del editor (Copilot, Codeium, Cursor Tab, IntelliCode con IA, etc.) y comprueben que el autocompletado de IA está apagado.
- **T1 (agente):** dejen instalado y con sesión iniciada el agente de terminal de su plan de USD 20 al mes, y tengan a mano el comprobante del plan.
- Creen la carpeta `evidencias/` en el repositorio para guardar las capturas de pantalla.

## Reglas de la sesión

1. Solo se instala lo que está en `requirements.txt`. No se agregan dependencias.
2. Se respeta el contrato técnico de la especificación: `app.py` en la raíz con `create_app(db_path)`.
3. Commits obligatorios con estos mensajes exactos, para que las horas se puedan verificar en el historial:

| Momento | Mensaje del commit |
|---|---|
| Al empezar (sin cambios, usar `--allow-empty`) | `inicio` |
| Cuando declaran que terminaron | `entrega 1` |
| Después de cada corrección | `entrega 2`, `entrega 3`, … |

4. Cada cambio de actividad se anota en la bitácora (hoja `bitacora` del Excel), con los códigos de la Hoja de registro.
5. Capturas de pantalla en cada hito (inicio, cada entrega y cierre), con la terminal mostrando `git log -1 --format="%h %ci %s"`. Se guardan en `evidencias/` como `P0X_01_inicio.png`, `P0X_02_entrega1.png`, etc.
6. El tope es de **6 horas** de trabajo (sin contar las pausas anotadas como `PAU`).
