import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# Configuración inicial de la página
st.set_page_config(page_title="Lean Six Sigma Analytics", layout="wide", page_icon="📊")

# ==========================================
# 1. GENERACIÓN DE DATOS (Simulación)
# ==========================================
@st.cache_data
def generar_datos():
    """
    Genera un dataset sintético simulando un proceso de manufactura.
    Relación matemática insertada: El diámetro depende ligeramente de la temperatura.
    """
    np.random.seed(42)
    n_samples = 500
    
    # Variables de entrada (X)
    temperatura = np.random.normal(loc=85, scale=5, size=n_samples) # Temperatura del horno
    turno = np.random.choice(['Mañana', 'Tarde', 'Noche'], size=n_samples)
    
    # Variable de salida (Y) - Diámetro (Target = 10.0 mm)
    # Introducimos una relación: a mayor temperatura, mayor diámetro + ruido aleatorio
    ruido = np.random.normal(loc=0, scale=0.15, size=n_samples)
    diametro = 10.0 + (temperatura - 85) * 0.05 + ruido
    
    # Crear DataFrame
    df = pd.DataFrame({
        'ID_Pieza': range(1, n_samples + 1),
        'Turno': turno,
        'Temperatura_C': temperatura,
        'Diametro_mm': diametro
    })
    return df

df = generar_datos()

# ==========================================
# 2. BARRA LATERAL: CONTROLES REACTIVOS
# ==========================================
st.sidebar.header("⚙️ Parámetros del Proceso")
st.sidebar.markdown("Ajusta los límites del cliente y filtra los datos para observar cómo reaccionan las métricas.")

# Filtros
turno_seleccionado = st.sidebar.multiselect(
    "Filtrar por Turno:", 
    options=df['Turno'].unique(), 
    default=df['Turno'].unique()
)

# Límites de Especificación (USL / LSL)
target = 10.0
lsl = st.sidebar.number_input("Límite Inferior (LSL)", value=9.5, step=0.1)
usl = st.sidebar.number_input("Límite Superior (USL)", value=10.5, step=0.1)

# Aplicar filtros
df_filtrado = df[df['Turno'].isin(turno_seleccionado)].copy()

# ==========================================
# 3. LÓGICA DE CÁLCULOS ESTADÍSTICOS
# ==========================================
# Medidas de tendencia central y dispersión
mu = df_filtrado['Diametro_mm'].mean()
sigma = df_filtrado['Diametro_mm'].std()

# Análisis de Capacidad
# Cp = Tolerancia / Variación del Proceso
cp = (usl - lsl) / (6 * sigma) if sigma > 0 else 0
# Cpk = Penaliza si la media no está centrada
cpk_upper = (usl - mu) / (3 * sigma) if sigma > 0 else 0
cpk_lower = (mu - lsl) / (3 * sigma) if sigma > 0 else 0
cpk = min(cpk_upper, cpk_lower)

# Defectos y Nivel Sigma (Aproximación DPMO)
defectos = df_filtrado[(df_filtrado['Diametro_mm'] > usl) | (df_filtrado['Diametro_mm'] < lsl)].shape[0]
dpmo = (defectos / len(df_filtrado)) * 1_000_000 if len(df_filtrado) > 0 else 0
# Nivel Sigma aproximado (usando la inversa de la normal estándar + shift de 1.5)
if dpmo == 0:
    nivel_sigma = 6.0
else:
    # stats.norm.ppf calcula el cuantil de la normal
    nivel_sigma = abs(stats.norm.ppf(defectos / len(df_filtrado))) + 1.5 

# ==========================================
# 4. CUERPO DE LA APLICACIÓN (STORYTELLING)
# ==========================================
st.title("📈 Asistente de Análisis Lean Six Sigma")
st.markdown("""
Bienvenido al análisis interactivo del proceso. Esta herramienta transforma los datos crudos en **conocimiento accionable**. 
Navegaremos desde la compresión básica de nuestra producción hasta la identificación de causas raíz.
""")

# --- SECCIÓN A: KPI's Principales ---
st.markdown("### 1. Resumen de Desempeño (Métricas Clave)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Media (μ)", f"{mu:.3f} mm")
col2.metric("Desviación Est. (σ)", f"{sigma:.3f} mm")
col3.metric("Índice Cpk", f"{cpk:.2f}", delta="Pobre (<1.33)" if cpk < 1.33 else "Capaz (>1.33)", delta_color="inverse")
col4.metric("Nivel Sigma", f"{nivel_sigma:.1f} σ")

st.divider()

# --- SECCIÓN B: Estadística Descriptiva ---
st.markdown("### 2. Distribución del Proceso frente al Cliente")
st.markdown("Visualizamos la **Voz del Proceso** (Histograma) contra la **Voz del Cliente** (Líneas Rojas LSL/USL).")

fig_hist = px.histogram(
    df_filtrado, x='Diametro_mm', 
    nbins=30, 
    marginal='box', # Agrega un Boxplot arriba para identificar outliers
    color_discrete_sequence=['#1f77b4'],
    opacity=0.7
)
# Agregar líneas de especificación
fig_hist.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
fig_hist.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
fig_hist.add_vline(x=target, line_dash="solid", line_color="green", annotation_text="Target")

fig_hist.update_layout(xaxis_title="Diámetro (mm)", yaxis_title="Frecuencia", template="plotly_white")
st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# --- SECCIÓN C: Control Estadístico (SPC) ---
st.markdown("### 3. Control Estadístico de Procesos (Gráfico de Control X)")
st.markdown("¿Existen causas especiales de variación? Evaluamos la estabilidad temporal del proceso.")

# Cálculos para Gráfico de Control (Aproximación simple con Media +/- 3 Sigma)
ucl = mu + (3 * sigma)
lcl = mu - (3 * sigma)

fig_spc = go.Figure()
# Datos del proceso
fig_spc.add_trace(go.Scatter(x=df_filtrado['ID_Pieza'], y=df_filtrado['Diametro_mm'], 
                             mode='lines+markers', name='Diámetro', marker=dict(size=5, color='gray')))
# Línea central
fig_spc.add_trace(go.Scatter(x=df_filtrado['ID_Pieza'], y=[mu]*len(df_filtrado), 
                             mode='lines', name='Media (LC)', line=dict(color='blue', width=2)))
# Límites de control
fig_spc.add_trace(go.Scatter(x=df_filtrado['ID_Pieza'], y=[ucl]*len(df_filtrado), 
                             mode='lines', name='UCL (+3σ)', line=dict(color='orange', dash='dash')))
fig_spc.add_trace(go.Scatter(x=df_filtrado['ID_Pieza'], y=[lcl]*len(df_filtrado), 
                             mode='lines', name='LCL (-3σ)', line=dict(color='orange', dash='dash')))

# Resaltar puntos fuera de control (Regla 1 de Nelson simple)
outliers_spc = df_filtrado[(df_filtrado['Diametro_mm'] > ucl) | (df_filtrado['Diametro_mm'] < lcl)]
fig_spc.add_trace(go.Scatter(x=outliers_spc['ID_Pieza'], y=outliers_spc['Diametro_mm'], 
                             mode='markers', name='Causa Especial', marker=dict(size=10, color='red', symbol='x')))

fig_spc.update_layout(xaxis_title="Secuencia de Producción (ID Pieza)", yaxis_title="Diámetro (mm)", template="plotly_white")
st.plotly_chart(fig_spc, use_container_width=True)

st.divider()

# --- SECCIÓN D: Análisis de Relación (Regresión) ---
st.markdown("### 4. Análisis de Causa Raíz (Relación de Variables)")
st.markdown("A través del análisis de correlación y regresión lineal, evaluamos cómo la **Temperatura** (X) impacta el **Diámetro** (Y).")

col_scatter, col_stats = st.columns([2, 1])

with col_scatter:
    # Gráfico de dispersión con línea de tendencia (Regresión Mínimos Cuadrados Ordinarios OLS)
    fig_scatter = px.scatter(
        df_filtrado, x='Temperatura_C', y='Diametro_mm', 
        color='Turno', trendline='ols',
        title="Dispersión: Temperatura vs Diámetro",
        opacity=0.6,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_scatter.update_layout(template="plotly_white")
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_stats:
    st.markdown("#### Hallazgos del Modelo")
    # Calcular Correlación de Pearson
    correlacion, p_value = stats.pearsonr(df_filtrado['Temperatura_C'], df_filtrado['Diametro_mm'])
    
    st.write(f"**Coeficiente de Correlación (r):** {correlacion:.2f}")
    if abs(correlacion) > 0.7:
        st.success("Correlación Fuerte detectada.")
    elif abs(correlacion) > 0.3:
        st.warning("Correlación Moderada detectada.")
    else:
        st.info("Correlación Débil.")
        
    st.write(f"**Valor P (p-value):** {p_value:.4f}")
    if p_value < 0.05:
        st.success("La relación es **estadísticamente significativa** (Rechazamos H0).")
    else:
        st.error("No hay evidencia suficiente de relación (Aceptamos H0).")
        
    st.info("💡 **Conclusión:** Si la regresión es significativa, controlar la temperatura del horno es una causa raíz vital para reducir la variación del diámetro y mejorar el Nivel Sigma.")