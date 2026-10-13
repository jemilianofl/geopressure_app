import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_advanced_log_plot(df, zones=None):
    # Crear subplots: 1. Litología (estrecho), 2. Curvas (ancho)
    fig = make_subplots(rows=1, cols=2, column_widths=[0.15, 0.85], shared_yaxes=True,
                        horizontal_spacing=0.02)

    # Track 1: Litología
    if 'Lithology_Color' in df.columns:
        fig.add_trace(go.Bar(
            y=df["Depth"],
            x=[1]*len(df),
            marker_color=df["Lithology_Color"],
            orientation='h',
            showlegend=False
        ), row=1, col=1)

    # Track 2: Curvas de Presión (Ventana Operativa)
    if 'GSV' in df.columns:
        fig.add_trace(go.Scatter(x=df["GSV"], y=df["Depth"], mode="lines", name="Sobrecarga (GSV)", line=dict(color="black")), row=1, col=2)
    if 'Pp_Cal' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Cal"], y=df["Depth"], mode="lines", name="Pp Calibrada", line=dict(color="blue")), row=1, col=2)
    elif 'Pp_Uncal' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Uncal"], y=df["Depth"], mode="lines", name="Pp Sin Calibrar", line=dict(dash="dash", color="blue")), row=1, col=2)
    if 'Pf' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pf"], y=df["Depth"], mode="lines", name="Presión Fractura (Pf)", line=dict(color="green")), row=1, col=2)
    if 'MW' in df.columns:
        fig.add_trace(go.Scatter(x=df["MW"], y=df["Depth"], mode="lines", name="Mud Weight (MW)", line=dict(color="brown")), row=1, col=2)

    # Zonificación
    if zones:
        for zone in zones:
            fig.add_hrect(
                y0=zone['start'], y1=zone['end'],
                fillcolor=zone['color'], opacity=0.2,
                layer="below", line_width=0,
                row=1, col=2
            )

    fig.update_layout(yaxis_autorange="reversed", height=800, template="plotly_white")
    return fig