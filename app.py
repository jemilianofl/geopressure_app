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
    with st.spinner("Leyendo archivo..."):
        try:
            # Aquí desempaquetamos la tupla correctamente
            df, error_msg = load_well_data(uploaded_file, file_format=formato_manual)
            
            if error_msg:
                st.warning(error_msg)
            elif df is not None:
                st.success("Datos cargados correctamente.")
                
                # Sidebar - Selección de Modelo
                st.sidebar.header("2. Configuración del Modelo")
                modelo_seleccionado = st.sidebar.selectbox(
                    "Seleccionar Modelo Predictivo", 
                    ["Eaton", "Divergencia (Athy/Trougott)"]
                )
                
                # Identificar curvas disponibles
                curvas_disponibles = df.columns.tolist()
                
                params = {}
                with st.sidebar.expander("Parámetros del Modelo", expanded=True):
                    # Parámetros compartidos
                    params['rho_matrix'] = st.number_input("Densidad Matriz (g/cm3)", value=2.65)
                    
                    # Parámetros específicos por modelo
                    if modelo_seleccionado == "Eaton":
                        params['curve_type'] = st.selectbox("Curva Base", ["Sonic", "Resistivity"])
                        params['ppn'] = st.number_input("Ppn (Normal)", value=1.03, step=0.01)
                        if params['curve_type'] == "Sonic":
                            params['eaton_exp_sonic'] = st.number_input("Exponente Eaton (Sónico)", value=3.0, step=0.1)
                            # Simulación de NCTL
                            if 'DT' in df.columns or 'DTC' in df.columns:
                                curva_sonico = 'DT' if 'DT' in df.columns else 'DTC'
                                params['dtn_trend'] = df[curva_sonico].rolling(500, min_periods=1).mean()
                        else:
                            params['eaton_exp_res'] = st.number_input("Exponente Eaton (Resistividad)", value=1.2, step=0.1)
                            if 'RT' in df.columns:
                                params['rtn_trend'] = df['RT'].rolling(500, min_periods=1).mean()

                    elif modelo_seleccionado == "Divergencia (Athy/Trougott)":
                        params['rkb'] = st.number_input("RKB (Mesa Rotaria)", value=30.2, step=0.1)
                        params['ta'] = st.number_input("Tirante de Agua (TA)", value=3014.0, step=1.0)
                        params['dtco'] = st.number_input("DTCO (Tránsito inicial)", value=180.0, step=1.0)
                        params['c1'] = st.number_input("c1 (Factor exp)", value=-0.0004, step=0.0001, format="%.5f")
                        params['prf'] = st.number_input("Profundidad Ref (PRF)", value=3329.0, step=10.0)
                        params['ms'] = st.number_input("Prof. Calibración (MS)", value=1784.0, step=10.0)

                # Botón de ejecución
                if st.button("Generar Ventana Operativa", type="primary"):
                    with st.spinner("Calculando sobrecarga, poro y fractura..."):
                        if modelo_seleccionado == "Eaton":
                            modelo = EatonModel(df, params)
                        elif modelo_seleccionado == "Divergencia (Athy/Trougott)":
                            modelo = DivergenceModel(df, params)
                            
                        resultados = modelo.run()
                        
                        st.plotly_chart(create_advanced_log_plot(resultados, zones=None), use_container_width=True)
                        
                        with st.expander("Ver Datos Crudos"):
                            st.dataframe(resultados)

        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")