import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Contable",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Directorios
BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / "datos"
CLIENTES_FILE = BASE_DIR / "clientes.json"

def cargar_clientes():
    if CLIENTES_FILE.exists():
        with open(CLIENTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clientes": {}, "admin": {"codigo": "admin2024", "nombre": "Administrador"}}

def procesar_excel(archivo):
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
    if pd.isna(valor):
        return "N/A"
    return f"${valor/1_000_000:,.1f}M"

def formatear_porcentaje(valor):
    if pd.isna(valor):
        return "N/A"
    return f"{valor:.1f}%"

def convertir_fecha_español(fecha_str):
    """Convierte formato YYYY-MM a Mes YYYY en español"""
    meses_es = {
        '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'
    }
    try:
        year, month = fecha_str.split('-')
        return f"{meses_es[month]} {year}"
    except:
        return fecha_str

def generar_alertas(df):
    alertas = []
    meses_negativos = df[df['Margen Operativo'] < 0]
    if len(meses_negativos) > 0:
        for idx, row in meses_negativos.iterrows():
            alertas.append({
                'tipo': 'warning',
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
    cliente_dir = DATOS_DIR / codigo_cliente
    if cliente_dir.exists():
        archivos = list(cliente_dir.glob("*.xlsx"))
        if archivos:
            return archivos[0]
    return None

def obtener_documentos_cliente(codigo_cliente):
    """Obtiene lista de PDFs disponibles para el cliente"""
    cliente_dir = DATOS_DIR / codigo_cliente / "documentos"
    documentos = []
    
    if cliente_dir.exists():
        # Buscar PDFs
        pdfs = list(cliente_dir.glob("*.pdf"))
        for pdf in pdfs:
            # Determinar tipo de documento
            nombre = pdf.stem.lower()
            if 'arca' in nombre or 'arba' in nombre:
                tipo = "Constancia ARCA"
                icono = "📄"
            elif 'pyme' in nombre:
                tipo = "Certificado PyME"
                icono = "🏭"
            elif 'reporte' in nombre or 'informe' in nombre:
                tipo = "Reporte Mensual"
                icono = "📊"
            else:
                tipo = "Documento"
                icono = "📎"
            
            documentos.append({
                'nombre': pdf.name,
                'tipo': tipo,
                'icono': icono,
                'ruta': pdf,
                'fecha': datetime.fromtimestamp(pdf.stat().st_mtime).strftime('%d/%m/%Y')
            })
    
    return sorted(documentos, key=lambda x: x['tipo'])

# Obtener parámetro de cliente
query_params = st.query_params
codigo_cliente = query_params.get("cliente", None)
config = cargar_clientes()

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

cliente = config['clientes'][codigo_cliente]

if not cliente['activo']:
    st.warning("⚠️ Cuenta inactiva")
    st.markdown("Tu cuenta está temporalmente inactiva. Contacta a tu contador.")
    st.stop()

# HEADER
st.title("📊 Dashboard Financiero")
st.subheader(f"**{cliente['nombre']}**")
st.divider()

# SIDEBAR
with st.sidebar:
    st.markdown("### 📑 Sección")
    
    # Navegación con iconos
    opciones = {
        "📊 Dashboard": "Dashboard",
        "📁 Documentos": "Documentos"
    }
    
    pagina_display = st.radio(
        "Selecciona una opción:",
        options=list(opciones.keys()),
        label_visibility="collapsed"
    )
    
    pagina = opciones[pagina_display]
    
    st.divider()
    st.markdown("### ℹ️ Información")
    st.markdown(f"""
**Cliente:** {cliente['nombre']}  
**Última actualización:** {datetime.now().strftime('%d/%m/%Y')}
    """)

# ============== PÁGINA: DOCUMENTOS ==============
if pagina == "Documentos":
    st.markdown("## 📁 Mis Documentos")
    st.markdown("Accedé y descargá tus documentos fiscales y reportes.")
    st.divider()
    
    documentos = obtener_documentos_cliente(codigo_cliente)
    
    if documentos:
        # Agrupar por tipo
        tipos = {}
        for doc in documentos:
            tipo = doc['tipo']
            if tipo not in tipos:
                tipos[tipo] = []
            tipos[tipo].append(doc)
        
        # Mostrar documentos agrupados
        for tipo, docs in tipos.items():
            with st.expander(f"{docs[0]['icono']} **{tipo}** ({len(docs)})", expanded=True):
                for doc in docs:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{doc['nombre']}**")
                    with col2:
                        st.caption(f"📅 {doc['fecha']}")
                    with col3:
                        # Leer el archivo para el botón de descarga
                        with open(doc['ruta'], 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar",
                                data=f.read(),
                                file_name=doc['nombre'],
                                mime="application/pdf",
                                key=doc['nombre']
                            )
                st.divider()
    else:
        st.info("📭 Aún no hay documentos disponibles")
        st.markdown("""
        ### Documentos que estarán disponibles:
        
        - 📄 **Constancia de ARCA/ARBA**
        - 🏭 **Certificado PyME**
        - 📊 **Reportes Mensuales**
        
        Tu contador subirá los documentos próximamente.
        """)
    
    # Botón para generar reporte (si hay datos)
    archivo_cliente = obtener_archivo_cliente(codigo_cliente)
    if archivo_cliente:
        st.divider()
        st.markdown("### 📊 Generar Reporte")
        st.markdown("Generá un reporte PDF con los datos del dashboard actual.")
        
        if st.button("🔄 Generar Reporte PDF", type="primary"):
            st.info("⏳ Generando reporte... Esta funcionalidad estará disponible próximamente.")
            # TODO: Implementar generación de PDF

# ============== PÁGINA: DASHBOARD ==============
else:
    archivo_cliente = obtener_archivo_cliente(codigo_cliente)
    
    if archivo_cliente:
        df_completo = procesar_excel(archivo_cliente)
        
        if df_completo is not None:
            # Convertir fechas al español
            df_completo['Mes'] = df_completo['Mes'].apply(convertir_fecha_español)
            
            # Filtros en sidebar
            with st.sidebar:
                st.divider()
                st.markdown("#### 📅 Filtrar Período")
                meses_disponibles = df_completo['Mes'].tolist()
                
                mes_desde = st.selectbox("Desde:", options=meses_disponibles, index=0)
                mes_hasta = st.selectbox("Hasta:", options=meses_disponibles, index=len(meses_disponibles)-1)
                
                idx_desde = meses_disponibles.index(mes_desde)
                idx_hasta = meses_disponibles.index(mes_hasta)
                
                if idx_desde > idx_hasta:
                    st.error("⚠️ 'Desde' debe ser anterior a 'Hasta'")
                    df = df_completo
                else:
                    df = df_completo.iloc[idx_desde:idx_hasta+1].copy()
                
                st.info(f"📊 Mostrando **{len(df)} meses**")
            
            # Alertas
            alertas = generar_alertas(df)
            if alertas:
                for alerta in alertas:
                    if alerta['tipo'] == 'warning':
                        st.warning(f"**{alerta['titulo']}**  \n{alerta['mensaje']}")
                    elif alerta['tipo'] == 'success':
                        st.success(f"**{alerta['titulo']}**  \n{alerta['mensaje']}")
            
            # KPIs
            st.markdown("### 📈 Indicadores Principales")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            ventas_total = df['Ventas'].sum()
            ventas_promedio = df['Ventas'].mean()
            compras_total = df['Total Compras'].sum()
            sueldos_total = df['Sueldos y CS'].sum()
            margen_bruto_total = df['Margen Bruto'].sum()
            margen_bruto_pct = (margen_bruto_total / ventas_total * 100)
            margen_operativo_total = df['Margen Operativo'].sum()
            margen_operativo_pct = (margen_operativo_total / ventas_total * 100)
            ratio_sueldos_ventas = (sueldos_total / ventas_total * 100)
            
            with col1:
                st.metric("Ventas Totales", formatear_monto(ventas_total), 
                         delta=f"Prom: {formatear_monto(ventas_promedio)}")
            with col2:
                st.metric("Compras Totales", formatear_monto(compras_total))
            with col3:
                st.metric("Margen Bruto", formatear_monto(margen_bruto_total),
                         delta=f"{margen_bruto_pct:.1f}%")
            with col4:
                color = "normal" if margen_operativo_total >= 0 else "inverse"
                st.metric("Margen Operativo", formatear_monto(margen_operativo_total),
                         delta=f"{margen_operativo_pct:.1f}%", delta_color=color)
            with col5:
                st.metric("Sueldos / Ventas", f"{ratio_sueldos_ventas:.1f}%")
            
            st.divider()
            
            # TABS
            tab1, tab2, tab3, tab4 = st.tabs(["💰 Ventas y Compras", "🧑‍💼 Sueldos", "💹 Rentabilidad", "📋 Resumen Ejecutivo"])
            
            with tab1:
                st.markdown("### Ventas y Compras")
                col_izq, col_der = st.columns(2)
                
                with col_izq:
                    st.markdown("#### Evolución de Ventas")
                    promedio_ventas = df['Ventas'].mean()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=df['Ventas'],
                        mode='lines+markers',
                        name='Ventas',
                        line=dict(color='#0066cc', width=3),
                        marker=dict(size=8)
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=[promedio_ventas]*len(df),
                        mode='lines',
                        name='Promedio',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    fig.update_layout(height=350, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_der:
                    st.markdown("#### Evolución de Compras")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=df['Compras CF'],
                        mode='lines+markers',
                        name='Compras CF',
                        line=dict(color='green', width=2),
                        stackgroup='one'
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=df['Compras Exentas'],
                        mode='lines+markers',
                        name='Compras Exentas',
                        line=dict(color='orange', width=2),
                        stackgroup='one'
                    ))
                    fig.update_layout(height=350, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.markdown("### Sueldos")
                
                st.markdown("#### Sueldos como % de Ventas")
                df['% Sueldos/Ventas'] = (df['Sueldos y CS'] / df['Ventas'] * 100).round(1)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['Mes'], y=df['% Sueldos/Ventas'],
                    marker_color='#3498db',
                    text=df['% Sueldos/Ventas'].apply(lambda x: f"{x:.1f}%"),
                    textposition='outside',
                    textfont=dict(size=12)
                ))
                fig.add_hline(y=df['% Sueldos/Ventas'].mean(), 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text="Promedio",
                            annotation_position="right")
                fig.update_layout(
                    height=400,
                    yaxis_title="Porcentaje (%)",
                    showlegend=False,
                    yaxis=dict(range=[0, df['% Sueldos/Ventas'].max() * 1.2])
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.markdown("### Rentabilidad")
                col_izq, col_der = st.columns(2)
                
                with col_izq:
                    st.markdown("#### Margen Operativo")
                    promedio_margen = df['Margen Operativo'].mean()
                    colores = ['green' if x > 0 else 'red' for x in df['Margen Operativo']]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df['Mes'], y=df['Margen Operativo'],
                        marker_color=colores,
                        name='Margen Operativo'
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=[promedio_margen]*len(df),
                        mode='lines',
                        name='Promedio',
                        line=dict(color='blue', width=2, dash='dash')
                    ))
                    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
                    fig.update_layout(height=350, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_der:
                    st.markdown("#### Evolución de Márgenes (%)")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=df['% Margen Bruto'],
                        mode='lines+markers',
                        name='% Margen Bruto',
                        line=dict(color='blue', width=2)
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['Mes'], y=df['% Margen Operativo'],
                        mode='lines+markers',
                        name='% Margen Operativo',
                        line=dict(color='green', width=2)
                    ))
                    fig.update_layout(height=350, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.markdown("### Resumen Ejecutivo")
                
                # Tabla de datos
                st.markdown("#### 📊 Datos Completos")
                
                # Calcular % Sueldos/Ventas si no existe
                if '% Sueldos/Ventas' not in df.columns:
                    df['% Sueldos/Ventas'] = (df['Sueldos y CS'] / df['Ventas'] * 100).round(1)
                
                # Seleccionar columnas en el orden correcto
                df_display = df[['Mes', 'Ventas', 'Compras CF', 'Compras Exentas', 'Sueldos y CS',
                                 'Margen Operativo', '% Margen Operativo', '% Sueldos/Ventas']].copy()
                
                # Guardar valores numéricos para usar en iconos
                valores_margen_op = df_display['% Margen Operativo'].copy()
                valores_sueldos = df_display['% Sueldos/Ventas'].copy()
                
                # Formatear columnas de montos
                for col in ['Ventas', 'Compras CF', 'Compras Exentas', 'Sueldos y CS', 'Margen Operativo']:
                    df_display[col] = df_display[col].apply(formatear_monto)
                
                # Formatear % Margen Operativo con iconos
                def formato_margen_icono(val):
                    if pd.isna(val):
                        return "N/A"
                    if val >= 20:
                        return f"🟢 {val:.1f}%"
                    elif val >= 10:
                        return f"🔵 {val:.1f}%"
                    elif val >= 0:
                        return f"🟡 {val:.1f}%"
                    else:
                        return f"🔴 {val:.1f}%"
                
                # Formatear % Sueldos/Ventas con iconos
                def formato_sueldos_icono(val):
                    if pd.isna(val):
                        return "N/A"
                    if val <= 10:
                        return f"🟢 {val:.1f}%"
                    elif val <= 15:
                        return f"🔵 {val:.1f}%"
                    elif val <= 20:
                        return f"🟡 {val:.1f}%"
                    else:
                        return f"🔴 {val:.1f}%"
                
                df_display['% Margen Operativo'] = valores_margen_op.apply(formato_margen_icono)
                df_display['% Sueldos/Ventas'] = valores_sueldos.apply(formato_sueldos_icono)
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Leyenda de colores
                st.markdown("""
                **Leyenda:**  
                🟢 Excelente • 🔵 Bueno • 🟡 Aceptable • 🔴 Requiere atención
                """)
                
                # Resumen de mejores y peores meses
                st.divider()
                st.markdown("#### 📈 Análisis de Períodos")
                
                col1, col2, col3 = st.columns(3)
                
                mejor_mes_ventas = df.loc[df['Ventas'].idxmax()]
                peor_mes_ventas = df.loc[df['Ventas'].idxmin()]
                mejor_margen = df.loc[df['Margen Operativo'].idxmax()]
                peor_margen = df.loc[df['Margen Operativo'].idxmin()]
                mejor_sueldo_eficiencia = df.loc[df['% Sueldos/Ventas'].idxmin()]
                peor_sueldo_eficiencia = df.loc[df['% Sueldos/Ventas'].idxmax()]
                
                with col1:
                    st.markdown("##### 🎯 Ventas")
                    st.success(f"**✅ Mejor:** {mejor_mes_ventas['Mes']}  \n{formatear_monto(mejor_mes_ventas['Ventas'])}")
                    st.warning(f"**⚠️ Menor:** {peor_mes_ventas['Mes']}  \n{formatear_monto(peor_mes_ventas['Ventas'])}")
                
                with col2:
                    st.markdown("##### 💹 Rentabilidad")
                    st.success(f"**✅ Mejor:** {mejor_margen['Mes']}  \n{formatear_monto(mejor_margen['Margen Operativo'])}")
                    st.warning(f"**⚠️ Menor:** {peor_margen['Mes']}  \n{formatear_monto(peor_margen['Margen Operativo'])}")
                
                with col3:
                    st.markdown("##### 💡 Eficiencia Sueldos")
                    st.success(f"**✅ Más eficiente:** {mejor_sueldo_eficiencia['Mes']}  \n{mejor_sueldo_eficiencia['% Sueldos/Ventas']:.1f}%")
                    st.warning(f"**⚠️ Menos eficiente:** {peor_sueldo_eficiencia['Mes']}  \n{peor_sueldo_eficiencia['% Sueldos/Ventas']:.1f}%")
    
    else:
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
st.divider()
st.caption("Dashboard Contable Profesional • Gestión Financiera Empresarial")
