import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_advanced_log_plot(df, zones=None, op_data=None, plot_height=900, curve_type="Sonic"):
    # Diseño de la industria: Track 1 (Calibración NCTL), Track 2 (Ventana Operativa)
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True, 
        column_widths=[0.3, 0.7], 
        horizontal_spacing=0.02,
        subplot_titles=("Track 1: Calibración NCTL", "Track 2: Ventana Operativa (ppg)")
    )

    # --- TRACK 1: REGISTRO CRUDO VS TENDENCIA NORMAL ---
    if curve_type == "Sonic":
        log_col = 'DT' if 'DT' in df.columns else 'DTC' if 'DTC' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#1f77b4", width=1)), row=1, col=1)
        if 'DTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["DTN"], y=df["Depth"], mode="lines", name="Tendencia (NCTL)", line=dict(color="#d62728", width=2, dash="dash")), row=1, col=1)
    elif curve_type == "Resistivity":
        log_col = 'RT' if 'RT' in df.columns else 'RES' if 'RES' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#1f77b4", width=1)), row=1, col=1)
        if 'RTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["RTN"], y=df["Depth"], mode="lines", name="Tendencia (NCTL)", line=dict(color="#d62728", width=2, dash="dash")), row=1, col=1)

    # --- TRACK 2: GRADIENTES DE PRESIÓN ---
    # 1. Sombrear la Ventana Operativa (Mud Window) entre Pp y Pf
    if 'Pp_Cal' in df.columns and 'Pf' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Cal"], y=df["Depth"], mode="lines", name="Presión de Poro (Pp)", line=dict(color="#17becf", width=2)), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["Pf"], y=df["Depth"], mode="lines", name="Presión Fractura (Pf)", fill="tonextx", fillcolor="rgba(44, 160, 44, 0.15)", line=dict(color="#2ca02c", width=2)), row=1, col=2)
    
    # 2. Sobrecarga (Sv)
    if 'GSV' in df.columns:
        fig.add_trace(go.Scatter(x=df["GSV"], y=df["Depth"], mode="lines", name="Sobrecarga (Sv)", line=dict(color="#9467bd", width=2)), row=1, col=2)

    # 3. Datos Operacionales Escalonados (MW y LOT)
    if op_data is not None and not op_data.empty:
        fig.add_trace(go.Scatter(x=op_data["mw"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Mud Weight (MW)", line=dict(color="#ff7f0e", width=3, dash="dot")), row=1, col=2)
        fig.add_trace(go.Scatter(x=op_data["lot_fit"], y=op_data["profundidad"], mode="markers+lines", line_shape="vh", name="LOT/FIT", marker=dict(symbol="triangle-right", size=8, color="#d62728"), line=dict(color="#d62728", width=1.5)), row=1, col=2)

    # Zonificación
    if zones:
        for zone in zones:
            fig.add_hrect(
                y0=zone['start'], y1=zone['end'],
                fillcolor=zone['color'], opacity=0.15,
                layer="below", line_width=0
            )

    # Configuraciones de diseño dinámico (Sin template estricto para soportar Modo Oscuro/Claro)
    fig.update_layout(
        yaxis=dict(autorange="reversed", title="Profundidad (ft)"),
        xaxis=dict(title="DT (us/ft)" if curve_type=="Sonic" else "RT (ohm.m)"),
        xaxis2=dict(title="Gradiente (ppg)", range=[7, 20]),
        height=plot_height, 
        hovermode="y unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Para resistividad, el track 1 suele ser logarítmico
    if curve_type == "Resistivity":
        fig.update_xaxes(type="log", row=1, col=1)
        
    return fig