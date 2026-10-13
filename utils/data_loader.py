import io
import pandas as pd
import dlisio
import lasio_rs  

def load_well_data(uploaded_file, file_format="Auto"):
    """
    Carga datos de pozo desde distintos formatos.
    Incluye detección inteligente de contenido para archivos sin extensión.
    """
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
            # MAGIA AQUÍ: Leer los primeros 10 bytes para ver si es un archivo LAS oculto
            content_start = uploaded_file.read(10).decode('utf-8', errors='ignore')
            uploaded_file.seek(0) # Muy importante: regresar el "cursor" de lectura al inicio
            
            if content_start.upper().startswith('~V'):
                file_format = "LAS"
            else:
                return None, "No se pudo determinar el formato automáticamente. Por favor, selecciona el formato manual en la barra lateral (ej. LAS)."

    try:
        if file_format == "CSV":
            return pd.read_csv(uploaded_file), None
        
        elif file_format == "EXCEL":
            return pd.read_excel(uploaded_file), None
        
        elif file_format == "LAS":
            content = uploaded_file.read().decode('utf-8')
            
            try:
                las = lasio_rs.read(content) 
            except TypeError:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".las", mode='w') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                las = lasio_rs.read(tmp_path)
                os.remove(tmp_path)
                
            return las.to_df(), None
            
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