import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os


# 1. CONFIGURACIÓN DE LA PÁGINA (OBLIGATORIO: DEBE SER LO PRIMERO)

st.set_page_config(
    page_title="Tasador CABA",
    page_icon="🏠",
    layout="centered"
)


# 2. CARGA DEL MODELO (CACHEADA)

@st.cache_resource
def cargar_modelo():
    
    ruta_modelo = os.path.join("modelos", "modelo_inmuebles_pack.pkl")
    
    if not os.path.exists(ruta_modelo):
        return None, None
        
    pack = joblib.load(ruta_modelo)
    return pack['modelo'], pack['columnas']

# Ejecutamos la carga
modelo, columnas_entrenamiento = cargar_modelo()

# 3. BARRA LATERAL (PERFIL Y DESCRIPCIÓN)
with st.sidebar:
    st.header("Contacto")
    
    # --- SECCIÓN DE LINKS ---
    linkedin_url = "https://www.linkedin.com/in/ruthncruz/"  
    github_url = "https://github.com/RuthCruz09"    
    notion_url = "#" 

    # Badges (Escudos)
    st.markdown(f"""
        <a href="{linkedin_url}" target="_blank">
            <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
        </a>
        <br>
        <a href="{github_url}" target="_blank">
            <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
        </a>
        <br>
        <a href="{notion_url}" target="_blank">
            <img src="https://img.shields.io/badge/Portfolio-Notion-000000?style=for-the-badge&logo=notion&logoColor=white" alt="Notion Portfolio">
        </a>
        """, unsafe_allow_html=True)

    st.divider()

    # --- DESCRIPCIÓN DEL PROYECTO ---
    st.subheader("🚀 Pipeline del Proyecto")
    st.info("""
    Este proyecto representa un flujo de trabajo completo de Data Science:

    1.  🕷️ **Web Scraping:** Extracción de datos crudos provenientes de la pag. web  *Inmuebles Clarín*.
    2.  🧹 **Limpieza y ETL:** Tratamiento de nulos, duplicados y estandarización.
    3.  📊 **EDA:** Análisis Exploratorio para entender los factores del mercado inmobiliario de CABA.
    4.  🤖 **Machine Learning:** Entrenamiento y optimización de un modelo **Random Forest**.
    5.  🚀 **Deployment:** Desarrollo de esta interfaz interactiva con **Streamlit**.
    """)
    
    st.caption("Autora : Ruth Cruz")


# 4. INTERFAZ PRINCIPAL (FRONTEND)


# Header
st.title(" Tasador de departamentos ubicados en CABA")
st.markdown("""
Esta herramienta utiliza un modelo de **Machine Learning (Random Forest)** entrenado con datos reales 
del mercado de CABA para estimar el valor de venta de una propiedad.
""")
st.divider()

# Verificación de carga del modelo
if modelo is None:
    st.error("❌ Error Crítico: No se encuentra el archivo del modelo. Verifica que la carpeta 'models' exista y contenga el archivo .pkl")
    st.stop()

# Formulario de Inputs
with st.container():
    st.subheader("📝 Características de la Propiedad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sup_cubierta = st.number_input("Superficie Cubierta (m²)", min_value=20, max_value=500, value=60, step=1)
        ambientes = st.slider("Cantidad de Ambientes", 1, 7, 3)
        baños = st.slider("Cantidad de Baños", 1, 5, 1)

    with col2:
        cocheras = st.radio("¿Posee Cochera?", ["No", "Sí"], horizontal=True)
        valor_cochera = 1 if cocheras == "Sí" else 0
        
        # Expensas
        expensas = st.number_input("Expensas ($ARS)", min_value=0, value=30000, step=5000, help="Las expensas altas suelen indicar edificios con seguridad o amenities.")
        
        # Selector de Barrio
        if columnas_entrenamiento:
            barrios_disponibles = [col.replace("barrio_", "") for col in columnas_entrenamiento if col.startswith("barrio_")]
            barrios_disponibles.sort()
            barrio_elegido = st.selectbox("Ubicación (Barrio)", barrios_disponibles)
        else:
            st.error("No se pudieron cargar los barrios del modelo.")
            st.stop()


# 5. LÓGICA DE PREDICCIÓN (BACKEND)
st.divider()

_, col_btn, _ = st.columns([1, 2, 1])

if col_btn.button("💰 Calcular Tasación Ahora", type="primary", use_container_width=True):
    
    # 1. Crear DataFrame vacío
    input_df = pd.DataFrame(columns=columnas_entrenamiento)
    input_df.loc[0] = 0 
    
    # 2. Llenar datos numéricos
    input_df.at[0, 'sup_cubierta'] = sup_cubierta
    input_df.at[0, 'ambientes'] = ambientes
    input_df.at[0, 'baños'] = baños
    input_df.at[0, 'dormitorios'] = max(1, ambientes - 1)
    input_df.at[0, 'cocheras'] = valor_cochera
    input_df.at[0, 'precio_expensas'] = expensas
    
    # 3. One-Hot Encoding del Barrio
    col_barrio = f"barrio_{barrio_elegido}"
    if col_barrio in input_df.columns:
        input_df.at[0, col_barrio] = 1
    
    # 4. Predicción
    try:
        prediccion_usd = modelo.predict(input_df)[0]
        precio_m2 = prediccion_usd / sup_cubierta
        
        # 5. Mostrar Resultados
        st.success("✅ Tasación Generada Exitosamente")
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric(label="Precio Estimado de Venta", value=f"USD {prediccion_usd:,.0f}")
        col_res2.metric(label="Valor por m²", value=f"USD {precio_m2:,.0f}")
        
        st.caption("⚠️ Nota: Esta es una estimación basada en IA y de los datos obtenidos de la página web 'Inmuebles Clarín'.")
        
    except Exception as e:
        st.error(f"Ocurrió un error al calcular: {e}")