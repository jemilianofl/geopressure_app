import pandas as pd
import streamlit as st

from models.eaton import EatonModel
from utils.data_loader import load_well_data
from utils.plot_engine import create_advanced_log_plot

st.sidebar.header("Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo (LAS, DLIS, CSV, EXCEL o sin extensión)")

# Selector de formato para archivos sin extensión
formato_manual = st.sidebar.selectbox(
    "Formato del archivo (Usa 'Auto' si tiene extensión)", 
    ["Auto", "LAS", "DLIS", "CSV", "EXCEL"]
)

if uploaded_file is not None:
    df = load_well_data(uploaded_file, file_format=formato_manual)
    
    # Selector de curva a utilizar según las disponibles en el LAS
    curvas_disponibles = df.columns.tolist()
    curva_seleccionada = st.sidebar.selectbox("Curva base para Eaton", [c for c in curvas_disponibles if c in ['DT', 'RT', 'DTC', 'RES']])
    
    if st.button("Generar Ventana Operativa"):
        params = {
            'ppn': 1.03,
            'curve_type': 'Sonic' if curva_seleccionada in ['DT', 'DTC'] else 'Resistivity',
            # Simulación de NCTL (En producción requiere un ajuste exponencial/lineal del usuario)
            'dtn_trend': df[curva_seleccionada].rolling(500, min_periods=1).mean() 
        }
        
        modelo = EatonModel(df, params)
        resultados = modelo.run()
        
        # Enviar resultados al plot_engine.py para dibujar 'GSV', 'Pp_Cal', 'Pf', 'MW'
        st.plotly_chart(create_advanced_log_plot(resultados, zones=None), use_container_width=True)