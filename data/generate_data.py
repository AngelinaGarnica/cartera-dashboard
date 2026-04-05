"""
Generador de datos sintéticos para cartera de créditos personales.
En producción, este módulo será reemplazado por llamadas a la API real.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

N = 500  # cantidad de créditos

def generar_cartera():
    hoy = datetime(2025, 3, 30)

    nombres = [
        "García", "Fernández", "López", "Martínez", "Rodríguez",
        "Pérez", "González", "Sánchez", "Romero", "Torres",
        "Díaz", "Flores", "Ruiz", "Jiménez", "Morales"
    ]
    nombres_pila = [
        "Ana", "Carlos", "María", "Luis", "Laura",
        "Diego", "Sofía", "Martín", "Valentina", "Pablo",
        "Lucía", "Agustín", "Camila", "Nicolás", "Florencia"
    ]

    zonas = ["CABA", "GBA Norte", "GBA Sur", "GBA Oeste", "Córdoba", "Rosario", "Mendoza", "Tucumán"]
    productos = ["Préstamo Personal", "Préstamo Nómina", "Refinanciación"]
    gestores = ["Estudio A", "Estudio B", "Estudio C", "Estudio D"]

    ids = [f"CR-{str(i).zfill(5)}" for i in range(1, N+1)]
    cliente = [f"{random.choice(nombres_pila)} {random.choice(nombres)}" for _ in range(N)]
    dni = [str(random.randint(20000000, 45000000)) for _ in range(N)]
    zona = np.random.choice(zonas, N, p=[0.25, 0.15, 0.15, 0.1, 0.15, 0.1, 0.05, 0.05])
    producto = np.random.choice(productos, N, p=[0.6, 0.3, 0.1])
    gestor = np.random.choice(gestores, N)

    capital_original = np.random.choice(
        [50000, 100000, 150000, 200000, 300000, 500000, 750000, 1000000],
        N,
        p=[0.1, 0.2, 0.2, 0.2, 0.15, 0.08, 0.05, 0.02]
    ).astype(float)
    capital_original += np.random.uniform(-5000, 5000, N)

    tasa_interes = np.random.uniform(0.08, 0.25, N)
    plazo_meses = np.random.choice([6, 12, 18, 24, 36, 48], N, p=[0.1, 0.3, 0.25, 0.2, 0.1, 0.05])

    fecha_inicio_dias = np.random.randint(-720, -30, N)
    fecha_inicio = [hoy + timedelta(days=int(d)) for d in fecha_inicio_dias]
    fecha_vencimiento = [fi + timedelta(days=int(p * 30)) for fi, p in zip(fecha_inicio, plazo_meses)]

    # Porcentaje pagado según tiempo transcurrido + ruido
    progreso_tiempo = np.clip(
        (-np.array(fecha_inicio_dias) / (plazo_meses * 30)) + np.random.uniform(-0.15, 0.15, N),
        0, 1
    )

    # Score de riesgo (0-1000, similar a Veraz)
    score_base = np.random.normal(580, 150, N)
    score_riesgo = np.clip(score_base, 300, 950).astype(int)

    # Días de mora: correlacionado inversamente con el score
    prob_mora = np.clip(1 - score_riesgo / 950 + np.random.uniform(-0.1, 0.1, N), 0.02, 0.85)
    tiene_mora = np.random.random(N) < prob_mora

    dias_mora = np.where(
        tiene_mora,
        np.random.choice([1, 15, 30, 45, 60, 90, 120, 180, 270, 360], N,
                         p=[0.1, 0.12, 0.15, 0.12, 0.12, 0.1, 0.1, 0.08, 0.06, 0.05]),
        0
    )
    dias_mora = dias_mora + np.where(tiene_mora, np.random.randint(0, 15, N), 0)

    # Saldo deudor
    saldo_capital = capital_original * (1 - progreso_tiempo * 0.8)
    intereses_devengados = saldo_capital * tasa_interes * (dias_mora / 365)
    saldo_total = saldo_capital + intereses_devengados

    # Bucket de mora (aging)
    def bucket_mora(dias):
        if dias == 0:
            return "Al día"
        elif dias <= 30:
            return "1-30 días"
        elif dias <= 60:
            return "31-60 días"
        elif dias <= 90:
            return "61-90 días"
        elif dias <= 180:
            return "91-180 días"
        else:
            return "+180 días"

    bucket = [bucket_mora(d) for d in dias_mora]

    # Estado del crédito
    def estado(dias, venc):
        if dias == 0:
            return "Vigente"
        elif dias <= 90:
            return "Mora Temprana"
        elif dias <= 180:
            return "Mora Avanzada"
        else:
            return "Incobrable"

    estado_credito = [estado(d, v) for d, v in zip(dias_mora, fecha_vencimiento)]

    # Pagos del último mes (cobranza)
    pagos_ultimo_mes = np.where(
        np.random.random(N) < (score_riesgo / 950) * 0.7,
        capital_original * np.random.uniform(0.02, 0.08, N),
        0
    )

    # Fecha último pago
    dias_ult_pago = np.random.randint(1, 90, N)
    fecha_ult_pago = [hoy - timedelta(days=int(d)) for d in dias_ult_pago]
    fecha_ult_pago = [f.strftime("%Y-%m-%d") if p > 0 else None
                      for f, p in zip(fecha_ult_pago, pagos_ultimo_mes)]

    df = pd.DataFrame({
        "id_credito": ids,
        "cliente": cliente,
        "dni": dni,
        "zona": zona,
        "producto": producto,
        "gestor": gestor,
        "capital_original": capital_original.round(2),
        "saldo_capital": saldo_capital.round(2),
        "intereses_devengados": intereses_devengados.round(2),
        "saldo_total": saldo_total.round(2),
        "tasa_interes_anual": (tasa_interes * 100).round(2),
        "plazo_meses": plazo_meses,
        "fecha_inicio": [f.strftime("%Y-%m-%d") for f in fecha_inicio],
        "fecha_vencimiento": [f.strftime("%Y-%m-%d") for f in fecha_vencimiento],
        "dias_mora": dias_mora.astype(int),
        "bucket_mora": bucket,
        "estado_credito": estado_credito,
        "score_riesgo": score_riesgo,
        "pagos_ultimo_mes": pagos_ultimo_mes.round(2),
        "fecha_ultimo_pago": fecha_ult_pago,
    })

    return df


if __name__ == "__main__":
    df = generar_cartera()
    out_path = os.path.join(os.path.dirname(__file__), "cartera.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Dataset generado: {len(df)} créditos → {out_path}")
    print(df.head(3).to_string())
