import pandas as pd

def export_csv(df):
    """Exporta el DataFrame a CSV crudo."""
    return df.to_csv(index=False).encode('utf-8')

def export_las(df, depth_col="Depth"):
    """
    Exporta el DataFrame a un formato estándar LAS 2.0.
    Asegura que la profundidad sea la primera columna y formatea los nulos.
    """
    df_export = df.copy()
    
    # Asegurar que la columna de profundidad esté de primera
    cols = df_export.columns.tolist()
    if depth_col in cols:
        cols.remove(depth_col)
        cols = [depth_col] + cols
        df_export = df_export[cols]
        
    # Construir cabecera estándar LAS 2.0
    las_str = "~Version\n"
    las_str += "VERS. 2.0 : CWLS LOG ASCII STANDARD - VERSION 2.0\n"
    las_str += "WRAP. NO  : ONE LINE PER DEPTH STEP\n"
    las_str += "~Well Information\n"
    las_str += "#MNEM.UNIT  DATA  : DESCRIPTION\n"
    
    min_depth = df_export[depth_col].min(skipna=True)
    max_depth = df_export[depth_col].max(skipna=True)
    
    las_str += f"STRT.FT {min_depth} : First Depth\n"
    las_str += f"STOP.FT {max_depth} : Last Depth\n"
    las_str += f"STEP.FT 0.0 : Step\n"
    las_str += f"NULL. -9999.0 : Missing Value\n"
    las_str += f"WELL. PREDICT_IO_EXPORT : Well Name\n"
    
    # Declarar curvas
    las_str += "~Curve Information\n"
    las_str += "#MNEM.UNIT  : DESCRIPTION\n"
    for col in cols:
        las_str += f"{col}. : {col}\n"
        
    las_str += "~Ascii\n"
    
    # Formatear la matriz de datos separada por espacios
    data_str = df_export.to_csv(sep=' ', na_rep='-9999.0', header=False, index=False)
    las_str += data_str
    
    return las_str.encode('utf-8')