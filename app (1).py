import os
import re

import streamlit as st
from bson import ObjectId
from pymongo import MongoClient

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="CRUD de Estudiantes",
    page_icon="🎓",
    layout="wide",
)

DB_NAME = "universidad"
COLLECTION_NAME = "estudiantes"


# ============================================================
# CONEXIÓN SEGURA CON MONGODB ATLAS
# Define MONGODB_CONNECTION_STRING en Streamlit Cloud → Secrets.
# No guardes la URI ni la contraseña directamente en este archivo.
# ============================================================
@st.cache_resource(show_spinner="Conectando con MongoDB Atlas...")
def get_mongo_client():
    # uri = None

    # try:
    #     uri = st.secrets.get("MONGODB_CONNECTION_STRING")
    # except Exception:
    #     pass

    # if not uri:
    #     uri = os.environ.get("MONGODB_CONNECTION_STRING")

    # if not uri:
    #     raise ValueError(
    #         "Falta MONGODB_CONNECTION_STRING. "
    #         "Configúrala en Streamlit Cloud → Settings → Secrets "
    #         "o como variable de entorno MONGODB_CONNECTION_STRING."
    #     )

    # client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    # client.admin.command("ping")
    #  Conectarse a MongoDB (por defecto al localhost en el puerto 27017)
    client = MongoClient('mongodb+srv://daquinonesv_db_user:BED2hp9bUTWZfMSu@clustergrupo2.ckoyg3n.mongodb.net/')

    # Eliminar la base de datos
    # client.drop_database('universidad')

    #  Seleccionar base de datos (se crea si no existe)

    return client


try:
    client = get_mongo_client()
    db = client['universidad']
    estudiantes = db['estudiantes']
except Exception as error:
    st.error(
        "No se pudo conectar a MongoDB Atlas. Revisa la URI, "
        "las credenciales y la configuración de acceso de red."
    )
    st.exception(error)
    st.stop()


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def validar_correo(correo):
    return (
        re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo.strip())
        is not None
    )


def mostrar_documentos(documentos):
    if not documentos:
        st.info("No hay estudiantes que mostrar.")
        return

    for documento in documentos:
        doc = dict(documento)
        doc["_id"] = str(doc["_id"])
        id_corto = doc["_id"][-6:]
        nombre = doc.get("nombre", "Sin nombre")

        with st.expander(f"{nombre} · ID ...{id_corto}"):
            st.json(doc)


def seleccionar_estudiante(key):
    documentos = list(estudiantes.find().sort("nombre", 1))

    if not documentos:
        st.info("La colección universidad.estudiantes está vacía.")
        return None, None

    opciones = {str(doc["_id"]): doc for doc in documentos}

    id_seleccionado = st.selectbox(
        "Selecciona un estudiante",
        options=list(opciones.keys()),
        format_func=lambda id_texto: (
            f'{opciones[id_texto].get("nombre", "Sin nombre")} '
            f'— {opciones[id_texto].get("correo", "Sin correo")} '
            f'· ID ...{id_texto[-6:]}'
        ),
        key=key,
    )
    return id_seleccionado, opciones[id_seleccionado]


# ============================================================
# INTERFAZ CRUD: universidad.estudiantes
# Campos: nombre, edad, correo, hobbies
# ============================================================
st.title("🎓 Gestión de estudiantes")
st.caption("Base de datos: `universidad` | Colección: `estudiantes`")

crear, buscar, actualizar, borrar = st.tabs(
    ["➕ Crear", "🔎 Buscar", "✏️ Actualizar", "🗑️ Borrar"]
)

with crear:
    st.subheader("Registrar estudiante")

    with st.form("form_crear_estudiante", clear_on_submit=True):
        nombre = st.text_input("Nombre completo *")
        edad = st.number_input("Edad", min_value=0, max_value=120, value=20)
        correo = st.text_input("Correo electrónico *")
        hobbies_texto = st.text_input(
            "Hobbies separados por coma",
            placeholder="Lectura, música, deportes",
        )
        guardar_nuevo = st.form_submit_button(
            "Guardar estudiante", type="primary"
        )

    if guardar_nuevo:
        nombre_limpio = nombre.strip()
        correo_limpio = correo.strip().lower()
        hobbies = [h.strip() for h in hobbies_texto.split(",") if h.strip()]

        if not nombre_limpio:
            st.warning("El nombre es obligatorio.")
        elif not validar_correo(correo_limpio):
            st.warning("Escribe un correo electrónico válido.")
        elif estudiantes.find_one({"correo": correo_limpio}):
            st.warning("Ya existe un estudiante con ese correo.")
        else:
            estudiantes.insert_one(
                {
                    "nombre": nombre_limpio,
                    "edad": int(edad),
                    "correo": correo_limpio,
                    "hobbies": hobbies,
                }
            )
            st.success(f"Se registró a {nombre_limpio}.")
            st.rerun()

with buscar:
    st.subheader("Consultar estudiantes")
    modo = st.radio(
        "Buscar por",
        ["Todos", "Nombre", "Edad mayor que"],
        horizontal=True,
        key="modo_busqueda",
    )

    if modo == "Nombre":
        texto = st.text_input("Nombre o parte del nombre", key="buscar_nombre")
        filtro = (
            {"nombre": {"$regex": re.escape(texto.strip()), "$options": "i"}}
            if texto.strip()
            else {}
        )
    elif modo == "Edad mayor que":
        edad_minima = st.number_input(
            "Edad mínima (se buscarán edades mayores)",
            min_value=0,
            max_value=120,
            value=18,
            key="buscar_edad",
        )
        filtro = {"edad": {"$gt": int(edad_minima)}}
    else:
        filtro = {}

    if st.button("Buscar estudiantes", key="btn_buscar"):
        mostrar_documentos(list(estudiantes.find(filtro).sort("nombre", 1)))

with actualizar:
    st.subheader("Actualizar estudiante")
    id_texto, doc = seleccionar_estudiante("selector_actualizar")

    if doc:
        hobbies_actuales = doc.get("hobbies", [])
        if not isinstance(hobbies_actuales, list):
            hobbies_actuales = []

        try:
            edad_actual = int(doc.get("edad", 20))
        except (TypeError, ValueError):
            edad_actual = 20
        edad_actual = max(0, min(120, edad_actual))

        with st.form("form_actualizar_estudiante"):
            nombre_nuevo = st.text_input(
                "Nombre", value=str(doc.get("nombre", ""))
            )
            edad_nueva = st.number_input(
                "Edad",
                min_value=0,
                max_value=120,
                value=edad_actual,
            )
            correo_nuevo = st.text_input(
                "Correo electrónico", value=str(doc.get("correo", ""))
            )
            hobbies_nuevos = st.text_input(
                "Hobbies separados por coma",
                value=", ".join(str(h) for h in hobbies_actuales),
            )
            guardar_cambios = st.form_submit_button(
                "Guardar cambios", type="primary"
            )

        if guardar_cambios:
            nombre_limpio = nombre_nuevo.strip()
            correo_limpio = correo_nuevo.strip().lower()
            hobbies = [
                h.strip() for h in hobbies_nuevos.split(",") if h.strip()
            ]

            if not nombre_limpio:
                st.warning("El nombre es obligatorio.")
            elif not validar_correo(correo_limpio):
                st.warning("Escribe un correo electrónico válido.")
            elif estudiantes.find_one(
                {
                    "correo": correo_limpio,
                    "_id": {"$ne": ObjectId(id_texto)},
                }
            ):
                st.warning("Ese correo ya pertenece a otro estudiante.")
            else:
                estudiantes.update_one(
                    {"_id": ObjectId(id_texto)},
                    {
                        "$set": {
                            "nombre": nombre_limpio,
                            "edad": int(edad_nueva),
                            "correo": correo_limpio,
                            "hobbies": hobbies,
                        }
                    },
                )
                st.success("Estudiante actualizado.")
                st.rerun()

with borrar:
    st.subheader("Eliminar estudiante")
    id_texto, doc = seleccionar_estudiante("selector_borrar")

    if doc:
        st.write(f'**Nombre:** {doc.get("nombre", "")}')
        st.write(f'**Correo:** {doc.get("correo", "")}')
        confirmar = st.checkbox(
            "Confirmo que deseo eliminar este estudiante",
            key=f"confirmar_borrar_{id_texto}",
        )

        if st.button(
            "Eliminar estudiante",
            type="primary",
            disabled=not confirmar,
            key="btn_borrar",
        ):
            estudiantes.delete_one({"_id": ObjectId(id_texto)})
            st.success("Estudiante eliminado.")
            st.rerun()
