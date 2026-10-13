import pandas as pd
import streamlit as st
from utils.data_loader import load_well_data
from utils.plot_engine import create_advanced_log_plot
from models.eaton import EatonModel
from models.bowers import BowersModel
from models.divergence import DivergenceModel

st.set_page_config(page_title="Predict.io - Geopressure Suite", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #1E90FF;'>Predict.io - Análisis de Estabilidad y Geopresiones</h1>
    <h4 style='text-align: center; color: gray;'>Configuración Especial: Amistad-015S1</h4>
    <hr>
""", unsafe_allow_html=True)

# 1. CARGA DE DATOS
st.sidebar.header("📂 1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Archivo Pozo (LAS, CSV)", type=None)
formato_manual = st.sidebar.selectbox("Formato (Si falla Auto)", ["Auto", "LAS", "CSV", "EXCEL"])

if uploaded_file is not None:
    with st.spinner("Procesando y sanitizando datos..."):
        df, error_msg = load_well_data(uploaded_file, file_format=formato_manual)
        
        if error_msg:
            st.sidebar.error(error_msg)
        elif df is not None:
            curvas_profundidad = [c for c in df.columns if c.upper() in ['DEPTH', 'DEPT', 'TVD', 'MD']]
            if not curvas_profundidad: curvas_profundidad = df.columns.tolist()
            
            # 2. CONFIGURACIÓN GEOMECÁNICA
            st.sidebar.header("⚙️ 2. Modelo y Calibración")
            col_prof = st.sidebar.selectbox("Curva de Profundidad", curvas_profundidad)
            modelo_seleccionado = st.sidebar.selectbox("Seleccionar Método Analítico", ["Eaton", "Bowers", "Divergencia (Athy)"])
            
            params = {'depth_col': col_prof, 'curve_type': 'Sonic'}
            params['rho_matrix'] = st.sidebar.number_input("Densidad Matriz (g/cm3)", value=2.65)
            
            if modelo_seleccionado == "Eaton":
                with st.sidebar.expander("Calibración NCTL (Eaton)", expanded=True):
                    st.caption("Ajusta la línea punteada para que coincida con las lutitas limpias.")
                    params['dt_ml'] = st.number_input("Intercepto Superficie (DT_ml)", value=175.0, step=1.0)
                    params['c_compaction'] = st.number_input("Factor Compactación (c)", value=0.00010, format="%.5f", step=0.00001)
            
            elif modelo_seleccionado == "Bowers":
                with st.sidebar.expander("Calibración Esfuerzo Efectivo (Bowers)", expanded=True):
                    st.caption("Ecuación Virgen: V = V_ml + A * (Sigma_e)^B")
                    params['bowers_vml'] = st.number_input("Velocidad Fondo Marino (ft/s)", value=5000.0, step=100.0)
                    params['bowers_a'] = st.number_input("Parámetro A", value=15.0, step=1.0)
                    params['bowers_b'] = st.number_input("Parámetro B", value=0.75, step=0.05)

            # 3. ZONIFICACIÓN DE PARÁMETROS OPERATIVOS EXACTOS (AMISTAD-015S1)
            st.sidebar.header("📊 3. Perfil de Presiones y MW")
            
            with st.sidebar.expander("Tabla de Operación (Valores Amistad-015S1)", expanded=True):
                # Data inyectada explícitamente desde el reporte de perforación
                op_data_base = pd.DataFrame([
                    {"profundidad": 400, "pp": 8.8, "pcol": 8.8, "mw": 9.2, "ecd": 9.4, "sh": 11.5, "fg": 12.0, "sv": 14.7, "eaton_exp": 3.0, "ppn": 8.6},
                    {"profundidad": 1578, "pp": 8.9, "pcol": 9.0, "mw": 9.4, "ecd": 9.8, "sh": 12.0, "fg": 12.68, "sv": 15.8, "eaton_exp": 3.0, "ppn": 8.6},
                    {"profundidad": 7006, "pp": 9.5, "pcol": 10.5, "mw": 10.8, "ecd": 11.1, "sh": 13.6, "fg": 14.76, "sv": 16.5, "eaton_exp": 3.0, "ppn": 8.9},
                    {"profundidad": 8000, "pp": 9.5, "pcol": 11.0, "mw": 11.2, "ecd": 11.6, "sh": 13.8, "fg": 16.8, "sv": 17.0, "eaton_exp": 3.0, "ppn": 9.2},
                    {"profundidad": 8500, "pp": 9.7, "pcol": 11.2, "mw": 11.3, "ecd": 11.7, "sh": 14.0, "fg": 17.0, "sv": 17.1, "eaton_exp": 3.0, "ppn": 9.2},
                    {"profundidad": 9000, "pp": 9.9, "pcol": 11.4, "mw": 11.5, "ecd": 11.9, "sh": 14.3, "fg": 17.1, "sv": 17.3, "eaton_exp": 3.0, "ppn": 9.6},
                    {"profundidad": 9999, "pp": 10.2, "pcol": 11.6, "mw": 11.6, "ecd": 12.0, "sh": 14.4, "fg": 17.2, "sv": 17.4, "eaton_exp": 3.0, "ppn": 9.8},
                    {"profundidad": 10677, "pp": 10.8, "pcol": 11.3, "mw": 12.0, "ecd": 12.2, "sh": 14.5, "fg": 18.0, "sv": 17.7, "eaton_exp": 3.0, "ppn": 10.5}
                ])
                op_df = st.data_editor(op_data_base, num_rows="dynamic", use_container_width=True)
            
            # Reestructurar zonas para pasarlo al modelo
            zonas_params = []
            prev_depth = 0
            for index, row in op_df.iterrows():
                zonas_params.append({"start": prev_depth, "end": row["profundidad"], "eaton_exp": row["eaton_exp"], "ppn": row["ppn"]})
                prev_depth = row["profundidad"]
            params['params_zones'] = zonas_params

            # Controles de Visualización
            st.sidebar.markdown("---")
            plot_height = st.sidebar.slider("🔍 Zoom Vertical (Píxeles)", min_value=800, max_value=4000, value=1200, step=100)

            # Ejecutar Modelos
            with st.spinner("Calculando red neuronal geomecánica..."):
                if modelo_seleccionado == "Eaton":
                    modelo = EatonModel(df, params)
                elif modelo_seleccionado == "Bowers":
                    modelo = BowersModel(df, params)
                else:
                    modelo = DivergenceModel(df, params)
                    
                resultados = modelo.run()
                
                # Renderizar Plotly
                fig = create_advanced_log_plot(resultados, zones=None, op_data=op_df, plot_height=plot_height, curve_type=params['curve_type'])
                st.plotly_chart(fig, width="stretch", theme=None) # theme=None obliga a usar la plantilla estricta de Plotly_dark