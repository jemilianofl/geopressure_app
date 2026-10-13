import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_advanced_log_plot(df, zones=None, op_data=None):
    # Track 1: Curvas (ancho)
    fig = make_subplots(rows=1, cols=1, shared_yaxes=True)

    # Ventana Operativa Continua
    if 'GSV' in df.columns:
        fig.add_trace(go.Scatter(x=df["GSV"], y=df["Depth"], mode="lines", name="Sobrecarga (Sv)", line=dict(color="black", width=2)))
    if 'Pp_Cal' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Cal"], y=df["Depth"], mode="lines", name="Presión de Poro (Pp)", line=dict(color="blue", width=2)))
    if 'Pf' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pf"], y=df["Depth"], mode="lines", name="Gradiente Fractura (Fg)", line=dict(color="green", width=2)))

    # Líneas de Operación Escalonadas (MW, LOT, Colapso)
    # CORRECCIÓN: Evaluar correctamente el DataFrame de Pandas
    if op_data is not None and not op_data.empty:
        # Mud Weight
        fig.add_trace(go.Scatter(x=op_data["mw"], y=op_data["profundidad"], mode="lines", line_shape="vh", name="Mud Weight (MW)", line=dict(color="brown", width=3, dash="dot")))
        # LOT / FIT
        fig.add_trace(go.Scatter(x=op_data["lot_fit"], y=op_data["profundidad"], mode="markers+lines", line_shape="vh", name="LOT/FIT", marker=dict(symbol="triangle-right", size=8, color="red"), line=dict(color="red", width=2)))

    # Zonificación
    if zones:
        for zone in zones:
            fig.add_hrect(
                y0=zone['start'], y1=zone['end'],
                fillcolor=zone['color'], opacity=0.15,
                layer="below", line_width=0
            )

    fig.update_layout(
        xaxis_title="Gradiente de Presión (ppg)",
        yaxis_title="Profundidad (ft)",
        yaxis_autorange="reversed", 
        height=900, 
        template="plotly_white",
        xaxis=dict(range=[7, 20]), # Escala fija para evitar deformaciones
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig