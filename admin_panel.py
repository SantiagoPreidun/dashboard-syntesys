import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
import shutil

# Configuración
st.set_page_config(page_title="Panel Administrativo", page_icon="⚙️", layout="wide")

BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / "datos"
CLIENTES_FILE = BASE_DIR / "clientes.json"

def cargar_clientes():
    if CLIENTES_FILE.exists():
        with open(CLIENTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clientes": {}, "admin": {"codigo": "admin2024", "nombre": "Administrador"}}

def guardar_clientes(config):
    with open(CLIENTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

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
        
        ventas = df.iloc[3, 2:2+len(fechas)].values
        margen_operativo = df.iloc[7, 2:2+len(fechas)].values
        
        ventas_total = sum([v for v in ventas if pd.notna(v)])
        margen_total = sum([m for m in margen_operativo if pd.notna(m)])
        
        return {
            'meses': len(fechas),
            'ventas_total': ventas_total,
            'margen_operativo': margen_total
        }
    except Exception as e:
        return None

# Validar acceso
query_params = st.query_params
codigo_admin = query_params.get("admin", None)
config = cargar_clientes()

if not codigo_admin or codigo_admin != config['admin']['codigo']:
    st.error("❌ Acceso no autorizado")
    st.markdown("### 🔒 Panel Administrativo")
    st.markdown("Este panel es de acceso exclusivo para administradores.")
    st.stop()

# HEADER
st.title("⚙️ Panel de Administración")
st.markdown("**Gestión de Clientes y Documentos**")
st.divider()

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Clientes", "📊 Subir Datos", "📁 Subir Documentos", "📈 Benchmarking", "➕ Nuevo Cliente"])

# ============== TAB 1: CLIENTES ==============
with tab1:
    st.markdown("### Lista de Clientes")
    
    if config['clientes']:
        for codigo, cliente in config['clientes'].items():
            with st.expander(f"{'🟢' if cliente['activo'] else '🔴'} **{cliente['nombre']}** ({codigo})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **Código:** `{codigo}`  
                    **Fecha alta:** {cliente.get('fecha_alta', 'N/A')}  
                    **Estado:** {'✅ Activo' if cliente['activo'] else '❌ Inactivo'}
                    """)
                    
                    # Link de acceso
                    url_base = "http://localhost:8501"
                    link_cliente = f"{url_base}?cliente={codigo}"
                    st.code(link_cliente, language=None)
                    
                    # Verificar datos
                    cliente_dir = DATOS_DIR / codigo
                    tiene_datos = False
                    tiene_documentos = False
                    
                    if cliente_dir.exists():
                        archivos_xlsx = list(cliente_dir.glob("*.xlsx"))
                        tiene_datos = len(archivos_xlsx) > 0
                        
                        doc_dir = cliente_dir / "documentos"
                        if doc_dir.exists():
                            archivos_pdf = list(doc_dir.glob("*.pdf"))
                            tiene_documentos = len(archivos_pdf) > 0
                    
                    if tiene_datos:
                        st.success("📊 Datos cargados")
                    else:
                        st.warning("📊 Sin datos")
                    
                    if tiene_documentos:
                        st.success("📁 Documentos cargados")
                    else:
                        st.info("📁 Sin documentos")
                
                with col2:
                    if cliente['activo']:
                        if st.button("🔴 Desactivar", key=f"desactivar_{codigo}"):
                            config['clientes'][codigo]['activo'] = False
                            guardar_clientes(config)
                            st.rerun()
                    else:
                        if st.button("🟢 Activar", key=f"activar_{codigo}"):
                            config['clientes'][codigo]['activo'] = True
                            guardar_clientes(config)
                            st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"eliminar_{codigo}", type="secondary"):
                        if st.session_state.get(f'confirmar_eliminar_{codigo}', False):
                            cliente_dir = DATOS_DIR / codigo
                            if cliente_dir.exists():
                                shutil.rmtree(cliente_dir)
                            del config['clientes'][codigo]
                            guardar_clientes(config)
                            st.success(f"Cliente {cliente['nombre']} eliminado")
                            st.rerun()
                        else:
                            st.session_state[f'confirmar_eliminar_{codigo}'] = True
                            st.warning("⚠️ Click de nuevo para confirmar")
    else:
        st.info("No hay clientes registrados. Creá uno en la pestaña 'Nuevo Cliente'.")

# ============== TAB 2: SUBIR DATOS ==============
with tab2:
    st.markdown("### 📊 Subir Datos del Cliente")
    
    if config['clientes']:
        clientes_lista = [(codigo, cliente['nombre']) for codigo, cliente in config['clientes'].items()]
        cliente_seleccionado = st.selectbox(
            "Seleccionar cliente:",
            options=clientes_lista,
            format_func=lambda x: f"{x[1]} ({x[0]})"
        )
        
        if cliente_seleccionado:
            codigo_sel = cliente_seleccionado[0]
            
            st.divider()
            archivo_subido = st.file_uploader("Subir archivo Excel", type=['xlsx'], key="datos_excel")
            
            if archivo_subido:
                st.markdown("#### 👀 Preview de Datos")
                
                info = procesar_excel(archivo_subido)
                
                if info:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Meses", info['meses'])
                    col2.metric("Ventas Totales", f"${info['ventas_total']/1_000_000:,.1f}M")
                    col3.metric("Margen Operativo", f"${info['margen_operativo']/1_000_000:,.1f}M")
                    
                    st.divider()
                    
                    if st.button("✅ Confirmar y Guardar", type="primary"):
                        cliente_dir = DATOS_DIR / codigo_sel
                        cliente_dir.mkdir(parents=True, exist_ok=True)
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        nombre_archivo = f"datos_{timestamp}.xlsx"
                        ruta_destino = cliente_dir / nombre_archivo
                        
                        with open(ruta_destino, 'wb') as f:
                            f.write(archivo_subido.getbuffer())
                        
                        st.success(f"✅ Datos guardados exitosamente para {cliente_seleccionado[1]}")
                else:
                    st.error("❌ Error al procesar el archivo. Verificá el formato.")
    else:
        st.warning("No hay clientes registrados. Creá uno primero.")

# ============== TAB 3: SUBIR DOCUMENTOS ==============
with tab3:
    st.markdown("### 📁 Subir Documentos PDF")
    st.markdown("Subí constancias de ARCA, certificados PyME y otros documentos para tus clientes.")
    
    if config['clientes']:
        clientes_lista = [(codigo, cliente['nombre']) for codigo, cliente in config['clientes'].items()]
        cliente_doc = st.selectbox(
            "Seleccionar cliente:",
            options=clientes_lista,
            format_func=lambda x: f"{x[1]} ({x[0]})",
            key="doc_cliente"
        )
        
        if cliente_doc:
            codigo_doc = cliente_doc[0]
            
            st.divider()
            
            # Selector de tipo de documento
            tipo_doc = st.selectbox(
                "Tipo de documento:",
                ["Constancia ARCA", "Certificado PyME", "Reporte Mensual", "Otro"]
            )
            
            # Campo para nombre personalizado
            if tipo_doc == "Otro":
                nombre_custom = st.text_input("Nombre del documento:", placeholder="Ej: Comprobante IVA Enero")
            
            # Subir archivo
            pdf_subido = st.file_uploader("Subir PDF", type=['pdf'], key="doc_pdf")
            
            if pdf_subido:
                st.info(f"📄 Archivo: **{pdf_subido.name}** ({pdf_subido.size/1024:.1f} KB)")
                
                if st.button("✅ Guardar Documento", type="primary"):
                    # Crear directorio de documentos
                    doc_dir = DATOS_DIR / codigo_doc / "documentos"
                    doc_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generar nombre del archivo
                    if tipo_doc == "Otro" and nombre_custom:
                        nombre_archivo = f"{nombre_custom}.pdf"
                    elif tipo_doc == "Constancia ARCA":
                        nombre_archivo = f"constancia_arca_{datetime.now().strftime('%Y%m')}.pdf"
                    elif tipo_doc == "Certificado PyME":
                        nombre_archivo = f"certificado_pyme_{datetime.now().strftime('%Y')}.pdf"
                    elif tipo_doc == "Reporte Mensual":
                        nombre_archivo = f"reporte_{datetime.now().strftime('%Y%m')}.pdf"
                    else:
                        nombre_archivo = pdf_subido.name
                    
                    # Guardar archivo
                    ruta_destino = doc_dir / nombre_archivo
                    with open(ruta_destino, 'wb') as f:
                        f.write(pdf_subido.getbuffer())
                    
                    st.success(f"✅ Documento guardado: {nombre_archivo}")
                    st.balloons()
            
            # Mostrar documentos existentes
            st.divider()
            st.markdown("#### 📋 Documentos Existentes")
            
            doc_dir = DATOS_DIR / codigo_doc / "documentos"
            if doc_dir.exists():
                pdfs = list(doc_dir.glob("*.pdf"))
                if pdfs:
                    for pdf in pdfs:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.markdown(f"📄 **{pdf.name}**")
                        with col2:
                            fecha = datetime.fromtimestamp(pdf.stat().st_mtime).strftime('%d/%m/%Y %H:%M')
                            st.caption(f"📅 {fecha}")
                        with col3:
                            if st.button("🗑️", key=f"del_{pdf.name}"):
                                pdf.unlink()
                                st.rerun()
                else:
                    st.info("No hay documentos guardados para este cliente")
            else:
                st.info("No hay documentos guardados para este cliente")
    else:
        st.warning("No hay clientes registrados. Creá uno primero.")

# ============== TAB 4: BENCHMARKING ==============
with tab4:
    st.markdown("### 📈 Benchmarking entre Clientes")
    st.markdown("Comparación anónima de indicadores financieros.")
    
    if len(config['clientes']) >= 2:
        datos_clientes = []
        
        for codigo, cliente in config['clientes'].items():
            if not cliente['activo']:
                continue
                
            cliente_dir = DATOS_DIR / codigo
            if cliente_dir.exists():
                archivos = list(cliente_dir.glob("*.xlsx"))
                if archivos:
                    info = procesar_excel(archivos[0])
                    if info:
                        datos_clientes.append({
                            'nombre_anonimo': f"Cliente {chr(65 + len(datos_clientes))}",
                            'ventas': info['ventas_total'],
                            'margen': info['margen_operativo'],
                            'margen_pct': (info['margen_operativo'] / info['ventas_total'] * 100) if info['ventas_total'] > 0 else 0
                        })
        
        if len(datos_clientes) >= 2:
            df_bench = pd.DataFrame(datos_clientes)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Ventas Promedio")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_bench['nombre_anonimo'],
                    y=df_bench['ventas']/1_000_000,
                    marker_color='lightblue'
                ))
                fig.update_layout(
                    yaxis_title="Millones ($)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### % Margen Operativo")
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_bench['nombre_anonimo'],
                    y=df_bench['margen_pct'],
                    marker_color='lightgreen'
                ))
                fig.update_layout(
                    yaxis_title="Porcentaje (%)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.markdown("#### Tabla Comparativa")
            df_display = df_bench.copy()
            df_display['ventas'] = df_display['ventas'].apply(lambda x: f"${x/1_000_000:,.1f}M")
            df_display['margen'] = df_display['margen'].apply(lambda x: f"${x/1_000_000:,.1f}M")
            df_display['margen_pct'] = df_display['margen_pct'].apply(lambda x: f"{x:.1f}%")
            df_display.columns = ['Cliente', 'Ventas Totales', 'Margen Operativo', '% Margen']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("Se necesitan al menos 2 clientes con datos para comparar")
    else:
        st.info("Se necesitan al menos 2 clientes registrados para benchmarking")

# ============== TAB 5: NUEVO CLIENTE ==============
with tab5:
    st.markdown("### ➕ Crear Nuevo Cliente")
    
    with st.form("nuevo_cliente"):
        nombre = st.text_input("Nombre del Cliente:", placeholder="Ej: Supply Petrolero SRL")
        codigo = st.text_input("Código único:", placeholder="Ej: supply_petrolero")
        
        st.markdown("*El código debe ser único, sin espacios, en minúsculas*")
        
        submitted = st.form_submit_button("✅ Crear Cliente", type="primary")
        
        if submitted:
            if not nombre or not codigo:
                st.error("❌ Completá todos los campos")
            elif codigo in config['clientes']:
                st.error(f"❌ El código '{codigo}' ya existe")
            elif ' ' in codigo or not codigo.islower():
                st.error("❌ El código debe ser en minúsculas y sin espacios")
            else:
                config['clientes'][codigo] = {
                    "nombre": nombre,
                    "codigo": codigo,
                    "activo": True,
                    "fecha_alta": datetime.now().strftime('%Y-%m-%d')
                }
                guardar_clientes(config)
                
                cliente_dir = DATOS_DIR / codigo
                cliente_dir.mkdir(parents=True, exist_ok=True)
                
                doc_dir = cliente_dir / "documentos"
                doc_dir.mkdir(parents=True, exist_ok=True)
                
                url_base = "http://localhost:8501"
                link_cliente = f"{url_base}?cliente={codigo}"
                
                st.success(f"✅ Cliente **{nombre}** creado exitosamente")
                st.balloons()
                st.markdown("#### 🔗 Link de Acceso:")
                st.code(link_cliente, language=None)
                st.markdown("*Compartí este link con tu cliente*")

# Footer
st.divider()
st.caption("Panel de Administración • Dashboard Contable")
