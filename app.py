"""
Dashboard de Seguimiento de Cartera de Deuda
Créditos Personales / Consumo
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# ─── Setup de rutas ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from data_loader import (
    cargar_cartera, calcular_kpis, resumen_aging,
    resumen_por_zona, resumen_por_gestor, distribucion_score, top_deudores
)
from charts import (
    fig_aging_barras, fig_aging_donut, fig_score_histograma,
    fig_score_vs_mora, fig_zona_horizontal, fig_gestores_radar,
    fig_waterfall_recupero, COLORS
)

# ─── Configuración de página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cartera Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personalizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0D1117;
    color: #E6EDF3;
}

.stApp { background-color: #0D1117; }

/* Header */
.dash-header {
    background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.dash-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #E6EDF3;
    margin: 0;
    letter-spacing: -0.02em;
}

.dash-subtitle {
    color: #7D8590;
    font-size: 0.85rem;
    margin: 4px 0 0 0;
    font-family: 'IBM Plex Mono', monospace;
}

.dash-badge {
    background: #1F6FEB22;
    border: 1px solid #1F6FEB55;
    color: #58A6FF;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    margin-left: auto;
}

/* KPI Cards */
.kpi-card {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.kpi-card:hover { border-color: #30363D; }

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}

.kpi-card.blue::before { background: linear-gradient(90deg, #1F6FEB, #58A6FF); }
.kpi-card.green::before { background: linear-gradient(90deg, #238636, #3FB950); }
.kpi-card.orange::before { background: linear-gradient(90deg, #9E6A03, #D29922); }
.kpi-card.red::before { background: linear-gradient(90deg, #DA3633, #F85149); }
.kpi-card.purple::before { background: linear-gradient(90deg, #6E40C9, #BC8CFF); }
.kpi-card.teal::before { background: linear-gradient(90deg, #1B7C83, #39D353); }

.kpi-label {
    font-size: 0.72rem;
    color: #7D8590;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 10px;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
    color: #E6EDF3;
    line-height: 1;
    margin-bottom: 6px;
}

.kpi-sub {
    font-size: 0.78rem;
    color: #7D8590;
    font-family: 'IBM Plex Mono', monospace;
}

.kpi-icon {
    position: absolute;
    top: 16px; right: 16px;
    font-size: 1.4rem;
    opacity: 0.4;
}

/* Section headers */
.section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #7D8590;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262D;
}

/* Alerts */
.alert-bar {
    background: #F851490D;
    border: 1px solid #F8514933;
    border-left: 3px solid #F85149;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.85rem;
    color: #E6EDF3;
    font-family: 'IBM Plex Mono', monospace;
}

.alert-warning {
    background: #D299220D;
    border: 1px solid #D2992233;
    border-left: 3px solid #D29922;
}

/* Table */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    font-family: 'IBM Plex Mono', monospace;
}

.styled-table th {
    background: #161B22;
    color: #7D8590;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid #21262D;
}

.styled-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #161B22;
    color: #E6EDF3;
}

.styled-table tr:hover td { background: #161B2288; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161B22;
    border-right: 1px solid #21262D;
}

/* Selectbox / multiselect */
.stSelectbox > div, .stMultiSelect > div {
    background-color: #21262D !important;
    border-color: #30363D !important;
}

/* Plotly charts */
.js-plotly-plot { border-radius: 10px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161B22;
    border-radius: 8px;
    padding: 6px;
    gap: 6px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #7D8590;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    border-radius: 6px;
    padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #21262D !important;
    color: #E6EDF3 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px !important;
}

/* Metric override */
[data-testid="stMetric"] { display: none; }

div[data-testid="stHorizontalBlock"] { gap: 16px; }
</style>
""", unsafe_allow_html=True)


# ─── Carga de datos ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    df = cargar_cartera()
    return df

df_raw = load_data()


# ─── Sidebar / Filtros ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#7D8590;
                text-transform:uppercase; letter-spacing:0.1em; margin-bottom:16px;">
        ⚙ Filtros de Cartera
    </div>
    """, unsafe_allow_html=True)

    zonas_opts = ["Todas"] + sorted(df_raw["zona"].unique().tolist())
    zona_sel = st.selectbox("Zona geográfica", zonas_opts)

    gestores_opts = ["Todos"] + sorted(df_raw["gestor"].unique().tolist())
    gestor_sel = st.selectbox("Gestor", gestores_opts)

    estados_opts = df_raw["estado_credito"].cat.categories.tolist()
    estados_sel = st.multiselect("Estado", estados_opts, default=estados_opts)

    score_range = st.slider("Score de riesgo", 300, 950, (300, 950), step=25)

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#7D8590;">
        📁 Fuente de datos<br>
        <span style="color:#3FB950;">● CSV (modo MVP)</span><br><br>
        <span style="color:#7D8590;">Próximamente: API REST</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─── Aplicar filtros ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if zona_sel != "Todas":
    df = df[df["zona"] == zona_sel]
if gestor_sel != "Todos":
    df = df[df["gestor"] == gestor_sel]
if estados_sel:
    df = df[df["estado_credito"].isin(estados_sel)]
df = df[(df["score_riesgo"] >= score_range[0]) & (df["score_riesgo"] <= score_range[1])]


# ─── Header ─────────────────────────────────────────────────────────────────────
kpis = calcular_kpis(df)

st.markdown(f"""
<div class="dash-header">
    <div>
        <p class="dash-title">📊 CARTERA / CONSUMO</p>
        <p class="dash-subtitle">Dashboard de Seguimiento · Actualizado hoy · {len(df):,} créditos en vista</p>
    </div>
    <div class="dash-badge">MVP v1.0</div>
</div>
""", unsafe_allow_html=True)


# ─── Alertas dinámicas ───────────────────────────────────────────────────────────
alertas = []
if kpis["ratio_mora_saldo"] > 0.35:
    alertas.append(("red", f"⚠ Ratio de mora sobre saldo: {kpis['ratio_mora_saldo']:.1%} — supera umbral crítico (35%)"))
if kpis["tasa_recupero"] < 0.10:
    alertas.append(("orange", f"⚡ Tasa de recupero baja: {kpis['tasa_recupero']:.1%} — revisar gestión de cobranza"))
if kpis["pct_alto_riesgo"] > 0.20:
    alertas.append(("orange", f"🔴 {kpis['pct_alto_riesgo']:.1%} de la cartera con score < 500 (alto riesgo)"))

if alertas:
    with st.expander(f"⚠ {len(alertas)} alerta(s) activa(s)", expanded=True):
        for tipo, msg in alertas:
            cls = "alert-bar" if tipo == "red" else "alert-bar alert-warning"
            st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)


# ─── KPIs principales ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">KPIs Principales</div>', unsafe_allow_html=True)

cols = st.columns(6)

kpi_data = [
    ("blue", "💼", "SALDO TOTAL", f"${kpis['saldo_total_cartera']/1e6:.1f}M",
     f"Capital: ${kpis['capital_total']/1e6:.1f}M"),
    ("red", "⚠", "MORA (SALDO)", f"{kpis['ratio_mora_saldo']:.1%}",
     f"${kpis['saldo_en_mora']/1e6:.1f}M en mora"),
    ("orange", "📅", "MORA (CANTIDAD)", f"{kpis['tasa_mora_cantidad']:.1%}",
     f"{int(kpis['tasa_mora_cantidad']*len(df)):,} créditos"),
    ("green", "💰", "RECUPERO MES", f"{kpis['tasa_recupero']:.1%}",
     f"${kpis['total_cobrado_mes']/1e3:.0f}K cobrados"),
    ("purple", "🎯", "SCORE PROM.", f"{kpis['score_promedio']:.0f}",
     f"{kpis['pct_alto_riesgo']:.1%} alto riesgo"),
    ("teal", "🏦", "TOTAL CRÉDITOS", f"{kpis['total_creditos']:,}",
     f"Provisión est.: ${kpis['provision_estimada']/1e6:.1f}M"),
]

for col, (color, icon, label, value, sub) in zip(cols, kpi_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── Tabs principales ────────────────────────────────────────────────────────────
st.markdown("")
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Mora & Aging", "🎯 Score de Riesgo", "🗺 Zonas", "👥 Gestores", "📋 Deudores"
])


# ── TAB 1: Mora & Aging ──────────────────────────────────────────────────────────
with tab1:
    df_aging = resumen_aging(df)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(fig_aging_barras(df_aging), use_container_width=True)
    with c2:
        st.plotly_chart(fig_aging_donut(df_aging), use_container_width=True)

    st.plotly_chart(fig_waterfall_recupero(kpis), use_container_width=True)

    # Tabla de aging detallada
    st.markdown('<div class="section-title">Detalle por Bucket</div>', unsafe_allow_html=True)
    df_aging_show = df_aging.copy()
    df_aging_show["bucket_mora"] = df_aging_show["bucket_mora"].astype(str)
    df_aging_show["saldo"] = df_aging_show["saldo"].apply(lambda x: f"${x:,.0f}")
    df_aging_show["pct_cantidad"] = df_aging_show["pct_cantidad"].apply(lambda x: f"{x:.1%}")
    df_aging_show["pct_saldo"] = df_aging_show["pct_saldo"].apply(lambda x: f"{x:.1%}")
    df_aging_show["score_prom"] = df_aging_show["score_prom"].apply(lambda x: f"{x:.0f}")
    df_aging_show["recupero_prom"] = df_aging_show["recupero_prom"].apply(lambda x: f"{x:.1%}")
    df_aging_show.columns = ["Bucket", "Cant.", "Saldo", "Score Prom.", "Recupero", "% Cant.", "% Saldo"]
    st.dataframe(
        df_aging_show,
        use_container_width=True,
        hide_index=True,
    )


# ── TAB 2: Score de Riesgo ───────────────────────────────────────────────────────
with tab2:
    df_score = distribucion_score(df)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_score_histograma(df_score), use_container_width=True)
    with c2:
        st.plotly_chart(fig_score_vs_mora(df), use_container_width=True)

    # KPIs por categoría de riesgo
    st.markdown('<div class="section-title">KPIs por Categoría de Riesgo</div>', unsafe_allow_html=True)
    df_cat = df.groupby("categoria_score", observed=True).agg(
        cantidad=("id_credito", "count"),
        saldo=("saldo_total", "sum"),
        mora_prom=("dias_mora", "mean"),
        recupero=("tasa_recupero", "mean"),
    ).reset_index()
    df_cat["saldo"] = df_cat["saldo"].apply(lambda x: f"${x:,.0f}")
    df_cat["mora_prom"] = df_cat["mora_prom"].apply(lambda x: f"{x:.1f} días")
    df_cat["recupero"] = df_cat["recupero"].apply(lambda x: f"{x:.1%}")
    df_cat.columns = ["Categoría", "Créditos", "Saldo", "Mora Promedio", "Recupero"]
    st.dataframe(df_cat, use_container_width=True, hide_index=True)


# ── TAB 3: Zonas ─────────────────────────────────────────────────────────────────
with tab3:
    df_zona = resumen_por_zona(df)
    st.plotly_chart(fig_zona_horizontal(df_zona), use_container_width=True)

    st.markdown('<div class="section-title">Detalle por Zona</div>', unsafe_allow_html=True)
    df_zona_show = df_zona.copy()
    df_zona_show["saldo"] = df_zona_show["saldo"].apply(lambda x: f"${x:,.0f}")
    df_zona_show["cobrado"] = df_zona_show["cobrado"].apply(lambda x: f"${x:,.0f}")
    df_zona_show["mora_prom_dias"] = df_zona_show["mora_prom_dias"].apply(lambda x: f"{x:.1f}")
    df_zona_show["score_prom"] = df_zona_show["score_prom"].apply(lambda x: f"{x:.0f}")
    df_zona_show.columns = ["Zona", "Créditos", "Saldo Total", "Mora Prom. (días)", "Score Prom.", "Cobrado Mes"]
    st.dataframe(df_zona_show, use_container_width=True, hide_index=True)


# ── TAB 4: Gestores ───────────────────────────────────────────────────────────────
with tab4:
    df_gest = resumen_por_gestor(df)
    if "radar_key" not in st.session_state:
        st.session_state.radar_key = 0

    col_chart, col_reset = st.columns([11, 1])
    with col_chart:
        st.plotly_chart(fig_gestores_radar(df_gest), use_container_width=True,
                        key=f"radar_{st.session_state.radar_key}")
    with col_reset:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        if st.button("↺", help="Resetear vista del radar", use_container_width=True):
            st.session_state.radar_key += 1
            st.rerun()

    st.markdown('<div class="section-title">Performance por Gestor</div>', unsafe_allow_html=True)
    df_gest_show = df_gest.copy()
    df_gest_show["saldo_gestionado"] = df_gest_show["saldo_gestionado"].apply(lambda x: f"${x:,.0f}")
    df_gest_show["cobrado"] = df_gest_show["cobrado"].apply(lambda x: f"${x:,.0f}")
    df_gest_show["mora_prom"] = df_gest_show["mora_prom"].apply(lambda x: f"{x:.1f} días")
    df_gest_show["score_prom"] = df_gest_show["score_prom"].apply(lambda x: f"{x:.0f}")
    df_gest_show["efectividad"] = df_gest_show["efectividad"].apply(lambda x: f"{x:.1%}")
    df_gest_show.columns = ["Gestor", "Créditos", "Saldo Gestionado", "Cobrado", "Mora Prom.", "Score Prom.", "Efectividad"]
    st.dataframe(df_gest_show, use_container_width=True, hide_index=True)


# ── TAB 5: Top Deudores ───────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Top Deudores por Saldo en Mora</div>', unsafe_allow_html=True)

    n_top = st.slider("Mostrar top N deudores", 5, 50, 15, step=5)
    df_top = top_deudores(df, n=n_top)

    # Color coding por estado
    def color_estado(val):
        colores = {
            "Vigente": "color: #3FB950",
            "Mora Temprana": "color: #D29922",
            "Mora Avanzada": "color: #F85149",
            "Incobrable": "color: #8B0000",
        }
        return colores.get(val, "")

    df_top_show = df_top.copy()
    df_top_show["saldo_total"] = df_top_show["saldo_total"].apply(lambda x: f"${x:,.0f}")
    df_top_show.columns = ["ID", "Cliente", "Zona", "Saldo Total", "Días Mora", "Bucket", "Score", "Estado", "Gestor"]

    st.dataframe(
        df_top_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=300, max_value=950, format="%d"
            ),
            "Días Mora": st.column_config.NumberColumn("Días Mora", format="%d días"),
        }
    )

    # Export
    csv_export = df_top.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Exportar CSV",
        data=csv_export,
        file_name="top_deudores.csv",
        mime="text/csv",
    )


# ─── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px; padding-top:16px; border-top:1px solid #21262D;
            text-align:center; font-family:'IBM Plex Mono',monospace;
            font-size:0.7rem; color:#7D8590;">
    Cartera Dashboard · MVP v1.0 · Datos en tiempo real (próximamente)
    · Construido con Streamlit + Plotly
</div>
""", unsafe_allow_html=True)
