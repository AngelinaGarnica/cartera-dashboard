"""
Capa de abstracción de datos.
Hoy lee desde CSV. En producción, reemplazar los métodos con llamadas a la API real.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


DATA_PATH = Path(__file__).parent.parent / "data" / "cartera.csv"


# ─── Carga principal ────────────────────────────────────────────────────────────

def cargar_cartera(path: str = None) -> pd.DataFrame:
    """
    Punto de entrada principal. En producción: reemplazar por fetch a la API.
    """
    p = Path(path) if path else DATA_PATH
    df = pd.read_csv(p, parse_dates=["fecha_inicio", "fecha_vencimiento"])
    df = _limpiar_y_enriquecer(df)
    return df


def _limpiar_y_enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Score en categorías legibles
    df["categoria_score"] = pd.cut(
        df["score_riesgo"],
        bins=[0, 400, 550, 700, 850, 1000],
        labels=["Muy Alto Riesgo", "Alto Riesgo", "Riesgo Medio", "Bajo Riesgo", "Muy Bajo Riesgo"]
    )

    # Orden de buckets para gráficos
    df["bucket_mora"] = pd.Categorical(
        df["bucket_mora"],
        categories=["Al día", "1-30 días", "31-60 días", "61-90 días", "91-180 días", "+180 días"],
        ordered=True
    )

    df["estado_credito"] = pd.Categorical(
        df["estado_credito"],
        categories=["Vigente", "Mora Temprana", "Mora Avanzada", "Incobrable"],
        ordered=True
    )

    # Tasa de recupero por crédito (pagos / saldo total)
    df["tasa_recupero"] = np.where(
        df["saldo_total"] > 0,
        (df["pagos_ultimo_mes"] / df["saldo_total"]).clip(0, 1),
        0
    )

    return df


# ─── KPIs agregados ─────────────────────────────────────────────────────────────

def calcular_kpis(df: pd.DataFrame) -> dict:
    total_creditos = len(df)
    saldo_total_cartera = df["saldo_total"].sum()
    capital_total = df["capital_original"].sum()

    en_mora = df[df["dias_mora"] > 0]
    tasa_mora = len(en_mora) / total_creditos
    saldo_en_mora = en_mora["saldo_total"].sum()
    ratio_mora_saldo = saldo_en_mora / saldo_total_cartera if saldo_total_cartera > 0 else 0

    total_cobrado = df["pagos_ultimo_mes"].sum()
    total_exigible = df[df["dias_mora"] > 0]["saldo_total"].sum()
    tasa_recupero = total_cobrado / total_exigible if total_exigible > 0 else 0

    score_promedio = df["score_riesgo"].mean()
    pct_alto_riesgo = (df["score_riesgo"] < 500).sum() / total_creditos

    incobrables = df[df["estado_credito"] == "Incobrable"]
    saldo_incobrable = incobrables["saldo_total"].sum()
    provision_estimada = saldo_incobrable * 0.85 + df[df["estado_credito"] == "Mora Avanzada"]["saldo_total"].sum() * 0.40

    return {
        "total_creditos": total_creditos,
        "saldo_total_cartera": saldo_total_cartera,
        "capital_total": capital_total,
        "tasa_mora_cantidad": tasa_mora,
        "saldo_en_mora": saldo_en_mora,
        "ratio_mora_saldo": ratio_mora_saldo,
        "total_cobrado_mes": total_cobrado,
        "tasa_recupero": tasa_recupero,
        "score_promedio": score_promedio,
        "pct_alto_riesgo": pct_alto_riesgo,
        "saldo_incobrable": saldo_incobrable,
        "provision_estimada": provision_estimada,
    }


def resumen_aging(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("bucket_mora", observed=True).agg(
        cantidad=("id_credito", "count"),
        saldo=("saldo_total", "sum"),
        score_prom=("score_riesgo", "mean"),
        recupero_prom=("tasa_recupero", "mean"),
    ).reset_index()
    g["pct_cantidad"] = g["cantidad"] / g["cantidad"].sum()
    g["pct_saldo"] = g["saldo"] / g["saldo"].sum()
    return g


def resumen_por_zona(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("zona").agg(
        cantidad=("id_credito", "count"),
        saldo=("saldo_total", "sum"),
        mora_prom_dias=("dias_mora", "mean"),
        score_prom=("score_riesgo", "mean"),
        cobrado=("pagos_ultimo_mes", "sum"),
    ).reset_index().sort_values("saldo", ascending=False)


def resumen_por_gestor(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("gestor").agg(
        cantidad=("id_credito", "count"),
        saldo_gestionado=("saldo_total", "sum"),
        cobrado=("pagos_ultimo_mes", "sum"),
        mora_prom=("dias_mora", "mean"),
        score_prom=("score_riesgo", "mean"),
    ).reset_index()
    g["efectividad"] = g["cobrado"] / g["saldo_gestionado"]
    return g


def distribucion_score(df: pd.DataFrame) -> pd.DataFrame:
    bins = list(range(300, 1000, 50))
    labels = [f"{b}-{b+50}" for b in bins[:-1]]
    df = df.copy()
    df["score_bin"] = pd.cut(df["score_riesgo"], bins=bins, labels=labels)
    return df.groupby("score_bin", observed=True).agg(
        cantidad=("id_credito", "count"),
        saldo=("saldo_total", "sum"),
    ).reset_index()


def top_deudores(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        df[df["dias_mora"] > 0]
        .sort_values("saldo_total", ascending=False)
        .head(n)[["id_credito", "cliente", "zona", "saldo_total", "dias_mora",
                   "bucket_mora", "score_riesgo", "estado_credito", "gestor"]]
    )
