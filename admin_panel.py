import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from pathlib import Path
from datetime import datetime
import shutil

# Configuración de la página
st.set_page_config(
    page_title="Panel Admin - Dashboard Contable",
    page_icon="👨‍💼",
    layout="wide"
)

# Directorios
BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / "datos"
CLIENTES_FILE = BASE_DIR / "clientes.json"

# Crear directorios si no existen
DATOS_DIR.mkdir(exist_ok=True)

# Funciones auxiliares
def cargar_clientes():
    """Carga la configuración de clientes"""
    if CLIENTES_FILE.exists():
        with open(CLIENTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clientes": {}, "admin": {"codigo": "admin2024", "nombre": "Administrador"}}

def guardar_clientes(config):
    """Guarda la configuración de clientes"""
    with open(CLIENTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def procesar_excel(archivo):
    """Procesa el archivo Excel"""
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
        
        return df_limpio
    except Exception as e:
        return None

def formatear_monto(valor):
    """Formatea valores en millones"""
    if pd.isna(valor):
        return "N/A"
    return f"${valor/1_000_000:,.1f}M"

def obtener_datos_cliente(codigo):
    """Obtiene los datos procesados de un cliente"""
    cliente_dir = DATOS_DIR / codigo
    if cliente_dir.exists():
        archivos = list(cliente_dir.glob("*.xlsx"))
        if archivos:
            return procesar_excel(archivos[0])
    return None

# CSS personalizado
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(90deg, #d62728 0%, #ff7f0e 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .cliente-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .link-box {
        background: #e8f4f8;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Verificar acceso admin
query_params = st.query_params
codigo_admin = query_params.get("admin", None)

config = cargar_clientes()

if codigo_admin != config['admin']['codigo']:
    st.error("❌ Acceso denegado")
    st.markdown("### 🔒 Panel de Administración")
    st.markdown("Este es el panel de administración. Se requiere código de acceso válido.")
    st.stop()

# Header
st.markdown(f"""
<div class="admin-header">
    <h1>👨‍💼 Panel de Administración</h1>
    <p>Gestión de clientes y datos</p>
</div>
""", unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📋 Clientes", "📤 Subir Datos", "📊 Benchmarking", "➕ Nuevo Cliente"])

# TAB 1: Lista de clientes
with tab1:
    st.header("📋 Clientes Activos")
    
    if not config['clientes']:
        st.info("No hay clientes registrados. Usa la pestaña 'Nuevo Cliente' para agregar uno.")
    else:
        for codigo, cliente in config['clientes'].items():
            with st.expander(f"{'✅' if cliente['activo'] else '❌'} {cliente['nombre']} ({codigo})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **Código:** `{codigo}`  
                    **Estado:** {'✅ Activo' if cliente['activo'] else '❌ Inactivo'}  
                    **Fecha de alta:** {cliente.get('fecha_alta', 'N/A')}
                    """)
                    
                    # Mostrar link de acceso
                    url_base = "http://localhost:8501"  # Cambiar en producción
                    link_cliente = f"{url_base}/?cliente={codigo}"
                    
                    st.markdown("**🔗 Link de acceso del cliente:**")
                    st.code(link_cliente, language=None)
                    
                    # Verificar si tiene datos
                    cliente_dir = DATOS_DIR / codigo
                    if cliente_dir.exists():
                        archivos = list(cliente_dir.glob("*.xlsx"))
                        if archivos:
                            st.success(f"✅ Datos cargados: {archivos[0].name}")
                        else:
                            st.warning("⚠️ Sin datos cargados")
                    else:
                        st.warning("⚠️ Sin datos cargados")
                
                with col2:
                    # Botones de acción
                    if st.button(f"🔄 {'Desactivar' if cliente['activo'] else 'Activar'}", key=f"toggle_{codigo}"):
                        config['clientes'][codigo]['activo'] = not cliente['activo']
                        guardar_clientes(config)
                        st.rerun()
                    
                    if st.button(f"🗑️ Eliminar", key=f"del_{codigo}"):
                        if st.session_state.get(f'confirm_del_{codigo}', False):
                            # Eliminar cliente y sus datos
                            del config['clientes'][codigo]
                            guardar_clientes(config)
                            cliente_dir = DATOS_DIR / codigo
                            if cliente_dir.exists():
                                shutil.rmtree(cliente_dir)
                            st.success("Cliente eliminado")
                            st.rerun()
                        else:
                            st.session_state[f'confirm_del_{codigo}'] = True
                            st.warning("⚠️ Presiona de nuevo para confirmar")

# TAB 2: Subir datos
with tab2:
    st.header("📤 Subir Datos de Cliente")
    
    if not config['clientes']:
        st.info("No hay clientes registrados. Primero debes crear un cliente.")
    else:
        cliente_seleccionado = st.selectbox(
            "Selecciona el cliente:",
            options=list(config['clientes'].keys()),
            format_func=lambda x: f"{config['clientes'][x]['nombre']} ({x})"
        )
        
        archivo_subido = st.file_uploader(
            "Sube el archivo Excel del cliente",
            type=['xlsx', 'xls'],
            help="Archivo con formato estándar de ventas, compras, sueldos"
        )
        
        if archivo_subido:
            # Preview de datos
            st.subheader("Vista Previa")
            df_preview = procesar_excel(archivo_subido)
            
            if df_preview is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Meses de datos", len(df_preview))
                with col2:
                    ventas_total = df_preview['Ventas'].sum()
                    st.metric("Ventas totales", formatear_monto(ventas_total))
                with col3:
                    margen_total = df_preview['Margen Operativo'].sum()
                    st.metric("Margen operativo", formatear_monto(margen_total))
                
                st.dataframe(df_preview.head(), use_container_width=True)
                
                if st.button("✅ Confirmar y Guardar"):
                    # Crear directorio del cliente
                    cliente_dir = DATOS_DIR / cliente_seleccionado
                    cliente_dir.mkdir(exist_ok=True)
                    
                    # Guardar archivo
                    archivo_path = cliente_dir / f"datos_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    
                    # Eliminar archivos anteriores
                    for old_file in cliente_dir.glob("*.xlsx"):
                        old_file.unlink()
                    
                    # Guardar nuevo archivo
                    with open(archivo_path, 'wb') as f:
                        f.write(archivo_subido.getvalue())
                    
                    st.success(f"✅ Datos guardados exitosamente para {config['clientes'][cliente_seleccionado]['nombre']}")
                    st.balloons()
            else:
                st.error("❌ Error al procesar el archivo. Verifica el formato.")

# TAB 3: Benchmarking
with tab3:
    st.header("📊 Benchmarking Anónimo")
    st.markdown("Comparación entre clientes (datos anónimos)")
    
    # Recopilar datos de todos los clientes
    datos_clientes = {}
    for codigo, cliente in config['clientes'].items():
        if cliente['activo']:
            df = obtener_datos_cliente(codigo)
            if df is not None:
                datos_clientes[codigo] = {
                    'nombre': cliente['nombre'],
                    'df': df
                }
    
    if len(datos_clientes) < 2:
        st.info("Se necesitan al menos 2 clientes con datos para realizar benchmarking.")
    else:
        st.subheader("Comparación de Métricas Clave")
        
        # Calcular métricas de cada cliente
        metricas = []
        for codigo, datos in datos_clientes.items():
            df = datos['df']
            metricas.append({
                'Cliente': f"Cliente {chr(65 + len(metricas))}",  # A, B, C...
                'Ventas Promedio': df['Ventas'].mean(),
                '% Margen Bruto Prom': df['% Margen Bruto'].mean(),
                '% Margen Operativo Prom': df['% Margen Operativo'].mean(),
                'Ratio Ventas/Sueldos': (df['Ventas'] / df['Sueldos y CS']).mean()
            })
        
        df_benchmark = pd.DataFrame(metricas)
        
        # Gráficos comparativos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Ventas Promedio Mensuales**")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_benchmark['Cliente'],
                y=df_benchmark['Ventas Promedio'],
                marker_color='#1f77b4'
            ))
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**% Margen Operativo Promedio**")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_benchmark['Cliente'],
                y=df_benchmark['% Margen Operativo Prom'],
                marker_color='#2ca02c'
            ))
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla comparativa
        st.subheader("Tabla Comparativa")
        df_display = df_benchmark.copy()
        df_display['Ventas Promedio'] = df_display['Ventas Promedio'].apply(lambda x: formatear_monto(x))
        df_display['% Margen Bruto Prom'] = df_display['% Margen Bruto Prom'].apply(lambda x: f"{x:.1f}%")
        df_display['% Margen Operativo Prom'] = df_display['% Margen Operativo Prom'].apply(lambda x: f"{x:.1f}%")
        df_display['Ratio Ventas/Sueldos'] = df_display['Ratio Ventas/Sueldos'].apply(lambda x: f"{x:.2f}x")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.info("💡 Los clientes se muestran de forma anónima para proteger la confidencialidad.")

# TAB 4: Nuevo cliente
with tab4:
    st.header("➕ Crear Nuevo Cliente")
    
    with st.form("nuevo_cliente"):
        nombre_cliente = st.text_input("Nombre de la empresa:", placeholder="Ej: Empresa ABC S.A.")
        codigo_cliente = st.text_input(
            "Código de cliente:",
            placeholder="Ej: empresa_abc",
            help="Sin espacios, solo letras minúsculas y guiones bajos"
        )
        
        submitted = st.form_submit_button("✅ Crear Cliente")
        
        if submitted:
            if not nombre_cliente or not codigo_cliente:
                st.error("❌ Todos los campos son obligatorios")
            elif codigo_cliente in config['clientes']:
                st.error("❌ Ese código de cliente ya existe")
            elif ' ' in codigo_cliente or not codigo_cliente.islower():
                st.error("❌ El código debe ser en minúsculas sin espacios")
            else:
                # Crear nuevo cliente
                config['clientes'][codigo_cliente] = {
                    'nombre': nombre_cliente,
                    'codigo': codigo_cliente,
                    'activo': True,
                    'fecha_alta': datetime.now().strftime('%Y-%m-%d')
                }
                guardar_clientes(config)
                
                # Crear directorio
                cliente_dir = DATOS_DIR / codigo_cliente
                cliente_dir.mkdir(exist_ok=True)
                
                st.success(f"✅ Cliente '{nombre_cliente}' creado exitosamente")
                st.balloons()
                
                # Mostrar link
                url_base = "http://localhost:8501"
                link_cliente = f"{url_base}/?cliente={codigo_cliente}"
                st.markdown("**🔗 Link de acceso del cliente:**")
                st.code(link_cliente, language=None)
                st.info("⚠️ Guarda este link para enviárselo al cliente")

# Sidebar con info
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown(f"""
    **Total de clientes:** {len(config['clientes'])}  
    **Activos:** {sum(1 for c in config['clientes'].values() if c['activo'])}  
    **Inactivos:** {sum(1 for c in config['clientes'].values() if not c['activo'])}
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Link Admin")
    st.code(f"?admin={config['admin']['codigo']}", language=None)
    
    st.markdown("---")
    st.info("💡 Usa este panel para gestionar clientes, subir datos y realizar análisis comparativos.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Panel de Administración | Dashboard Contable Multi-Cliente</div>",
    unsafe_allow_html=True
)
