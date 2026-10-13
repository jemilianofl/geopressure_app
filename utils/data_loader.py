import pandas as pd
import dlisio
import las_read_rs  # Tu librería en Rust
import io

def load_well_data(uploaded_file, file_format="Auto"):
    """
    Carga datos de pozo desde distintos formatos.
    uploaded_file: el archivo subido desde Streamlit
    file_format: formato forzado por el usuario (útil para archivos sin extensión)
    """
    # Detectar formato si está en Auto
    if file_format == "Auto":
        filename = uploaded_file.name.lower()
        if filename.endswith('.csv'):
            file_format = "CSV"
        elif filename.endswith(('.xls', '.xlsx')):
            file_format = "EXCEL"
        elif filename.endswith('.las'):
            file_format = "LAS"
        elif filename.endswith('.dlis'):
            file_format = "DLIS"
        else:
            raise ValueError("No se pudo determinar el formato. Seleccionalo manualmente.")

    # Procesamiento según formato
    try:
        if file_format == "CSV":
            return pd.read_csv(uploaded_file)
        
        elif file_format == "EXCEL":
            return pd.read_excel(uploaded_file)
        
        elif file_format == "LAS":
            # Usando tu librería las-read-rs
            # Suponiendo que lee bytes o texto crudo
            content = uploaded_file.read().decode('utf-8')
            # Ajusta esta llamada según los métodos reales de tu librería
            las_data = las_read_rs.read_string(content) 
            return pd.DataFrame(las_data.curves)
            
        elif file_format == "DLIS":
            # Lectura básica de DLIS con dlisio
            f, *tail = dlisio.load(uploaded_file)
            frame = f.frames[0] # Tomar el primer frame
            curves = frame.curves()
            df = pd.DataFrame()
            for curve in curves:
                df[curve.name] = curve.astype(float)
            return df
            
    except Exception as e:
        raise Exception(f"Error al leer el archivo como {file_format}: {str(e)}")