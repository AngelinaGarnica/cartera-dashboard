"""
Módulo de visualizaciones con Plotly.
Paleta oscura profesional, estilo fintech.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ─── Paleta y tema ──────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#0D1117",
    "card": "#161B22",
    "border": "#21262D",
    "text": "#E6EDF3",
    "text_muted": "#7D8590",
    "accent": "#58A6FF",
    "accent2": "#3FB950",
    "warning": "#D29922",
    "danger": "#F85149",
    "purple": "#BC8CFF",
    "teal": "#39D353",
}

BUCKET_COLORS = {
    "Al día":        "#3FB950",
    "1-30 días":     "#D29922",
    "31-60 días":    "#F0883E",
    "61-90 días":    "#F85149",
    "91-180 días":   "#CF222E",
    "+180 días":     "#8B0000",
}

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'IBM Plex Mono', monospace", color=COLORS["text"], size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=COLORS["border"],
        font=dict(color=COLORS["text_muted"], size=11)
    ),
)

AXIS_STYLE = dict(
    gridcolor=COLORS["border"],
    linecolor=COLORS["border"],
    tickcolor=COLORS["border"],
    tickfont=dict(color=COLORS["text_muted"], size=11),
    title_font=dict(color=COLORS["text_muted"], size=12),
    zeroline=False,
)


def _apply_base(fig) -> go.Figure:
    fig.update_layout(**LAYOUT_BASE)
    return fig


# ─── Aging / Buckets ────────────────────────────────────────────────────────────

def fig_aging_barras(df_aging: pd.DataFrame) -> go.Figure:
    colors = [BUCKET_COLORS.get(b, COLORS["accent"]) for b in df_aging["bucket_mora"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_aging["bucket_mora"].astype(str),
        y=df_aging["saldo"],
        name="Saldo en mora",
        marker_color=colors,
        text=[f"${v/1e6:.1f}M" for v in df_aging["saldo"]],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Saldo: $%{y:,.0f}<br>"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Distribución de Saldo por Aging", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(**AXIS_STYLE, title="Bucket de Mora"),
        yaxis=dict(**AXIS_STYLE, title="Saldo Total ($)", tickformat="$,.0f"),
        bargap=0.3,
    )
    return fig


def fig_aging_donut(df_aging: pd.DataFrame) -> go.Figure:
    labels = df_aging["bucket_mora"].astype(str).tolist()
    colors = [BUCKET_COLORS.get(b, COLORS["accent"]) for b in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=df_aging["cantidad"],
        hole=0.65,
        marker=dict(colors=colors, line=dict(color=COLORS["bg"], width=3)),
        textinfo="percent",
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Composición de Cartera", font=dict(size=14, color=COLORS["text"])),
        annotations=[dict(
            text=f"<b>{df_aging['cantidad'].sum()}</b><br>créditos",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=COLORS["text"], size=16),
        )],
    )
    return fig


# ─── Score de Riesgo ────────────────────────────────────────────────────────────

def fig_score_histograma(df_score: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df_score["score_bin"].astype(str),
        y=df_score["cantidad"],
        marker=dict(
            color=df_score["cantidad"],
            colorscale=[[0, COLORS["danger"]], [0.5, COLORS["warning"]], [1, COLORS["accent2"]]],
            showscale=False,
        ),
        hovertemplate="<b>Score %{x}</b><br>Cantidad: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Distribución de Score de Riesgo", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(**AXIS_STYLE, title="Rango de Score", tickangle=-45),
        yaxis=dict(**AXIS_STYLE, title="Cantidad de Créditos"),
        bargap=0.15,
    )
    return fig


def fig_score_vs_mora(df: pd.DataFrame) -> go.Figure:
    sample = df.sample(min(300, len(df)), random_state=42)
    color_map = {
        "Vigente": COLORS["accent2"],
        "En mora": COLORS["warning"],
        "En gestión judicial": "#8B0000",
    }
    fig = go.Figure()
    for estado, color in color_map.items():
        sub = sample[sample["estado_credito"] == estado]
        fig.add_trace(go.Scatter(
            x=sub["score_riesgo"],
            y=sub["dias_mora"],
            mode="markers",
            name=estado,
            marker=dict(color=color, size=5, opacity=0.7, line=dict(width=0)),
            hovertemplate=(
                f"<b>{estado}</b><br>"
                "Score: %{x}<br>"
                "Días mora: %{y}<br>"
                "<extra></extra>"
            ),
        ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Score vs Días de Mora", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(**AXIS_STYLE, title="Score de Riesgo"),
        yaxis=dict(**AXIS_STYLE, title="Días en Mora"),
    )
    return fig


# ─── Zona geográfica ────────────────────────────────────────────────────────────

def fig_zona_horizontal(df_zona: pd.DataFrame) -> go.Figure:
    df_s = df_zona.sort_values("saldo")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_s["zona"],
        x=df_s["saldo"],
        orientation="h",
        name="Saldo Total",
        marker_color=COLORS["accent"],
        opacity=0.85,
        hovertemplate="<b>%{y}</b><br>Saldo: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df_s["zona"],
        x=df_s["cobrado"],
        orientation="h",
        name="Cobrado mes",
        marker_color=COLORS["accent2"],
        opacity=0.85,
        hovertemplate="<b>%{y}</b><br>Cobrado: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Saldo y Cobranza por Zona", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(**AXIS_STYLE, title="Monto ($)", tickformat="$,.0f"),
        yaxis=dict(**AXIS_STYLE, title=""),
        barmode="group",
        bargap=0.25,
    )
    return fig


# ─── Gestores ───────────────────────────────────────────────────────────────────

def fig_gestores_radar(df_gestores: pd.DataFrame) -> go.Figure:
    categorias = ["Efectividad", "Score Prom.", "Saldo Gestionado", "Créditos", "Cobranza"]
    fig = go.Figure()

    max_vals = {
        "efectividad": df_gestores["efectividad"].max() or 1,
        "score_prom": df_gestores["score_prom"].max() or 1,
        "saldo_gestionado": df_gestores["saldo_gestionado"].max() or 1,
        "cantidad": df_gestores["cantidad"].max() or 1,
        "cobrado": df_gestores["cobrado"].max() or 1,
    }

    radar_colors = [COLORS["accent"], COLORS["accent2"], COLORS["warning"], COLORS["purple"]]

    for i, row in df_gestores.iterrows():
        vals = [
            row["efectividad"] / max_vals["efectividad"],
            row["score_prom"] / max_vals["score_prom"],
            row["saldo_gestionado"] / max_vals["saldo_gestionado"],
            row["cantidad"] / max_vals["cantidad"],
            row["cobrado"] / max_vals["cobrado"],
        ]
        vals_closed = vals + [vals[0]]
        cats_closed = categorias + [categorias[0]]
        color = radar_colors[i % len(radar_colors)]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=cats_closed,
            fill="none",
            name=row["gestor"],
            line=dict(color=color, width=2.5),
            marker=dict(color=color, size=6),
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Performance por Gestor", font=dict(size=14, color=COLORS["text"])),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(tickcolor=COLORS["border"], gridcolor=COLORS["border"],
                             tickfont=dict(color=COLORS["text_muted"], size=11)),
            radialaxis=dict(tickcolor=COLORS["border"], gridcolor=COLORS["border"],
                            tickfont=dict(color=COLORS["text_muted"], size=10),
                            range=[0, 1]),
        ),
    )
    return fig


# ─── Waterfall recupero ─────────────────────────────────────────────────────────

def fig_waterfall_recupero(kpis: dict) -> go.Figure:
    saldo = kpis["saldo_total_cartera"]
    al_dia = saldo - kpis["saldo_en_mora"]
    en_mora = kpis["saldo_en_mora"]
    cobrado = kpis["total_cobrado_mes"]
    incobrable = kpis["saldo_incobrable"]

    fig = go.Figure(go.Waterfall(
        name="Flujo de cartera",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Cartera Total", "Al Día", "Cobrado Mes", "Exposición Neta"],
        y=[saldo, -al_dia, -cobrado, 0],
        connector=dict(line=dict(color=COLORS["border"], width=1)),
        increasing=dict(marker=dict(color=COLORS["accent2"])),
        decreasing=dict(marker=dict(color=COLORS["danger"])),
        totals=dict(marker=dict(color=COLORS["accent"])),
        text=[f"${v/1e6:.1f}M" for v in [saldo, al_dia, cobrado, en_mora - cobrado]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Flujo de Exposición de Cartera", font=dict(size=14, color=COLORS["text"])),
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, tickformat="$,.0f"),
    )
    return fig
