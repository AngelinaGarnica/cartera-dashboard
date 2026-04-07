"""
Capa de abstracción de datos.
Hoy lee desde df_enriquecido_muestra_ROL.csv. En producción, reemplazar con llamadas a la API real.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import wkt as shapely_wkt


DATA_PATH = Path(__file__).parent.parent / "data" / "df_enriquecido_muestra_ROL.csv"


# ─── Carga principal ────────────────────────────────────────────────────────────

def cargar_cartera(path: str = None) -> pd.DataFrame:
    """
    Punto de entrada principal. En producción: reemplazar por fetch a la API.
    """
    p = Path(path) if path else DATA_PATH
    df = pd.read_csv(p, parse_dates=["fecha_inicio", "fecha_vencimiento", "fecha_ultimo_pago"])

    # Columnas identificadoras derivadas de los datos reales de la unidad
    df["id_credito"] = df["unidad"].astype(str)
    df["cliente"] = (
        df["calle_unidad"].str.strip() + " " + df["nro_unidad"].astype(str)
    )

    # Columna geográfica legible para el dashboard
    df["barrio"] = df["barrio_unidad"].str.strip().str.title()

    # Columna zona legible (código numérico → "Zona 01")
    df["zona_label"] = "Zona " + df["zona"].astype(str).str.zfill(2)

    df = _limpiar_y_enriquecer(df)
    return df


def _limpiar_y_enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Score en categorías legibles (escala 1–99)
    df["categoria_score"] = pd.cut(
        df["score_riesgo"],
        bins=[0, 20, 40, 60, 80, 100],
        labels=["Muy Alto Riesgo", "Alto Riesgo", "Riesgo Medio", "Bajo Riesgo", "Muy Bajo Riesgo"],
        right=True,
    )

    # Orden de buckets para gráficos
    df["bucket_mora"] = pd.Categorical(
        df["bucket_mora"],
        categories=["Al día", "1-30 días", "31-60 días", "61-90 días", "91-180 días", "+180 días"],
        ordered=True,
    )

    df["estado_credito"] = pd.Categorical(
        df["estado_credito"],
        categories=["Vigente", "En mora", "En gestión judicial"],
        ordered=True,
    )

    # Tasa de recupero por crédito (pago del mes / saldo total)
    df["tasa_recupero"] = np.where(
        df["saldo_total"] > 0,
        (df["pagos_ultimo_mes"] / df["saldo_total"]).clip(0, 1),
        0,
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
    pct_alto_riesgo = (df["score_riesgo"] < 40).sum() / total_creditos

    judiciales = df[df["estado_credito"] == "En gestión judicial"]
    mora_avanzada = df[(df["estado_credito"] == "En mora") & (df["dias_mora"] > 90)]
    saldo_incobrable = judiciales["saldo_total"].sum()
    provision_estimada = (
        saldo_incobrable * 0.85
        + mora_avanzada["saldo_total"].sum() * 0.40
    )

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
    return df.groupby("barrio").agg(
        cantidad=("id_credito", "count"),
        saldo=("saldo_total", "sum"),
        mora_prom_dias=("dias_mora", "mean"),
        score_prom=("score_riesgo", "mean"),
        cobrado=("pagos_ultimo_mes", "sum"),
    ).reset_index().rename(columns={"barrio": "zona"}).sort_values("saldo", ascending=False)


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
    bins = list(range(0, 105, 10))
    labels = [f"{b}-{b+10}" for b in bins[:-1]]
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
        .head(n)[["id_credito", "cliente", "barrio", "saldo_total", "dias_mora",
                   "bucket_mora", "score_riesgo", "estado_credito", "gestor"]]
    )


# ─── Mapa de polígonos ──────────────────────────────────────────────────────────

_BUCKET_COLORS_RGB = {
    "Al día":        [63, 185, 80, 180],
    "1-30 días":     [210, 153, 34, 180],
    "31-60 días":    [240, 136, 62, 180],
    "61-90 días":    [248, 81, 73, 180],
    "91-180 días":   [207, 34, 46, 180],
    "+180 días":     [139, 0, 0, 200],
}

_TRANSFORMER = Transformer.from_crs(22184, 4326, always_xy=True)


def _wkt_to_geojson_coords(geom_wkt: str) -> list | None:
    """Convierte WKT (EPSG:22184) a lista de coordenadas GeoJSON en WGS84."""
    try:
        poly = shapely_wkt.loads(geom_wkt)
        coords = [
            list(_TRANSFORMER.transform(x, y))
            for x, y in poly.exterior.coords
        ]
        return coords
    except Exception:
        return None


def preparar_geodata(df: pd.DataFrame) -> list[dict]:
    """
    Devuelve lista de features GeoJSON con propiedades de cartera.
    Solo incluye filas con geometría válida.
    """
    features = []
    df_geo = df[df["geometry"].notna()].copy()

    for _, row in df_geo.iterrows():
        coords = _wkt_to_geojson_coords(row["geometry"])
        if coords is None:
            continue

        bucket = str(row["bucket_mora"])
        color = _BUCKET_COLORS_RGB.get(bucket, [100, 100, 100, 150])

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords],
            },
            "properties": {
                "id": row["id_credito"],
                "direccion": row["cliente"],
                "barrio": row["barrio"],
                "gestor": row["gestor"],
                "bucket": bucket,
                "dias_mora": int(row["dias_mora"]),
                "saldo_total": int(row["saldo_total"]),
                "estado": str(row["estado_credito"]),
                "score": int(row["score_riesgo"]),
                "fill_color": color,
            },
        })

    return features
