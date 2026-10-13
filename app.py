import pandas as pd
import streamlit as st
from utils.data_loader import load_well_data
from utils.plot_engine import create_advanced_log_plot
from models.eaton import EatonModel
from models.divergence import DivergenceModel

st.set_page_config(page_title="Geopressure Suite", layout="wide")
st.title("Análisis Multi-Modelo de Geopresiones")

# Sidebar - Carga de Datos
st.sidebar.header("1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo (LAS, DLIS, CSV, EXCEL)", type=None)
formato_manual = st.sidebar.selectbox("Forzar formato (si no tiene extensión)", ["Auto", "LAS", "DLIS", "CSV", "EXCEL"])

if uploaded_file is not None:
    with st.spinner("Leyendo archivo y limpiando datos..."):
        try:
            df, error_msg = load_well_data(uploaded_file, file_format=formato_manual)
            
            if error_msg:
                st.warning(error_msg)
            elif df is not None:
                st.success("Datos cargados correctamente.")
                
                # Buscar posibles curvas de profundidad
                curvas_profundidad = [c for c in df.columns if c.upper() in ['DEPTH', 'DEPT', 'TVD', 'MD']]
                if not curvas_profundidad: curvas_profundidad = df.columns.tolist()
                
                # Configuración del Modelo
                st.sidebar.header("2. Configuración del Modelo")
                
                col_profundidad = st.sidebar.selectbox("Curva de Profundidad (Eje Y)", curvas_profundidad)
                modelo_seleccionado = st.sidebar.selectbox("Seleccionar Modelo Predictivo", ["Eaton", "Divergencia (Athy/Trougott)"])
                
                params = {'depth_col': col_profundidad}
                
                # Tabla de zonificación de parámetros
                st.sidebar.subheader("Zonificación de Parámetros (Tops)")
                prof_min = float(df[col_profundidad].min(skipna=True))
                prof_max = float(df[col_profundidad].max(skipna=True))
                prof_media = float(df[col_profundidad].mean(skipna=True))
                
                zonas_params_base = pd.DataFrame([
                    {"start": prof_min, "end": prof_media, "eaton_exp": 3.0, "ppn": 1.03},
                    {"start": prof_media, "end": prof_max, "eaton_exp": 1.2, "ppn": 1.04}
                ])
                st.sidebar.write("Edita exponentes y Ppn por intervalo:")
                params_df = st.sidebar.data_editor(zonas_params_base, num_rows="dynamic", use_container_width=True)
                params['params_zones'] = params_df.to_dict('records')
                params['eaton_exp_default'] = 3.0
                params['ppn_default'] = 1.03
                
                with st.sidebar.expander("Parámetros Generales Adicionales", expanded=False):
                    params['rho_matrix'] = st.number_input("Densidad Matriz (g/cm3)", value=2.65)
                    
                    if modelo_seleccionado == "Eaton":
                        params['curve_type'] = st.selectbox("Curva Base", ["Sonic", "Resistivity"])
                        if params['curve_type'] == "Sonic":
                            curva_sonico = 'DT' if 'DT' in df.columns else 'DTC' if 'DTC' in df.columns else df.columns[1]
                            params['dtn_trend'] = df[curva_sonico].rolling(500, min_periods=1).mean()
                        else:
                            if 'RT' in df.columns:
                                params['rtn_trend'] = df['RT'].rolling(500, min_periods=1).mean()

                # Zonificación visual Litológica
                st.sidebar.header("3. Zonificación Litológica (Visual)")
                usar_zonas = st.sidebar.checkbox("Habilitar sombreado litológico")
                zonas_visuales = None
                
                if usar_zonas:
                    zonas_visuales_base = pd.DataFrame([
                        {"start": prof_min, "end": prof_media, "color": "yellow", "label": "Arena"},
                        {"start": prof_media, "end": prof_max, "color": "green", "label": "Arcilla"}
                    ])
                    zonas_vis_df = st.sidebar.data_editor(zonas_visuales_base, num_rows="dynamic", key="vis_zones")
                    zonas_visuales = zonas_vis_df.to_dict('records')

                # Ejecución
                if st.button("Generar Ventana Operativa", type="primary"):
                    with st.spinner("Calculando sobrecarga, poro y fractura..."):
                        if modelo_seleccionado == "Eaton":
                            modelo = EatonModel(df, params)
                        elif modelo_seleccionado == "Divergencia (Athy/Trougott)":
                            modelo = DivergenceModel(df, params)
                            
                        resultados = modelo.run()
                        
                        st.plotly_chart(create_advanced_log_plot(resultados, zones=zonas_visuales), use_container_width=True)
                        
                        with st.expander("Ver Datos Crudos"):
                            st.dataframe(resultados.dropna(subset=[col_profundidad, 'Pp_Cal', 'Pf'], how='all').head(100))

        except Exception as e:
            st.error(f"Error crítico procesando el archivo: {e}")