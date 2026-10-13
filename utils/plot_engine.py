import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_advanced_log_plot(df, zones=None, op_data=None, plot_height=1200, curve_type="Sonic"):
    # Configuración de los 2 Tracks profesionales
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True, 
        column_widths=[0.35, 0.65], 
        horizontal_spacing=0.015,
        subplot_titles=("Calibración (NCTL / Modelo)", "Ventana Operativa (Amistad-015S1)")
    )

    # --- TRACK 1: REGISTRO VS TENDENCIA ---
    if curve_type == "Sonic":
        log_col = 'DT' if 'DT' in df.columns else 'DTC' if 'DTC' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#00CED1", width=1)), row=1, col=1)
        if 'DTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["DTN"], y=df["Depth"], mode="lines", name="NCTL", line=dict(color="#FF4500", width=2, dash="dash")), row=1, col=1)
        
        # El sónico se grafica invertido
        fig.update_xaxes(title_text="DT (us/ft)", autorange="reversed", row=1, col=1)
        
    elif curve_type == "Resistivity":
        log_col = 'RT' if 'RT' in df.columns else 'RES' if 'RES' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#00CED1", width=1)), row=1, col=1)
        if 'RTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["RTN"], y=df["Depth"], mode="lines", name="NCTL", line=dict(color="#FF4500", width=2, dash="dash")), row=1, col=1)
        
        fig.update_xaxes(title_text="RT (ohm.m)", type="log", row=1, col=1)

    # --- TRACK 2: VENTANA OPERATIVA (DISEÑO TECHLOG) ---
    # CORRECCIÓN DE OPACITY AQUÍ
    if 'Pp_Cal' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Cal"], y=df["Depth"], mode="lines", name="Pp Calculada", line=dict(color="#1E90FF", width=1), opacity=0.4), row=1, col=2)

    # LÍMITES GEOMECÁNICOS Y OPERACIONALES (Modo Escalera "vh")
    if op_data is not None and not op_data.empty:
        if "pcol" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["pcol"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="P. Colapso (10% Breakout)", line=dict(color="#FF00FF", width=2, dash="dash")), row=1, col=2)
        if "pp" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["pp"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Pp (Kick Limit)", line=dict(color="#00BFFF", width=2)), row=1, col=2)
        if "sh" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["sh"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Sh (Límite Pérdidas)", line=dict(color="#00FFFF", width=2, dash="dot")), row=1, col=2)
        if "fg" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["fg"], y=op_data["profundidad"], mode="lines+markers", line_shape="vh", name="Fg / LOT", marker=dict(symbol="diamond", size=8, color="#32CD32"), line=dict(color="#32CD32", width=2)), row=1, col=2)
        if "sv" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["sv"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Sobrecarga (Sv)", line=dict(color="#F5F5F5", width=2)), row=1, col=2)
        if "mw" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["mw"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Mud Weight (MW)", line=dict(color="#FFA500", width=3)), row=1, col=2)
        if "ecd" in op_data.columns:
            fig.add_trace(go.Scatter(x=op_data["ecd"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="ECD (Máx Estimado)", line=dict(color="#FF4500", width=2, dash="dashdot")), row=1, col=2)

    # Diseño y Tema Oscuro Estricto
    fig.update_layout(
        template="plotly_dark",
        yaxis=dict(autorange="reversed", title="Profundidad (ft)", gridcolor="rgba(128,128,128,0.2)"),
        xaxis2=dict(title="Gradiente (ppg)", range=[7.5, 19.5], gridcolor="rgba(128,128,128,0.2)"),
        height=plot_height, 
        hovermode="y unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig