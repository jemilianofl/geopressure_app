import io
import os
import tempfile
import pandas as pd
import numpy as np
import dlisio
import lasio_rs  

def load_well_data(uploaded_file, file_format="Auto"):
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
            content_start = uploaded_file.read(10).decode('utf-8', errors='ignore')
            uploaded_file.seek(0)
            if content_start.upper().startswith('~V'):
                file_format = "LAS"
            else:
                return None, "No se pudo determinar el formato. Selecciona LAS manualmente."

    try:
        uploaded_file.seek(0)
        df = None
        
        if file_format == "CSV":
            df = pd.read_csv(uploaded_file)
        elif file_format == "EXCEL":
            df = pd.read_excel(uploaded_file)
        elif file_format == "LAS":
            file_bytes = uploaded_file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".las", mode='wb') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
                
            try:
                las = lasio_rs.read(tmp_path)
                df = las.to_df()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        elif file_format == "DLIS":
            f, *tail = dlisio.load(uploaded_file)
            frame = f.frames[0] 
            curves = frame.curves()
            df = pd.DataFrame()
            for curve in curves:
                df[curve.name] = curve.astype(float)

        # LIMPIEZA RIGUROSA DE NULOS
        if df is not None:
            df = df.replace([-9999, -9999.0, -9999.25, -999.25, -999.0], np.nan)
            
        return df, None
            
    except Exception as e:
        return None, f"Error al leer el archivo: {str(e)}"