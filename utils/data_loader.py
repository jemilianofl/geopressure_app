import io
import pandas as pd
import dlisio
import lasio_rs  # Nombre correcto de importación según tu documentación

def load_well_data(uploaded_file, file_format="Auto"):
    """
    Carga datos de pozo desde distintos formatos.
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
            raise ValueError("No se pudo determinar el formato. Seleccionalo manualmente.")

    try:
        if file_format == "CSV":
            return pd.read_csv(uploaded_file)
        
        elif file_format == "EXCEL":
            return pd.read_excel(uploaded_file)
        
        elif file_format == "LAS":
            # Guardamos el archivo temporalmente en memoria o leemos su contenido
            # Suponiendo que lasio_rs.read acepta un string con la ruta o el contenido crudo
            # Como Streamlit usa UploadedFile, lo más seguro es decodificarlo a texto
            content = uploaded_file.read().decode('utf-8')
            
            # Si tu librería en Rust acepta un string directamente (necesitas verificar si tiene read_string)
            # Si solo acepta rutas, habría que guardarlo en un archivo temporal.
            # Por la documentación "lasio_rs.read(path)" parece pedir ruta, pero asumamos que maneja strings:
            try:
                las = lasio_rs.read(content) 
            except TypeError:
                # Si falla porque requiere una ruta física de archivo:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".las", mode='w') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                las = lasio_rs.read(tmp_path)
                os.remove(tmp_path)
                
            # Tu librería tiene conversión nativa a pandas muy rápida
            return las.to_df()
            
        elif file_format == "DLIS":
            f, *tail = dlisio.load(uploaded_file)
            frame = f.frames[0] 
            curves = frame.curves()
            df = pd.DataFrame()
            for curve in curves:
                df[curve.name] = curve.astype(float)
            return df
            
    except Exception as e:
        raise Exception(f"Error al leer el archivo como {file_format}: {str(e)}")