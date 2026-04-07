"""
Agrega campos ficticios de cartera de créditos al df_enriquecido_muestra_ROL.csv.
Los valores son sintéticos pero coherentes con Categoria_perfil.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

# ── Lectura ──────────────────────────────────────────────────────────────────
df = pd.read_csv("df_enriquecido_muestra_ROL.csv")
n = len(df)

# ── Parámetros por perfil ─────────────────────────────────────────────────────
# mora_min, mora_max, p_judicial, score_min, score_max
PERFIL_CONFIG = {
    "Perfil Excelente":    (0,   0,   0.00, 88, 99),
    "Perfil Superior":     (0,   5,   0.00, 80, 90),
    "Perfil Muy Bueno":    (0,  15,   0.00, 70, 82),
    "Perfil Bueno":        (0,  30,   0.02, 60, 74),
    "Perfil Adecuado":     (0,  45,   0.05, 50, 68),
    "Perfil Con Límites":  (30,  90,  0.10, 35, 55),
    "Perfil Con L�mites":  (30,  90,  0.10, 35, 55),   # encoding alternativo
    "Perfil Insuficiente": (60, 180,  0.25, 20, 42),
    "Perfil Nulo":         (90, 540,  0.55, 5,  28),
}

# ── Gestor ────────────────────────────────────────────────────────────────────
gestores = ["Estudio A", "Estudio B", "Estudio C", "Estudio D"]
df["gestor"] = rng.choice(gestores, size=n)

# ── Tasas y plazos ────────────────────────────────────────────────────────────
tasas_disponibles = [60, 72, 84, 96, 108, 120]   # % anual nominal
plazos_disponibles = [6, 12, 18, 24, 36, 48]

df["tasa_interes_anual"] = rng.choice(tasas_disponibles, size=n)
df["plazo_meses"] = rng.choice(plazos_disponibles, size=n)

# ── Capital original ──────────────────────────────────────────────────────────
# Distribucion log-normal: mayoría entre 100k-800k ARS
capital_base = rng.lognormal(mean=12.8, sigma=0.7, size=n)   # ~360k media
capital_base = np.clip(capital_base, 30_000, 3_000_000).round(-3)
df["capital_original"] = capital_base.astype(int)

# ── Fechas de inicio (entre 2022-01-01 y 2025-01-01) ─────────────────────────
origen = date(2022, 1, 1)
dias_rango = (date(2025, 1, 1) - origen).days
dias_offset = rng.integers(0, dias_rango, size=n)
fechas_inicio = [origen + timedelta(days=int(d)) for d in dias_offset]
df["fecha_inicio"] = fechas_inicio

df["fecha_vencimiento"] = [
    (fi + pd.DateOffset(months=int(pm))).date()
    for fi, pm in zip(pd.to_datetime(df["fecha_inicio"]), df["plazo_meses"])
]

# ── Días de mora y buckets ────────────────────────────────────────────────────
dias_mora_arr = np.zeros(n, dtype=int)
score_arr = np.zeros(n, dtype=int)

for perfil, (mora_min, mora_max, p_jud, sc_min, sc_max) in PERFIL_CONFIG.items():
    mask = df["Categoria_perfil"] == perfil
    cnt = mask.sum()
    if cnt == 0:
        continue
    dias_mora_arr[mask] = rng.integers(mora_min, max(mora_max, mora_min + 1), size=cnt)
    score_arr[mask] = rng.integers(sc_min, sc_max + 1, size=cnt)

df["dias_mora"] = dias_mora_arr
df["score_riesgo"] = score_arr

def bucket(d):
    if d == 0:
        return "Al día"
    elif d <= 30:
        return "1-30 días"
    elif d <= 60:
        return "31-60 días"
    elif d <= 90:
        return "61-90 días"
    elif d <= 180:
        return "91-180 días"
    else:
        return "+180 días"

df["bucket_mora"] = df["dias_mora"].apply(bucket)

# ── Estado crédito ────────────────────────────────────────────────────────────
def estado(row):
    d = row["dias_mora"]
    perfil = row["Categoria_perfil"]
    cfg = PERFIL_CONFIG.get(perfil, (0, 0, 0, 50, 70))
    p_jud = cfg[2]
    if d == 0:
        return "Vigente"
    elif d <= 90:
        return "En mora"
    elif rng.random() < p_jud:
        return "En gestión judicial"
    else:
        return "En mora"

df["estado_credito"] = df.apply(estado, axis=1)

# ── Saldos ────────────────────────────────────────────────────────────────────
# Porcentaje pagado: créditos más viejos tienen más capital amortizado
# (simplificado: cuotas pagadas proporcional al tiempo transcurrido)
hoy = date(2026, 4, 7)

pct_transcurrido = np.array([
    min((hoy - fi).days / max((fv - fi).days, 1), 1.0)
    for fi, fv in zip(
        pd.to_datetime(df["fecha_inicio"]).dt.date,
        pd.to_datetime(df["fecha_vencimiento"]).dt.date,
    )
])

# Si hay mora, el deudor dejó de pagar antes — reducimos el pct pagado
pct_mora_penalty = np.clip(df["dias_mora"].values / 365, 0, 0.8)
pct_amortizado = np.clip(pct_transcurrido - pct_mora_penalty, 0, 1)

saldo_capital = (df["capital_original"].values * (1 - pct_amortizado)).round(-2).astype(int)
df["saldo_capital"] = saldo_capital

# Intereses devengados: saldo * tasa_diaria * dias_mora (como mínimo)
tasa_diaria = df["tasa_interes_anual"].values / 100 / 365
dias_devengado = np.maximum(df["dias_mora"].values, 30)   # mínimo 30 días devengados
intereses = (saldo_capital * tasa_diaria * dias_devengado).round(-2).astype(int)
df["intereses_devengados"] = intereses
df["saldo_total"] = saldo_capital + intereses

# ── Pagos último mes ──────────────────────────────────────────────────────────
# Monto cobrado en el último mes: cuota mensual (capital/plazo) si pagó, 0 si no.
# Si dias_mora <= 30 → 90% de probabilidad de haber pagado; si > 30 → 15%.
cuota_mensual = (df["capital_original"].values / df["plazo_meses"].values).round(-2).astype(int)
p_pago = np.where(df["dias_mora"].values <= 30, 0.9, 0.15)
pago_binario = rng.binomial(1, p_pago)
df["pagos_ultimo_mes"] = (cuota_mensual * pago_binario).astype(int)

# ── Fecha último pago ─────────────────────────────────────────────────────────
fecha_ultimo_pago = []
for i, row in df.iterrows():
    dias = int(row["dias_mora"])
    if dias == 0:
        # pagó en los últimos 30 días
        offset = rng.integers(1, 31)
        fecha_ultimo_pago.append(hoy - timedelta(days=int(offset)))
    else:
        # último pago fue aproximadamente hace dias_mora días (±15)
        jitter = rng.integers(-15, 16)
        offset = max(dias + int(jitter), 1)
        fecha_ultimo_pago.append(hoy - timedelta(days=offset))

df["fecha_ultimo_pago"] = fecha_ultimo_pago

# ── Guardar ───────────────────────────────────────────────────────────────────
out_cols = list(df.columns)
df.to_csv("df_enriquecido_muestra_ROL.csv", index=False)

print(f"Archivo guardado: {len(df)} filas, {len(df.columns)} columnas")
print("\nNuevas columnas agregadas:")
nuevas = ["gestor","capital_original","saldo_capital","intereses_devengados",
          "saldo_total","tasa_interes_anual","plazo_meses","fecha_inicio",
          "fecha_vencimiento","dias_mora","bucket_mora","estado_credito",
          "score_riesgo","pagos_ultimo_mes","fecha_ultimo_pago"]
for col in nuevas:
    print(f"  {col}: {df[col].dtype} — ej: {df[col].iloc[0]}")
