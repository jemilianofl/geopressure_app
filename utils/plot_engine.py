import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_advanced_log_plot(df, zones=None, op_data=None, plot_height=1200, curve_type="Sonic"):
    fig = make_subplots(
        rows=1, cols=2, 
        shared_yaxes=True, 
        column_widths=[0.35, 0.65], 
        horizontal_spacing=0.015,
        subplot_titles=("Calibración Analítica", "Ventana Operativa (Curvas Reales)")
    )

    # --- TRACK 1: NCTL ---
    if curve_type == "Sonic":
        log_col = 'DT' if 'DT' in df.columns else 'DTC' if 'DTC' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#00CED1", width=1)), row=1, col=1)
        if 'DTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["DTN"], y=df["Depth"], mode="lines", name="NCTL", line=dict(color="#FF4500", width=2, dash="dash")), row=1, col=1)
        fig.update_xaxes(title_text="DT (us/ft)", autorange="reversed", row=1, col=1)
        
    elif curve_type == "Resistivity":
        log_col = 'RT' if 'RT' in df.columns else 'RES' if 'RES' in df.columns else None
        if log_col:
            fig.add_trace(go.Scatter(x=df[log_col], y=df["Depth"], mode="lines", name=log_col, line=dict(color="#00CED1", width=1)), row=1, col=1)
        if 'RTN' in df.columns:
            fig.add_trace(go.Scatter(x=df["RTN"], y=df["Depth"], mode="lines", name="NCTL", line=dict(color="#FF4500", width=2, dash="dash")), row=1, col=1)
        fig.update_xaxes(title_text="RT (ohm.m)", type="log", row=1, col=1)

    # --- TRACK 2: VENTANA OPERATIVA (CURVAS SUAVES) ---
    if 'Pp_Cal' in df.columns and 'Pf' in df.columns:
        fig.add_trace(go.Scatter(x=df["Pp_Cal"], y=df["Depth"], mode="lines", name="Presión Poro (Pp)", line=dict(color="#1E90FF", width=2)), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["Pf"], y=df["Depth"], mode="lines", name="Presión Fractura (Pf)", fill="tonextx", fillcolor="rgba(46, 139, 87, 0.2)", line=dict(color="#2E8B57", width=2)), row=1, col=2)
    
    if 'GSV' in df.columns:
        fig.add_trace(go.Scatter(x=df["GSV"], y=df["Depth"], mode="lines", name="Sobrecarga (Sv)", line=dict(color="#9370DB", width=2)), row=1, col=2)

    # DATOS OPERACIONALES (Modo Escalera Inmune a Errores)
    if op_data is not None and not op_data.empty:
        prof = op_data.get("profundidad")
        if prof is not None:
            if "pcol" in op_data.columns:
                fig.add_trace(go.Scatter(x=op_data["pcol"], y=prof, mode="lines", line_shape="vh", name="P. Colapso", line=dict(color="#FF00FF", width=2, dash="dash")), row=1, col=2)
            
            # Soporta ambos nombres para compatibilidad de caché
            col_pp = "pp_op" if "pp_op" in op_data.columns else "pp" if "pp" in op_data.columns else None
            if col_pp:
                fig.add_trace(go.Scatter(x=op_data[col_pp], y=prof, mode="lines", line_shape="vh", name="Pp Operacional", line=dict(color="#00BFFF", width=2)), row=1, col=2)
            
            if "sh" in op_data.columns:
                fig.add_trace(go.Scatter(x=op_data["sh"], y=prof, mode="lines", line_shape="vh", name="Sh", line=dict(color="#00FFFF", width=2, dash="dot")), row=1, col=2)
            if "fg" in op_data.columns:
                fig.add_trace(go.Scatter(x=op_data["fg"], y=prof, mode="lines+markers", line_shape="vh", name="LOT/FIT", marker=dict(symbol="diamond", size=8, color="#32CD32"), line=dict(color="#32CD32", width=2)), row=1, col=2)
            if "mw" in op_data.columns:
                fig.add_trace(go.Scatter(x=op_data["mw"], y=prof, mode="lines", line_shape="vh", name="MW", line=dict(color="#FFA500", width=3)), row=1, col=2)
            if "ecd" in op_data.columns:
                fig.add_trace(go.Scatter(x=op_data["ecd"], y=prof, mode="lines", line_shape="vh", name="ECD", line=dict(color="#FF4500", width=2, dash="dashdot")), row=1, col=2)

    fig.update_layout(
        template="plotly_dark",
        yaxis=dict(autorange="reversed", title="Profundidad (ft)", gridcolor="rgba(128,128,128,0.2)"),
        xaxis2=dict(title="Gradiente (ppg)", range=[7.5, 19.5], gridcolor="rgba(128,128,128,0.2)"),
        height=plot_height, 
        hovermode="y unified",
        # --- AQUÍ ESTÁ LA CORRECCIÓN DEL CURSOR ---
        hoverlabel=dict(
            bgcolor="rgba(20, 20, 20, 0.95)", # Fondo casi negro
            font_size=13,
            font_family="monospace",
            font_color="white",               # Letras blancas siempre
            bordercolor="#00CED1"             # Borde cian estilo Techlog
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig