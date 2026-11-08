const $ = (selector) => document.querySelector(selector);
let editandoId = null;

async function api(url, opciones = {}) {
  const respuesta = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new Error(datos && datos.error ? datos.error : "Error " + respuesta.status);
  }
  return datos;
}

function mostrarMensaje(texto) {
  const caja = $("#mensaje");
  caja.textContent = texto;
  caja.hidden = !texto;
}

async function ejecutar(accion) {
  try {
    mostrarMensaje("");
    await accion();
  } catch (error) {
    mostrarMensaje(error.message);
  }
}

function crearBoton(texto, alHacerClic) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.textContent = texto;
  boton.addEventListener("click", alHacerClic);
  return boton;
}

function dibujarTarea(tarea) {
  const item = document.createElement("li");
  if (tarea.completada) item.classList.add("completada");

  const titulo = document.createElement("strong");
  titulo.textContent = tarea.titulo;

  const meta = document.createElement("p");
  meta.className = "meta";
  meta.textContent =
    "Prioridad: " + tarea.prioridad +
    " | Fecha límite: " + (tarea.fecha_limite || "sin fecha") +
    " | Estado: " + (tarea.completada ? "completada" : "pendiente");

  item.append(titulo, meta);

  if (tarea.descripcion) {
    const descripcion = document.createElement("p");
    descripcion.textContent = tarea.descripcion;
    item.append(descripcion);
  }

  const acciones = document.createElement("div");
  acciones.className = "fila";
  if (!tarea.completada) {
    acciones.append(
      crearBoton("Editar", () => empezarEdicion(tarea)),
      crearBoton("Completar", () =>
        ejecutar(async () => {
          await api("/api/tareas/" + tarea.id + "/completar", { method: "POST" });
          await cargarLista();
        })
      )
    );
  }
  acciones.append(
    crearBoton("Eliminar", () =>
      ejecutar(async () => {
        await api("/api/tareas/" + tarea.id, { method: "DELETE" });
        if (editandoId === tarea.id) terminarEdicion();
        await cargarLista();
      })
    )
  );
  item.append(acciones);
  return item;
}

async function cargarLista() {
  const parametros = new URLSearchParams();
  const q = $("#q").value.trim();
  const estado = $("#estado").value;
  if (q) parametros.set("q", q);
  if (estado) parametros.set("estado", estado);

  const tareas = await api("/api/tareas?" + parametros.toString());
  const lista = $("#lista");
  lista.replaceChildren();
  if (tareas.length === 0) {
    const vacio = document.createElement("li");
    vacio.textContent = "No hay tareas para mostrar.";
    lista.append(vacio);
    return;
  }
  tareas.forEach((tarea) => lista.append(dibujarTarea(tarea)));
}

function empezarEdicion(tarea) {
  editandoId = tarea.id;
  $("#titulo").value = tarea.titulo;
  $("#descripcion").value = tarea.descripcion;
  $("#prioridad").value = tarea.prioridad;
  $("#fecha_limite").value = tarea.fecha_limite || "";
  $("#titulo-form").textContent = "Editar tarea";
  $("#btn-guardar").textContent = "Guardar cambios";
  $("#btn-cancelar").hidden = false;
  mostrarMensaje("");
  $("#titulo").focus();
}

function terminarEdicion() {
  editandoId = null;
  $("#form-tarea").reset();
  $("#titulo-form").textContent = "Nueva tarea";
  $("#btn-guardar").textContent = "Crear tarea";
  $("#btn-cancelar").hidden = true;
}

$("#form-tarea").addEventListener("submit", (evento) => {
  evento.preventDefault();
  ejecutar(async () => {
    const cuerpo = {
      titulo: $("#titulo").value,
      descripcion: $("#descripcion").value,
      prioridad: $("#prioridad").value,
      fecha_limite: $("#fecha_limite").value || null,
    };
    if (editandoId === null) {
      await api("/api/tareas", { method: "POST", body: JSON.stringify(cuerpo) });
    } else {
      await api("/api/tareas/" + editandoId, { method: "PUT", body: JSON.stringify(cuerpo) });
    }
    terminarEdicion();
    await cargarLista();
  });
});

$("#btn-cancelar").addEventListener("click", () => {
  terminarEdicion();
  mostrarMensaje("");
});

$("#form-busqueda").addEventListener("submit", (evento) => {
  evento.preventDefault();
  ejecutar(cargarLista);
});

ejecutar(cargarLista);