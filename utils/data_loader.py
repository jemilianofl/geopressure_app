import io
import os
import tempfile
import pandas as pd
import dlisio
import lasio_rs  

def load_well_data(uploaded_file, file_format="Auto"):
    """
    Carga datos de pozo desde distintos formatos.
    Incluye detección inteligente de contenido para archivos sin extensión.
    """
    # 1. Detección automática de formato
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
            # Detección inteligente para archivos sin extensión
            content_start = uploaded_file.read(10).decode('utf-8', errors='ignore')
            uploaded_file.seek(0) # Regresamos el cursor al inicio
            
            if content_start.upper().startswith('~V'):
                file_format = "LAS"
            else:
                return None, "No se pudo determinar el formato automáticamente. Por favor, selecciona el formato manual en la barra lateral."

    # 2. Procesamiento según el formato detectado
    try:
        uploaded_file.seek(0) # Aseguramos siempre empezar desde el inicio
        
        if file_format == "CSV":
            return pd.read_csv(uploaded_file), None
        
        elif file_format == "EXCEL":
            return pd.read_excel(uploaded_file), None
        
        elif file_format == "LAS":
            # Guardamos los bytes en un archivo temporal real en disco
            file_bytes = uploaded_file.read()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".las", mode='wb') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
                
            try:
                # Le pasamos la RUTA al lector de Rust, no el contenido
                las = lasio_rs.read(tmp_path)
                df = las.to_df()
            finally:
                # Limpiamos el disco duro sin importar si falla o tiene éxito
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
            return df, None
            
        elif file_format == "DLIS":
            f, *tail = dlisio.load(uploaded_file)
            frame = f.frames[0] 
            curves = frame.curves()
            df = pd.DataFrame()
            for curve in curves:
                df[curve.name] = curve.astype(float)
            return df, None
            
    except Exception as e:
        return None, f"Error al leer el archivo como {file_format}: {str(e)}"