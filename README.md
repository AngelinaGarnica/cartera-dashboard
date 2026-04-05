# 📊 Dashboard de Cartera de Deuda

Sistema de seguimiento de cartera de créditos personales.
Construido con **Python · Streamlit · Plotly**.

---

## 🚀 Instalación y Ejecución

```bash
# 1. Clonar / descomprimir el proyecto
cd cartera_dashboard

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Generar datos de ejemplo (solo primera vez)
python data/generate_data.py

# 5. Lanzar dashboard
streamlit run app.py
```

El dashboard se abre en `http://localhost:8501`

---

## 📁 Estructura del Proyecto

```
cartera_dashboard/
│
├── app.py                  ← Streamlit app (punto de entrada)
├── requirements.txt
│
├── data/
│   ├── generate_data.py    ← Generador de CSV sintético (reemplazar por API)
│   └── cartera.csv         ← Datos generados
│
└── src/
    ├── data_loader.py      ← Capa de datos (CSV → API ready)
    └── charts.py           ← Todas las visualizaciones Plotly
```

---

## 📊 KPIs y Métricas incluidas

| Métrica | Descripción |
|---|---|
| **Tasa de Mora (Saldo)** | % del saldo total en situación de mora |
| **Tasa de Mora (Cantidad)** | % de créditos con días de atraso > 0 |
| **Aging / Buckets** | Distribución por rango de días en mora |
| **Tasa de Recupero** | Cobros del mes / Saldo en mora |
| **Score de Riesgo** | Distribución y correlación con mora |
| **Performance por Gestor** | Efectividad, cobranza, saldo gestionado |
| **Análisis Geográfico** | Mora y cobranza por zona |
| **Provisión Estimada** | Cálculo simplificado de previsiones |

---

## 🔌 Conectar a una API real

Editar **`src/data_loader.py`**, función `cargar_cartera()`:

```python
def cargar_cartera(path=None) -> pd.DataFrame:
    # PRODUCCIÓN: reemplazar esto
    # response = requests.get("https://mi-api.com/v1/cartera", headers={"Authorization": "Bearer TOKEN"})
    # df = pd.DataFrame(response.json()["data"])
    
    # MVP: leer CSV
    df = pd.read_csv(DATA_PATH, parse_dates=["fecha_inicio", "fecha_vencimiento"])
    return _limpiar_y_enriquecer(df)
```

El resto del sistema no necesita cambios.

---

## 🗺 Roadmap

### Fase 1 — MVP ✅ (actual)
- Dashboard visual con KPIs clave
- Datos desde CSV
- Filtros por zona, gestor, estado, score
- Exportación de top deudores

### Fase 2 — Integración API
- [ ] Conexión a API REST real
- [ ] Autenticación JWT
- [ ] Actualización automática cada N minutos
- [ ] Manejo de múltiples carteras

### Fase 3 — Analytics Avanzado
- [ ] Modelo de scoring propio (ML)
- [ ] Proyección de recupero
- [ ] Alertas por email/Slack
- [ ] Comparativa histórica (series de tiempo)

### Fase 4 — Bot de Gestión
- [ ] Bot WhatsApp/Telegram integrado
- [ ] Generación automática de acciones de cobranza
- [ ] Asignación inteligente de gestores
- [ ] Reportes automáticos schedulados

---

## 🛠 Stack Técnico

- **Python 3.11+**
- **Streamlit** — interfaz web
- **Plotly** — visualizaciones interactivas
- **Pandas / NumPy** — procesamiento de datos

---

*Cartera Dashboard MVP v1.0*
