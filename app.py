import pandas as pd
import streamlit as st
from utils.data_loader import load_well_data
from utils.plot_engine import create_advanced_log_plot
from models.eaton import EatonModel

st.set_page_config(page_title="Geopressure Suite - Amistad", layout="wide")
st.title("Ventana Operativa de Perforación (Sistema Inglés)")

# 1. CARGA DE DATOS
st.sidebar.header("1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Archivo Pozo (LAS, CSV)", type=None)
formato_manual = st.sidebar.selectbox("Formato", ["Auto", "LAS", "CSV", "EXCEL"])

if uploaded_file is not None:
    with st.spinner("Procesando..."):
        df, error_msg = load_well_data(uploaded_file, file_format=formato_manual)
        
        if error_msg:
            st.warning(error_msg)
        elif df is not None:
            
            curvas_profundidad = [c for c in df.columns if c.upper() in ['DEPTH', 'DEPT', 'TVD', 'MD']]
            if not curvas_profundidad: curvas_profundidad = df.columns.tolist()
            
            # --- NUEVO: Control de aspecto del gráfico ---
            st.sidebar.header("Opciones de Visualización")
            plot_height = st.sidebar.slider("Altura del gráfico (zoom vertical)", min_value=600, max_value=3000, value=900, step=100)
            
            # 2. CONFIGURACIÓN GEOMECÁNICA
            st.sidebar.header("2. Modelo Eaton (NCTL)")
            col_prof = st.sidebar.selectbox("Eje de Profundidad (ft)", curvas_profundidad)
            
            params = {'depth_col': col_prof, 'curve_type': 'Sonic'}
            
            params['rkb'] = st.sidebar.number_input("Elevación Mesa Rotaria (ft)", value=101.0)
            params['wd'] = st.sidebar.number_input("Tirante de Agua (ft)", value=138.0)
            
            with st.sidebar.expander("Calibración de Tendencia (NCTL)", expanded=True):
                st.info("Ajusta estos valores para que la línea punteada del Track 1 coincida con las lutitas limpias.")
                params['dt_ml'] = st.number_input("Tránsito en Lecho Marino (DT_ml)", value=160.0, step=1.0)
                params['c_compaction'] = st.number_input("Factor Compactación (c)", value=0.00010, format="%.5f", step=0.00001)

            # 3. ZONAS OPERATIVAS AMISTAD-015S1
            st.sidebar.header("3. Diseño de Revestidores y MW")
            
            op_data_base = pd.DataFrame([
                {"profundidad": 400, "mw": 9.2, "lot_fit": 12.0, "eaton_exp": 3.0, "ppn": 8.6},
                {"profundidad": 1578, "mw": 9.4, "lot_fit": 12.68, "eaton_exp": 3.0, "ppn": 8.6},
                {"profundidad": 7006, "mw": 10.8, "lot_fit": 14.76, "eaton_exp": 3.0, "ppn": 8.9},
                {"profundidad": 8000, "mw": 11.2, "lot_fit": 16.8, "eaton_exp": 3.0, "ppn": 9.2},
                {"profundidad": 9000, "mw": 11.5, "lot_fit": 17.1, "eaton_exp": 3.0, "ppn": 9.6},
                {"profundidad": 9999, "mw": 11.6, "lot_fit": 17.2, "eaton_exp": 3.0, "ppn": 9.8},
                {"profundidad": 10677, "mw": 12.0, "lot_fit": 18.0, "eaton_exp": 3.0, "ppn": 10.5}
            ])
            
            st.sidebar.write("Ajusta densidades (ppg) y profundidades (ft):")
            op_df = st.sidebar.data_editor(op_data_base, num_rows="dynamic", use_container_width=True)
            
            zonas_params = []
            prev_depth = 0
            for index, row in op_df.iterrows():
                zonas_params.append({
                    "start": prev_depth, 
                    "end": row["profundidad"], 
                    "eaton_exp": row["eaton_exp"], 
                    "ppn": row["ppn"]
                })
                prev_depth = row["profundidad"]
            params['params_zones'] = zonas_params

            # Ejecución Automática
            with st.spinner("Calculando en PPG..."):
                modelo = EatonModel(df, params)
                resultados = modelo.run()
                
                # --- NUEVO: Gráfico dinámico adaptado al tema ---
                fig = create_advanced_log_plot(resultados, zones=None, op_data=op_df, plot_height=plot_height, curve_type=params['curve_type'])
                st.plotly_chart(fig, width="stretch", theme="streamlit")
                
                with st.expander("Tabla de Resultados (ppg / ft)"):
                    st.dataframe(resultados[[col_prof, 'GSV', 'Pp_Uncal', 'Pf']].dropna().head(100))