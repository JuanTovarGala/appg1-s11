import streamlit as st
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuración de página
st.set_page_config(page_title="CRUD Estudiantes", page_icon="🎓", layout="wide")

# URI de conexión directa a MongoDB Atlas
MONGO_URI = "mongodb+srv://jltrujillod_db_user:Itb3XsGMXEdF6FkB@numberone.t152kkb.mongodb.net/"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client["universidad"]
    coleccion = db["estudiantes_v2"]
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.title("🎓 Panel de Control CRUD - Estudiantes")
st.markdown("Gestión interactiva de la base de datos `universidad` en MongoDB Atlas.")

# Estructura en 2 columnas
col_izquierda, col_derecha = st.columns([1, 1])

with col_izquierda:
    st.subheader("⚡ Panel de Operaciones")

    # OPERACIÓN: LEER
    with st.expander("🔍 Operación: LEER (Read)", expanded=True):
        buscar_nombre = st.text_input("Nombre a buscar:", key="search_name")
        btn_leer = st.button("🔍 Buscar / Mostrar Todo")

    # OPERACIÓN: CREAR
    with st.expander("➕ Operación: CREAR (Create)", expanded=False):
        nuevo_nombre = st.text_input("Nombre completo:", key="create_name")
        nueva_edad = st.number_input("Edad:", min_value=1, max_value=120, value=20, key="create_age")
        nuevo_correo = st.text_input("Correo electrónico:", key="create_email")
        ciudad = st.text_input("Ciudad:", "Lima", key="create_city")
        btn_crear = st.button("➕ Registrar Estudiante")

    # Cargar lista actualizada de estudiantes para selectboxes
    estudiantes_lista = list(coleccion.find({}))
    opciones_dict = {f"{e.get('nombre')} ({e['_id']})": e for e in estudiantes_lista}

    # OPERACIÓN: ACTUALIZAR
    with st.expander("✏️ Operación: ACTUALIZAR (Update)", expanded=False):
        if opciones_dict:
            seleccionado_upd = st.selectbox("Seleccionar estudiante a actualizar:", list(opciones_dict.keys()), key="upd_sel")
            est_doc = opciones_dict[seleccionado_upd]
            nueva_edad_upd = st.number_input("Nueva Edad:", value=int(est_doc.get("edad", 20)), key="upd_age")
            nueva_ciudad_upd = st.text_input("Nueva Ciudad:", value=est_doc.get("direccion", {}).get("ciudad", ""), key="upd_city")
            btn_update = st.button("✏️ Actualizar Datos")
        else:
            st.warning("No hay registros disponibles para actualizar.")
            btn_update = False

    # OPERACIÓN: ELIMINAR
    with st.expander("🗑️ Operación: ELIMINAR (Delete)", expanded=False):
        if opciones_dict:
            seleccionado_del = st.selectbox("Seleccionar estudiante a eliminar:", list(opciones_dict.keys()), key="del_sel")
            btn_eliminar = st.button("🗑️ Eliminar Registro", type="primary")
        else:
            st.warning("No hay registros disponibles para eliminar.")
            btn_eliminar = False

with col_derecha:
    st.subheader("📊 Resultados y Consulta")

    if btn_leer:
        st.info("Consultando base de datos...")
        query = {}
        if buscar_nombre:
            query["nombre"] = {"$regex": buscar_nombre, "$options": "i"}
        resultados = list(coleccion.find(query))
        st.success(f"Se encontraron {len(resultados)} registro(s).")
        for doc in resultados:
            st.json({k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()})

    elif btn_crear:
        if nuevo_nombre:
            nuevo_registro = {
                "nombre": nuevo_nombre,
                "edad": nueva_edad,
                "correo": nuevo_correo,
                "direccion": {"ciudad": ciudad}
            }
            res = coleccion.insert_one(nuevo_registro)
            st.success(f"✅ Estudiante registrado con ID: {res.inserted_id}")
            st.json(nuevo_registro)
            st.rerun()
        else:
            st.warning("Por favor ingrese al menos el nombre.")

    elif btn_update and 'seleccionado_upd' in locals():
        est_doc = opciones_dict[seleccionado_upd]
        res = coleccion.update_one(
            {"_id": est_doc["_id"]},
            {"$set": {"edad": nueva_edad_upd, "direccion.ciudad": nueva_ciudad_upd}}
        )
        st.success("✅ Registro actualizado con éxito.")
        st.rerun()

    elif btn_eliminar and 'seleccionado_del' in locals():
        est_doc = opciones_dict[seleccionado_del]
        res = coleccion.delete_one({"_id": est_doc["_id"]})
        st.success("✅ Registro eliminado con éxito.")
        st.rerun()

    else:
        st.markdown("👉 *Selecciona o ejecuta una acción en el panel izquierdo para interactuar.*")
        st.markdown("### Vista rápida actual de la base de datos:")
        actuales = list(coleccion.find({}))
        for doc in actuales:
            st.json({k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()})
