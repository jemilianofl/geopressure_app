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
    <h4 style='text-align: center; color: gray;'>Locación: Pozo Amistad-015S1</h4>
    <hr>
""", unsafe_allow_html=True)

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
            modelo_seleccionado = st.sidebar.selectbox("Método Analítico", ["Eaton", "Bowers", "Divergencia (Athy)"])
            
            params = {'depth_col': col_prof, 'curve_type': 'Sonic'}
            
            with st.sidebar.expander("Propiedades de Matriz y Esfuerzos", expanded=False):
                params['rho_matrix'] = st.number_input("Densidad Matriz (g/cm3)", value=2.65)
                params['biot_alpha'] = st.number_input("Coeficiente de Biot (α)", value=1.0, min_value=0.0, max_value=1.0, step=0.05, help="1.0 para rocas no consolidadas")
                params['poisson_ratio'] = st.number_input("Relación de Poisson (ν)", value=0.40, min_value=0.1, max_value=0.5, step=0.01, help="Dejar en 0.4 para arcillas/arenas blandas. Si el LAS tiene curva POIS, se usará automáticamente.")
            
            if modelo_seleccionado == "Eaton":
                with st.sidebar.expander("Calibración NCTL", expanded=True):
                    params['dt_ml'] = st.number_input("DT Lecho Marino", value=175.0, step=1.0)
                    params['c_compaction'] = st.number_input("Factor Compactación (c)", value=0.00010, format="%.5f", step=0.00001)
            elif modelo_seleccionado == "Bowers":
                with st.sidebar.expander("Esfuerzo Efectivo (Bowers)", expanded=True):
                    params['bowers_vml'] = st.number_input("Velocidad Fondo Marino (ft/s)", value=5000.0, step=100.0)
                    params['bowers_a'] = st.number_input("Parámetro A Global", value=15.0, step=1.0)
                    params['bowers_b'] = st.number_input("Parámetro B Global", value=0.75, step=0.05)
                    
            st.sidebar.header("📊 3. Parámetros Estratigráficos (Amistad-015S1)")
            with st.sidebar.expander("Zonificación por Formación", expanded=True):
                # Usamos los topes de las formaciones como intervalos de calibración
                base_data = [
                    {"formacion": "Spud Mud", "profundidad": 400, "pp_op": 8.8, "pcol": 8.8, "mw": 9.2, "ecd": 9.4, "sh": 11.5, "fg": 12.0, "sv": 14.7},
                    {"formacion": "Fm. Puna", "profundidad": 1578, "pp_op": 8.9, "pcol": 9.0, "mw": 9.4, "ecd": 9.8, "sh": 12.0, "fg": 12.68, "sv": 15.8},
                    {"formacion": "Fm. Progreso", "profundidad": 7006, "pp_op": 9.5, "pcol": 10.5, "mw": 10.8, "ecd": 11.1, "sh": 13.6, "fg": 14.76, "sv": 16.5},
                    {"formacion": "Progreso Int 1", "profundidad": 8000, "pp_op": 9.5, "pcol": 11.0, "mw": 11.2, "ecd": 11.6, "sh": 13.8, "fg": 16.8, "sv": 17.0},
                    {"formacion": "Progreso Int 2", "profundidad": 8500, "pp_op": 9.7, "pcol": 11.2, "mw": 11.3, "ecd": 11.7, "sh": 14.0, "fg": 17.0, "sv": 17.1},
                    {"formacion": "Progreso Int 3", "profundidad": 9000, "pp_op": 9.9, "pcol": 11.4, "mw": 11.5, "ecd": 11.9, "sh": 14.3, "fg": 17.1, "sv": 17.3},
                    {"formacion": "Zapata 9 5/8", "profundidad": 9999, "pp_op": 10.2, "pcol": 11.6, "mw": 11.6, "ecd": 12.0, "sh": 14.4, "fg": 17.2, "sv": 17.4},
                    {"formacion": "Fm. Subibaja", "profundidad": 10677, "pp_op": 10.8, "pcol": 11.3, "mw": 12.0, "ecd": 12.2, "sh": 14.5, "fg": 18.0, "sv": 17.7}
                ]
                
                if modelo_seleccionado == "Eaton":
                    for row in base_data:
                        row["eaton_exp"] = 3.0
                        row["ppn"] = 8.6 if row["profundidad"] <= 1578 else (8.9 if row["profundidad"] <= 7006 else (9.2 if row["profundidad"] <= 8500 else (9.6 if row["profundidad"] <= 9000 else (9.8 if row["profundidad"] <= 9999 else 10.5))))
                elif modelo_seleccionado == "Bowers":
                    for row in base_data:
                        row["bowers_a"] = params['bowers_a']
                        row["bowers_b"] = params['bowers_b']

                op_df = st.data_editor(pd.DataFrame(base_data), num_rows="dynamic", use_container_width=True)
            
            zonas_params = []
            prev_depth = 0
            for index, row in op_df.iterrows():
                zona = {"start": prev_depth, "end": row["profundidad"]}
                if modelo_seleccionado == "Eaton":
                    zona["eaton_exp"] = row.get("eaton_exp", 3.0)
                    zona["ppn"] = row.get("ppn", 8.6)
                elif modelo_seleccionado == "Bowers":
                    zona["bowers_a"] = row.get("bowers_a", params.get('bowers_a'))
                    zona["bowers_b"] = row.get("bowers_b", params.get('bowers_b'))
                zonas_params.append(zona)
                prev_depth = row["profundidad"]
                
            params['params_zones'] = zonas_params

            st.sidebar.markdown("---")
            plot_height = st.sidebar.slider("🔍 Escala Vertical", min_value=800, max_value=4000, value=1200, step=100)

            with st.spinner("Computando Red Geomecánica..."):
                if modelo_seleccionado == "Eaton":
                    modelo = EatonModel(df, params)
                elif modelo_seleccionado == "Bowers":
                    modelo = BowersModel(df, params)
                else:
                    modelo = DivergenceModel(df, params)
                    
                resultados = modelo.run()
                
                fig = create_advanced_log_plot(resultados, zones=None, op_data=op_df, plot_height=plot_height, curve_type=params['curve_type'])
                st.plotly_chart(fig, width="stretch", theme=None)