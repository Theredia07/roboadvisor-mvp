# RoboAdvisor MVP (Streamlit)

Un prototipo sencillo de **RoboAdvisor** para Europa: asignación por perfil (Conservador/Moderado/Agresivo),
aportaciones mensuales (DCA) y rebalanceo periódico entre **VWCE (acciones globales)** y **AGGH (bonos globales)**.

## ⚙️ Requisitos
- Python 3.10+
- Pip

## 🚀 Instalación
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Ejecutar la app
```bash
streamlit run app.py
```

## 🌐 Despliegue rápido (Streamlit Community Cloud)
1. Crea un repo en GitHub y sube estos archivos.
2. Ve a https://share.streamlit.io/ e inicia sesión con tu GitHub.
3. Selecciona el repo y `app.py` como archivo principal.
4. Añade los **secrets** si luego integras brokers/APIs. (Para este MVP no hace falta)

## 🧠 Notas
- Los datos se obtienen con `yfinance`. Si algún ticker no existe en tu región, cambia el `symbol` a uno válido.
- Este proyecto es **educativo**: no es asesoramiento financiero ni gestiona dinero real.