import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Contable - Cliente",
    page_icon="📊",
    layout="wide"
)

# Directorios
BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / "datos"
CLIENTES_FILE = BASE_DIR / "clientes.json"

# Crear directorios si no existen
DATOS_DIR.mkdir(exist_ok=True)

# Cargar configuración de clientes
def cargar_clientes():
    """Carga la configuración de clientes desde el JSON"""
    if CLIENTES_FILE.exists():
        with open(CLIENTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clientes": {}, "admin": {"codigo": "admin2024", "nombre": "Administrador"}}

# Funciones auxiliares
def procesar_excel(archivo):
    """Procesa el archivo Excel con el formato estándar"""
    try:
        df = pd.read_excel(archivo, sheet_name=0, header=None)
        
        fechas_raw = df.iloc[2, 2:].values
        fechas = []
        for fecha in fechas_raw:
            if pd.notna(fecha):
                if isinstance(fecha, datetime):
                    fechas.append(fecha.strftime('%Y-%m'))
                else:
                    fechas.append(str(fecha)[:7])
        
        conceptos = {
            'Ventas': df.iloc[3, 2:2+len(fechas)].values,
            'Compras CF': df.iloc[4, 2:2+len(fechas)].values,
            'Compras Exentas': df.iloc[5, 2:2+len(fechas)].values,
            'Sueldos y CS': df.iloc[6, 2:2+len(fechas)].values,
            'Margen Operativo': df.iloc[7, 2:2+len(fechas)].values
        }
        
        data = {'Mes': fechas}
        data.update(conceptos)
        df_limpio = pd.DataFrame(data)
        
        for col in df_limpio.columns:
            if col != 'Mes':
                df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')
        
        df_limpio['Total Compras'] = df_limpio['Compras CF'] + df_limpio['Compras Exentas']
        df_limpio['Margen Bruto'] = df_limpio['Ventas'] - df_limpio['Total Compras']
        df_limpio['% Margen Bruto'] = (df_limpio['Margen Bruto'] / df_limpio['Ventas'] * 100).round(2)
        df_limpio['% Margen Operativo'] = (df_limpio['Margen Operativo'] / df_limpio['Ventas'] * 100).round(2)
        df_limpio['Ratio Ventas/Sueldos'] = (df_limpio['Ventas'] / df_limpio['Sueldos y CS']).round(2)
        
        return df_limpio
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

def formatear_monto(valor):
    """Formatea valores en millones"""
    if pd.isna(valor):
        return "N/A"
    return f"${valor/1_000_000:,.1f}M"

def formatear_porcentaje(valor):
    """Formatea valores como porcentaje"""
    if pd.isna(valor):
        return "N/A"
    return f"{valor:.1f}%"

def generar_alertas(df):
    """Genera alertas automáticas"""
    alertas = []
    
    meses_negativos = df[df['Margen Operativo'] < 0]
    if len(meses_negativos) > 0:
        for idx, row in meses_negativos.iterrows():
            alertas.append({
                'tipo': 'danger',
                'titulo': '⚠️ Margen Operativo Negativo',
                'mensaje': f"El mes {row['Mes']} tuvo margen operativo negativo: {formatear_monto(row['Margen Operativo'])}"
            })
    
    if len(df) > 1 and df.iloc[-1]['Margen Operativo'] > 0:
        if any(df.iloc[:-1]['Margen Operativo'] < 0):
            alertas.append({
                'tipo': 'success',
                'titulo': '✅ Recuperación de Margen',
                'mensaje': f"El último mes ({df.iloc[-1]['Mes']}) volvió a margen operativo positivo: {formatear_monto(df.iloc[-1]['Margen Operativo'])}"
            })
    
    return alertas

def obtener_archivo_cliente(codigo_cliente):
    """Busca el archivo Excel del cliente"""
    cliente_dir = DATOS_DIR / codigo_cliente
    if cliente_dir.exists():
        archivos = list(cliente_dir.glob("*.xlsx"))
        if archivos:
            return archivos[0]  # Retorna el primer archivo encontrado
    return None

# Obtener parámetro de cliente desde URL
query_params = st.query_params
codigo_cliente = query_params.get("cliente", None)

# Cargar clientes
config = cargar_clientes()

# CSS personalizado
st.markdown("""
<style>
    .cliente-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Validar acceso
if not codigo_cliente:
    st.error("❌ Acceso no autorizado")
    st.markdown("""
    ### 🔒 Acceso Restringido
    
    Este dashboard es de acceso exclusivo para clientes autorizados.
    
    Si sos cliente y no tenés tu link de acceso, contacta a tu contador.
    """)
    st.stop()

if codigo_cliente not in config['clientes']:
    st.error("❌ Cliente no encontrado")
    st.markdown("El código de cliente proporcionado no es válido.")
    st.stop()

# Obtener datos del cliente
cliente = config['clientes'][codigo_cliente]

if not cliente['activo']:
    st.warning("⚠️ Cuenta inactiva")
    st.markdown("Tu cuenta está temporalmente inactiva. Contacta a tu contador.")
    st.stop()

# Header personalizado
st.markdown(f"""
<div class="cliente-header">
    <h1>📊 Dashboard Contable</h1>
    <h2>{cliente['nombre']}</h2>
    <p>Bienvenido a tu panel de análisis financiero</p>
</div>
""", unsafe_allow_html=True)

# Buscar archivo del cliente
archivo_cliente = obtener_archivo_cliente(codigo_cliente)

if archivo_cliente:
    # Procesar archivo existente
    df_completo = procesar_excel(archivo_cliente)
    
    if df_completo is not None:
        # Sidebar con filtros
        with st.sidebar:
            st.header("🔍 Filtros")
            st.markdown("Selecciona el rango de meses:")
            
            meses_disponibles = df_completo['Mes'].tolist()
            
            col_desde, col_hasta = st.columns(2)
            with col_desde:
                mes_desde = st.selectbox("Desde:", options=meses_disponibles, index=0)
            with col_hasta:
                mes_hasta = st.selectbox("Hasta:", options=meses_disponibles, index=len(meses_disponibles)-1)
            
            idx_desde = meses_disponibles.index(mes_desde)
            idx_hasta = meses_disponibles.index(mes_hasta)
            
            if idx_desde > idx_hasta:
                st.error("⚠️ 'Desde' debe ser anterior a 'Hasta'")
                df = df_completo
            else:
                df = df_completo.iloc[idx_desde:idx_hasta+1].copy()
            
            st.markdown(f"**Mostrando:** {len(df)} meses")
            
            st.markdown("---")
            st.info("💡 Usa los filtros para analizar períodos específicos")
        
        # Generar alertas
        alertas = generar_alertas(df)
        
        if alertas:
            st.header("🚨 Alertas e Insights")
            for alerta in alertas:
                if alerta['tipo'] == 'danger':
                    st.error(f"**{alerta['titulo']}**\n\n{alerta['mensaje']}")
                elif alerta['tipo'] == 'success':
                    st.success(f"**{alerta['titulo']}**\n\n{alerta['mensaje']}")
            st.markdown("---")
        
        # KPIs principales
        st.header("📈 Métricas Principales")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            ventas_total = df['Ventas'].sum()
            ventas_promedio = df['Ventas'].mean()
            st.metric("Ventas Totales", formatear_monto(ventas_total), delta=f"Prom: {formatear_monto(ventas_promedio)}")
        
        with col2:
            compras_total = df['Total Compras'].sum()
            st.metric("Compras Totales", formatear_monto(compras_total))
        
        with col3:
            margen_bruto_total = df['Margen Bruto'].sum()
            margen_bruto_pct = (margen_bruto_total / ventas_total * 100)
            st.metric("Margen Bruto", formatear_monto(margen_bruto_total), delta=f"{margen_bruto_pct:.1f}%")
        
        with col4:
            margen_operativo_total = df['Margen Operativo'].sum()
            margen_operativo_pct = (margen_operativo_total / ventas_total * 100)
            st.metric("Margen Operativo", formatear_monto(margen_operativo_total), delta=f"{margen_operativo_pct:.1f}%")
        
        with col5:
            ratio_promedio = df['Ratio Ventas/Sueldos'].mean()
            st.metric("Ratio Ventas/Sueldos", f"{ratio_promedio:.2f}x")
        
        st.markdown("---")
        
        # Gráficos principales
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Ventas", "🛒 Compras", "💹 Rentabilidad", "📋 Datos"])
        
        with tab1:
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                st.subheader("Evolución de Ventas")
                promedio_ventas = df['Ventas'].mean()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Mes'], y=df['Ventas'], mode='lines+markers', name='Ventas', line=dict(color='#1f77b4', width=3)))
                fig.add_trace(go.Scatter(x=df['Mes'], y=[promedio_ventas] * len(df), mode='lines', name='Promedio', line=dict(color='red', width=2, dash='dash')))
                fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Ventas ($)", hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            with col_der:
                st.subheader("Comparación vs Promedio")
                df['% Dif vs Promedio'] = ((df['Ventas'] - promedio_ventas) / promedio_ventas * 100).round(1)
                colores = ['green' if x > 0 else 'red' for x in df['% Dif vs Promedio']]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df['Mes'], y=df['% Dif vs Promedio'], marker_color=colores))
                fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Diferencia vs Promedio (%)")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                st.subheader("Evolución de Compras")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Mes'], y=df['Compras CF'], mode='lines+markers', name='Compras CF', stackgroup='one'))
                fig.add_trace(go.Scatter(x=df['Mes'], y=df['Compras Exentas'], mode='lines+markers', name='Compras Exentas', stackgroup='one'))
                fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Compras ($)", hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            with col_der:
                st.subheader("Composición de Compras")
                avg_cf = df['Compras CF'].mean()
                avg_exentas = df['Compras Exentas'].mean()
                
                fig = go.Figure()
                fig.add_trace(go.Pie(labels=['Compras CF', 'Compras Exentas'], values=[avg_cf, avg_exentas]))
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                st.subheader("Margen Operativo")
                promedio_margen = df['Margen Operativo'].mean()
                colores = ['green' if x > 0 else 'red' for x in df['Margen Operativo']]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df['Mes'], y=df['Margen Operativo'], marker_color=colores))
                fig.add_trace(go.Scatter(x=df['Mes'], y=[promedio_margen] * len(df), mode='lines', name='Promedio', line=dict(color='blue', width=2, dash='dash')))
                fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
                fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Margen Operativo ($)")
                st.plotly_chart(fig, use_container_width=True)
            
            with col_der:
                st.subheader("Márgenes Comparados")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Mes'], y=df['% Margen Bruto'], mode='lines+markers', name='% Margen Bruto'))
                fig.add_trace(go.Scatter(x=df['Mes'], y=df['% Margen Operativo'], mode='lines+markers', name='% Margen Operativo'))
                fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Porcentaje (%)", hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("Tabla de Datos Completa")
            df_display = df[['Mes', 'Ventas', 'Compras CF', 'Compras Exentas', 'Total Compras', 
                             'Margen Bruto', '% Margen Bruto', 'Sueldos y CS', 
                             'Margen Operativo', '% Margen Operativo', 'Ratio Ventas/Sueldos']].copy()
            
            for col in ['Ventas', 'Compras CF', 'Compras Exentas', 'Total Compras', 'Margen Bruto', 'Sueldos y CS', 'Margen Operativo']:
                df_display[col] = df_display[col].apply(lambda x: formatear_monto(x))
            
            df_display['% Margen Bruto'] = df['% Margen Bruto'].apply(lambda x: formatear_porcentaje(x))
            df_display['% Margen Operativo'] = df['% Margen Operativo'].apply(lambda x: formatear_porcentaje(x))
            df_display['Ratio Ventas/Sueldos'] = df['Ratio Ventas/Sueldos'].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Resumen ejecutivo
        st.markdown("---")
        st.header("📊 Resumen Ejecutivo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🎯 Ventas**")
            mejor_mes_ventas = df.loc[df['Ventas'].idxmax()]
            peor_mes_ventas = df.loc[df['Ventas'].idxmin()]
            st.write(f"✅ Mejor mes: **{mejor_mes_ventas['Mes']}**")
            st.write(f"   {formatear_monto(mejor_mes_ventas['Ventas'])}")
            st.write(f"⚠️ Menor mes: **{peor_mes_ventas['Mes']}**")
            st.write(f"   {formatear_monto(peor_mes_ventas['Ventas'])}")
        
        with col2:
            st.markdown("**💹 Rentabilidad**")
            mejor_margen = df.loc[df['Margen Operativo'].idxmax()]
            peor_margen = df.loc[df['Margen Operativo'].idxmin()]
            st.write(f"✅ Mejor margen: **{mejor_margen['Mes']}**")
            st.write(f"   {formatear_monto(mejor_margen['Margen Operativo'])}")
            st.write(f"⚠️ Menor margen: **{peor_margen['Mes']}**")
            st.write(f"   {formatear_monto(peor_margen['Margen Operativo'])}")
        
        with col3:
            st.markdown("**💡 Eficiencia**")
            mejor_ratio = df.loc[df['Ratio Ventas/Sueldos'].idxmax()]
            peor_ratio = df.loc[df['Ratio Ventas/Sueldos'].idxmin()]
            st.write(f"✅ Mejor ratio: **{mejor_ratio['Mes']}**")
            st.write(f"   {mejor_ratio['Ratio Ventas/Sueldos']:.2f}x")
            st.write(f"⚠️ Menor ratio: **{peor_ratio['Mes']}**")
            st.write(f"   {peor_ratio['Ratio Ventas/Sueldos']:.2f}x")

else:
    # No hay archivo para este cliente
    st.info("📁 Aún no hay datos disponibles")
    st.markdown("""
    ### Información
    
    Tu contador está preparando tus datos para visualización.
    
    Una vez que los datos estén disponibles, podrás ver:
    - 📊 Evolución de ventas
    - 🛒 Análisis de compras
    - 💹 Rentabilidad y márgenes
    - 📈 Indicadores de eficiencia
    
    Por favor, vuelve a consultar pronto.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Dashboard Contable Multi-Cliente | Acceso seguro y confidencial</div>",
    unsafe_allow_html=True
)
