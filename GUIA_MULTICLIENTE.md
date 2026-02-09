# 📊 Dashboard Multi-Cliente - Guía Completa

## 🎯 ¿Qué construimos?

Un sistema completo de dashboards con:
- ✅ **Acceso por cliente** mediante links únicos (sin contraseñas)
- ✅ **Panel de administración** para gestionar todo
- ✅ **Benchmarking anónimo** entre clientes
- ✅ **Listo para publicar online** gratis en Streamlit Cloud

---

## 📁 Archivos del Sistema

```
MisDashboards/
├── dashboard_multicliente.py    # Dashboard principal (clientes)
├── admin_panel.py                # Panel de administración (vos)
├── clientes.json                 # Base de datos de clientes
├── requirements.txt              # Librerías necesarias
└── datos/                        # Carpeta de datos
    ├── cliente_a/
    │   └── datos_20250209.xlsx
    ├── cliente_b/
    │   └── datos_20250209.xlsx
    └── ...
```

---

## 🚀 Instalación y Configuración Inicial

### Paso 1: Preparar el entorno

1. Crea la carpeta principal:
```bash
mkdir C:\MisDashboards
cd C:\MisDashboards
```

2. Copia los archivos que te pasé:
   - `dashboard_multicliente.py`
   - `admin_panel.py`
   - `clientes.json`
   - `requirements.txt`

3. Instala las librerías (si aún no lo hiciste):
```bash
python -m pip install -r requirements.txt
```

### Paso 2: Crear la estructura de datos

El sistema crea automáticamente la carpeta `datos/` cuando ejecutas el admin panel.

---

## 👨‍💼 Uso del Panel de Administración

### Ejecutar el Panel Admin

```bash
cd C:\MisDashboards
python -m streamlit run admin_panel.py
```

Se abre en: `http://localhost:8501`

**Para acceder:** Agrega al final de la URL: `?admin=admin2024`

Ejemplo completo: `http://localhost:8501?admin=admin2024`

### ¿Qué puedes hacer en el Panel Admin?

#### 1️⃣ **Tab "Clientes"**
- Ver lista de todos los clientes
- Ver el link de acceso de cada cliente
- Activar/desactivar clientes
- Eliminar clientes
- Ver estado de datos (si tienen archivo cargado)

#### 2️⃣ **Tab "Subir Datos"**
- Seleccionar un cliente
- Subir su archivo Excel
- Ver preview de los datos
- Guardar en la carpeta del cliente

#### 3️⃣ **Tab "Benchmarking"**
- Ver comparación anónima entre clientes
- Gráficos de ventas promedio
- Comparación de márgenes
- Tabla comparativa de todas las métricas
- Los clientes aparecen como "Cliente A", "Cliente B", etc.

#### 4️⃣ **Tab "Nuevo Cliente"**
- Crear un nuevo cliente
- Ingresar nombre de empresa
- Definir código único
- Obtener link de acceso automáticamente

---

## 👤 Acceso de Clientes

### ¿Cómo accede un cliente?

Cada cliente recibe un link único tipo:
```
http://localhost:8501?cliente=codigo_cliente
```

Por ejemplo:
- Cliente "Empresa A": `http://localhost:8501?cliente=demo_empresa_a`
- Cliente "Empresa B": `http://localhost:8501?cliente=demo_empresa_b`

### ¿Qué ve el cliente?

1. **Header personalizado** con su nombre de empresa
2. **Todas las visualizaciones** del dashboard PRO:
   - Métricas principales
   - Gráficos de ventas
   - Análisis de compras
   - Rentabilidad
   - Tablas de datos
3. **Filtros de fecha** para seleccionar períodos
4. **Alertas automáticas** si hay problemas
5. **Resumen ejecutivo**

### Seguridad

- Cada cliente solo ve SUS datos
- No puede acceder a datos de otros clientes
- No puede ver el panel admin
- No necesita contraseña (solo conocer su link)

---

## 📤 Flujo de Trabajo Típico

### Escenario 1: Agregar un nuevo cliente

1. Abrir panel admin (`?admin=admin2024`)
2. Tab "Nuevo Cliente"
3. Ingresar datos:
   - Nombre: "Transportes López S.A."
   - Código: "transportes_lopez"
4. Click en "Crear Cliente"
5. Copiar el link generado
6. Enviárselo al cliente por email

### Escenario 2: Actualizar datos de un cliente

1. Abrir panel admin
2. Tab "Subir Datos"
3. Seleccionar cliente de la lista
4. Subir nuevo archivo Excel
5. Revisar preview
6. Click en "Confirmar y Guardar"
7. El cliente verá los nuevos datos automáticamente

### Escenario 3: Comparar performance de clientes

1. Abrir panel admin
2. Tab "Benchmarking"
3. Ver gráficos comparativos
4. Analizar qué clientes tienen mejor performance
5. Identificar oportunidades de mejora

---

## 🌐 Publicar Online en Streamlit Cloud (GRATIS)

### Requisitos previos

1. Cuenta en GitHub (gratis)
2. Cuenta en Streamlit Cloud (gratis)

### Paso 1: Crear repositorio en GitHub

1. Ve a https://github.com
2. Click en "New repository"
3. Nombre: `dashboard-contable` (o el que quieras)
4. Público o Privado (recomiendo privado por seguridad)
5. Click en "Create repository"

### Paso 2: Subir archivos a GitHub

Desde tu computadora, en la carpeta del proyecto:

```bash
cd C:\MisDashboards

# Inicializar git
git init

# Agregar todos los archivos
git add dashboard_multicliente.py
git add admin_panel.py
git add clientes.json
git add requirements.txt

# Commit
git commit -m "Primer commit - Dashboard multi-cliente"

# Conectar con GitHub (reemplaza TU_USUARIO y TU_REPO)
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Subir
git push -u origin main
```

**Alternativa SIN terminal:**
1. Descarga GitHub Desktop: https://desktop.github.com/
2. Arrastra los archivos a un nuevo repo
3. Click en "Publish repository"

### Paso 3: Desplegar en Streamlit Cloud

1. Ve a https://streamlit.io/cloud
2. Sign in con tu cuenta de GitHub
3. Click en "New app"
4. Configuración:
   - **Repository:** Selecciona tu repo
   - **Branch:** main
   - **Main file path:** `dashboard_multicliente.py` o `admin_panel.py`
   - **App URL:** Elige tu subdominio (ej: `santi-contable`)
5. Click en "Deploy"

¡Listo! Tu app estará en: `https://santi-contable.streamlit.app`

### Crear dos apps separadas

Puedes crear:
1. **App para clientes:** usando `dashboard_multicliente.py`
   - URL: `https://santi-contable.streamlit.app`
2. **App para admin:** usando `admin_panel.py`
   - URL: `https://santi-contable-admin.streamlit.app`

### ⚠️ Importante para producción

**Cambiar URLs en el código:**

En `admin_panel.py`, línea ~150:
```python
url_base = "http://localhost:8501"  # CAMBIAR ESTO
```

Por:
```python
url_base = "https://santi-contable.streamlit.app"  # Tu URL real
```

---

## 🔐 Seguridad en Producción

### Cambiar código de admin

En `clientes.json`, cambia:
```json
"admin": {
  "codigo": "admin2024",  ← Cambia esto por algo seguro
  "nombre": "Administrador"
}
```

Por ejemplo:
```json
"admin": {
  "codigo": "MiC0d1g0S3gur0X7",
  "nombre": "Administrador"
}
```

### Proteger datos sensibles

- Mantén el repositorio de GitHub como **privado**
- No compartas el código admin públicamente
- Cambia códigos de cliente si se filtran

---

## 📊 Gestión de Datos en Producción

### ¿Dónde se guardan los datos en Streamlit Cloud?

Los datos se guardan en el servidor de Streamlit Cloud, pero son **temporales**.

**Problema:** Si reinicias la app, los datos se pierden.

**Soluciones:**

#### Opción A: Git LFS (archivos en GitHub)
```bash
git lfs install
git lfs track "datos/**/*.xlsx"
git add .gitattributes
git add datos/
git commit -m "Agregar datos"
git push
```

#### Opción B: Google Drive (recomendado)
En una próxima iteración podemos integrar Google Drive para almacenamiento permanente.

#### Opción C: Secrets de Streamlit
Para datos pequeños (como clientes.json), usar Streamlit Secrets:
1. En Streamlit Cloud → App Settings → Secrets
2. Pegar contenido de `clientes.json`
3. Modificar código para leer desde secrets

---

## 💡 Consejos de Uso

### Para Vos (Contador)

1. **Mantené actualizados los datos** - Subi archivos regularmente
2. **Revisa el benchmarking** - Identifica clientes con problemas
3. **Usa links fáciles de recordar** - Códigos tipo `empresa_nombre`
4. **Backups** - Guarda copias de `clientes.json` y la carpeta `datos/`

### Para tus Clientes

1. **Guarden su link** - Agregar a favoritos del navegador
2. **Revisar mensualmente** - Analizar tendencias
3. **Usar filtros** - Comparar diferentes períodos
4. **Contactarte con dudas** - Vos interpretas los números

---

## 🔧 Solución de Problemas

### "Error: cliente no encontrado"
- Verifica que el código en la URL sea correcto
- Revisa `clientes.json` que el cliente exista

### "Aún no hay datos disponibles"
- El cliente no tiene archivos en su carpeta
- Subi datos desde el panel admin

### "Acceso denegado" en admin
- Verifica el código admin en la URL
- Debe ser: `?admin=admin2024` (o tu código personalizado)

### Los cambios no se reflejan
- Si estás en Streamlit Cloud, espera 1-2 minutos
- Presiona "Rerun" en la esquina superior derecha
- Si modificaste código, hace `git push` de nuevo

---

## 📈 Próximos Pasos y Mejoras

### Funcionalidades que podríamos agregar:

1. **Exportar a PDF** - Botón para descargar reportes
2. **Notificaciones por email** - Alertas automáticas
3. **Integración con Google Drive** - Actualización automática
4. **Comparación año vs año** - Análisis temporal
5. **Proyecciones** - Forecasting automático
6. **Multi-idioma** - Español e Inglés
7. **Temas personalizados** - Colores por cliente
8. **Comentarios del contador** - Notas en el dashboard

---

## ✅ Checklist de Implementación

### Fase 1: Local (Hoy)
- [ ] Instalar librerías
- [ ] Ejecutar admin panel
- [ ] Crear 2-3 clientes de prueba
- [ ] Subir datos de ejemplo
- [ ] Probar acceso de clientes
- [ ] Revisar benchmarking

### Fase 2: Preparación para Online
- [ ] Crear cuenta GitHub
- [ ] Subir código a repositorio
- [ ] Cambiar código admin
- [ ] Actualizar URLs en código

### Fase 3: Publicación
- [ ] Crear cuenta Streamlit Cloud
- [ ] Desplegar app de clientes
- [ ] Desplegar app de admin
- [ ] Probar accesos
- [ ] Enviar links a clientes

---

## 📞 Soporte

Si tenés problemas:
1. Revisa esta guía
2. Verifica los logs de Streamlit (en la consola)
3. Avisame y lo resolvemos juntos

---

¡Felicitaciones! Ahora tenés un sistema profesional de dashboards multi-cliente. 🎉
