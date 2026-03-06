# 📋 Sistema de Generación de Actas de Entrega - Red Medicron IPS

**Versión**: 2.0.0  
**Python**: 3.12+  
**Última Actualización**: Marzo 2026

---

## 📋 Descripción General

Aplicativo de escritorio desarrollado en **Python 3.12 + PyQt6** para gestionar la generación automática de **"Actas de Entrega de Medicamentos"** en formato PDF. El sistema integra:

- 🗄️ Conexión a **SQL Server** (bases: SIFacturacion, RedMedicronIPS)
- 📄 Procesamiento de plantillas Word con **docxtpl** (Jinja2)
- 🖨️ Conversión a PDF con Microsoft Word
- 🔐 Soporte para firmas digitales binarias
- ⚡ Interfaz responsiva con indicador de progreso
- 🛡️ Manejo robusto de excepciones y errores COM

---

## 🚀 Instalación Rápida

### Prerequisitos
- **Python 3.12+** instalado
- **Microsoft Word 2016+** (requerido para conversión a PDF)
- **SQL Server** accesible en red local (IP: 192.168.59.230)
- **pyodbc Driver 17 o superior** para SQL Server

### Pasos de Instalación

```bash
# 1. Clonar o descargar el proyecto
cd "g:\Desarollo Red Medicron IPS\SistemaFarmacia"

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales (IMPORTANTE)
# Editar config.py con las credenciales correctas:
# - Server: IP del SQL Server
# - UID: Usuario de autenticación
# - PWD: Contraseña

# 5. Ejecutar aplicación
python main.py
```

---

## ⚙️ Configuración (config.py)

Editar `config.py` y actualizar las credenciales de conexión:

```python
CONN_STR = (
    "Driver={SQL Server Native Client 11.0};"  # O Driver 17
    "Server=192.168.59.230;"
    "Database=sifacturacion;"
    "UID=ConexionSistemas;"
    "PWD=TuPassword_Aqui;"
)
```

### ⚠️ Variables de Entorno (Seguridad - Recomendado)

**Alternativa más segura** (evita hardcodear contraseñas):

```python
import os
CONN_STR = (
    "Driver={SQL Server Native Client 11.0};"
    f"Server={os.getenv('SQL_SERVER', '192.168.59.230')};"
    f"Database={os.getenv('SQL_DB', 'sifacturacion')};"
    f"UID={os.getenv('SQL_USER', 'ConexionSistemas')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
)
```

Luego ejecutar:
```bash
$env:SQL_SERVER = "192.168.59.230"
$env:SQL_USER = "ConexionSistemas"
$env:SQL_PASSWORD = "TuPassword"
python main.py
```

---

## 📖 Guía de Uso

### Flujo Básico

1. **Abrir Aplicación**
   - Ejecutar `python main.py`
   - Se abre la ventana principal

2. **Buscar Admisión**
   - Escribir número de admisión en el campo de entrada
   - Presionar `Enter` o click en botón **🔍 Buscar Entregas**
   - El sistema consulta SQL Server busca todas las entregas realizadas

3. **Seleccionar Entrega**
   - En la tabla aparecen las entregas disponibles
   - Click para seleccionar una fila
   - (Si hay 1 sola, se selecciona automáticamente)

4. **Generar PDF**
   - Click en botón **🖨️ Generar e Imprimir PDF**
   - Barra de progreso muestra el estado:
     - ✓ Validando archivo de salida
     - ✓ Cargando plantilla Word
     - ✓ Procesando firma digital
     - ✓ Renderizando Jinja2
     - ✓ Convirtiendo a PDF
   - El PDF se abre automáticamente en el lector predeterminado

### Status Bar (Parte Inferior)

Indica el estado de las operaciones:
- 🔍 Buscando entregas...
- ✓ Se encontraron X entrega(s)
- ✓ PDF generado: Acta_Entrega_123.pdf
- ❌ Error de conexión a BD

---

## 🏗️ Arquitectura del Proyecto
> **Nota**: este proyecto puede empacarse en un solo ejecutable (.exe) para distribución.

### 📦 Empaquetado a `.exe`

Para que el sistema se pueda ejecutar en máquinas donde no haya Python ni dependencias instaladas, se utiliza [PyInstaller](https://www.pyinstaller.org/) para generar un solo archivo ejecutable. **Advertencia importante**: _la conversión DOCX→PDF se hace mediante Microsoft Word_, por lo que Word debe estar instalado y accesible en cada equipo donde se ejecute el EXE. Si la aplicación no encuentra Word mostrará un error como:

> "Error durante conversión PDF: 'NoneType' object has no attribute 'write'"

A partir de la versión actual el programa detecta esta situación y sugiere comprobar la instalación.

El proceso básico es:

1. Activar el entorno virtual:
   ```powershell
   cd "g:\Desarollo Red Medicron IPS\SistemaFarmacia"
   venv\Scripts\activate
   ```

2. Instalar PyInstaller (ya incluido en `requirements.txt`):
   ```powershell
   pip install pyinstaller
   ```

3. Ejecutar el empaquetado desde la raíz del proyecto:
   ```powershell
   pyinstaller \
     --noconfirm \
     --onefile \
     --windowed \
     --icon=icono.ico \
     --add-data "ACTA_MEDICAMENTOS.docx;." \
     main.py
   ```
   - `--onefile` produce un solo `.exe` en `dist\`.
   - `--windowed` evita que se abra una consola al ejecutar la aplicación.
   - `--icon` asigna el icono provisto (`icono.ico`).
   - `--add-data` empaqueta la plantilla Word y cualquier otro recurso necesario.   
   **Importante**: el ejecutable **no contiene las credenciales de SQL**. Debes
   proporcionar un archivo `.env` junto al EXE con las variables
   `SQL_SERVER`, `SQL_DATABASE`, `SQL_DRIVER`, `SQL_USER` y
   `SQL_PASSWORD`, o bien modificar `config.py` antes de empaquetar para que
   incluya directamente la cadena de conexión. Si no hay datos válidos, al
   iniciar la aplicación verás el siguiente mensaje:

   > "Error en la búsqueda: Error de autenticación SQL Server. Verifique usuario
   > y contraseña en config.py"

   Esta verificación se hace en
   `config.py` y ahora intenta cargar `.env` desde la carpeta del ejecutable.
   Si prefieres no usar `.env`, puedes definir las variables de entorno en el
   sistema destino (PowerShell: `$env:SQL_USER = '...'`).
4. **Adaptaciones del código**: el módulo `report_gen.py` ya soporta cargar recursos dentro del ejecutable mediante la función `_resource_path()`. Esta función utiliza `sys._MEIPASS` cuando el programa está empaquetado.

5. **Opcional: editar el spec**: PyInstaller genera `main.spec` que puede ajustarse para incluir más datos, cambiar nombre del ejecutable, etc. Un ejemplo mínimo:
   ```python
   # -*- mode: python ; coding: utf-8 -*-

   block_cipher = None
   a = Analysis(
       ['main.py'],
       pathex=['.'],
       binaries=[],
       datas=[('ACTA_MEDICAMENTOS.docx', '.')],
       hiddenimports=[],
       hookspath=[],
       runtime_hooks=[],
       excludes=[],
       win_no_prefer_redirects=False,
       win_private_assemblies=False,
       cipher=block_cipher,
   )
   pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
   exe = EXE(
       pyz,
       a.scripts,
       [],
       exclude_binaries=True,
       name='SistemaFarmacia',
       debug=False,
       bootloader_ignore_signals=False,
       strip=False,
       upx=True,
       console=False,
       icon='icono.ico'
   )
   coll = COLLECT(
       exe,
       a.binaries,
       a.zipfiles,
       a.datas,
       strip=False,
       upx=True,
       name='SistemaFarmacia'
   )
   ```
   Guardar y ejecutar:
   ```powershell
   pyinstaller main.spec
   ```

6. **Resultado**: el ejecutable final aparece en `dist\` (por defecto `main.exe`). Puedes renombrarlo y distribuirlo; ya contiene Python y las dependencias.

> ⚠️ Al ejecutar por primera vez Windows puede mostrar advertencias de SmartScreen. Para despliegues formales se recomienda firmar el EXE.

---

```
SistemaFarmacia/
├── config.py                    # Credenciales SQL Server ⚙️
├── database.py                  # Consultas SQL + DataManager 🗄️
├── report_gen.py               # Generación Word→PDF 📄
├── main.py                      # Interfaz PyQt6 🖥️
├── ACTA_MEDICAMENTOS.docx       # Plantilla Word (Jinja2) 📋
├── requirements.txt             # Dependencias Python 📦
├── README.md                    # Esta documentación 📖
├── venv/                        # Entorno virtual Python 🐍
├── __pycache__/                 # Cache compilado
└── templates/                   # (Opcional) Plantillas adicionales
```

### Flujo de Datos

```
┌─────────────────┐
│  main.py (GUI)  │  ← Usuario ingresa admisión y selecciona entrega
└────────┬────────┘
         │ PDFWorker (Thread)
         ▼
┌─────────────────┐
│ database.py     │  ← 3 consultas SQL:
├─────────────────┤  1. Header (paciente, funcionario, institución)
│ SQL Server      │  2. Medicamentos (entregados vs formulados)
│ SIFacturacion   │  3. Firma digital (bytes binarios)
│ RedMedicronIPS  │
└────────┬────────┘
         │ (header, medicamentos, firma)
         ▼
┌─────────────────────────┐
│ report_gen.py           │  ← Renderiza context en Word
├─────────────────────────┤  → Valida PDF no esté abierto
│ ACTA_MEDICAMENTOS.docx  │  → Convierte a PDF (docx2pdf)
│ (Jinja2 Template)       │  → Limpia archivos temporales
│ + InlineImage (firma)   │
└────────┬────────────────┘
         │ PDF generado
         ▼
Acta_Entrega_12345.pdf  ← Abre automáticamente

```

---

## 🔑 Variables de Contexto en Plantilla Word

La plantilla `ACTA_MEDICAMENTOS.docx` espera las siguientes variables Jinja2:

| Variable | Tipo | Descripción | Ejemplo |
|----------|------|-------------|---------|
| `hc` | str | Número de historia clínica | "HC-2024-001" |
| `paciente` | str | Nombre completo paciente | "Juan Pérez García" |
| `doc_id` | str | Documento de identidad | "CC12953795" |
| `sede` | str | Nombre de la institución | "Hospital Central Red Medicron" |
| `funcionario` | str | Nombre farmacéutico | "Dra. María González" |
| `admision` | int | ID de admisión | 54321 |
| `id_entrega` | int | Número de entrega | 1 |
| `fecha_firma` | str | Fecha/hora de firma | "15/03/2024 14:30" |
| `firma_paciente` | InlineImage | Firma digital escaneada | (objeto binario) |
| `medicamentos` | list[dict] | Array de medicamentos: | Ver abajo ⬇️ |

### Estructura de `medicamentos` (Lista de Diccionarios)

Cada medicamento debe tener esta estructura para la tabla dinámica en Word:

```python
{
    'nombre': 'Amoxicilina 500mg',
    'lote': 'LT-2024-0045',
    'orden': 'ORD-001',
    'ordenado': 30,          # Cantidad formulada por médico
    'entregado': 25,         # Cantidad entregada al paciente
    'pendiente': 5           # Cantidad faltante (ordenado - entregado)
}
```

### Tabla en Word (Loop Jinja2)

```jinja2
{% for m in medicamentos %}
| {{ m.nombre }} | {{ m.lote }} | {{ m.orden }} | {{ m.ordenado }} | {{ m.entregado }} | {{ m.pendiente }} |
{% endfor %}
```

---

## 🐛 Troubleshooting

### ❌ Error: "No se puede conectar a la base de datos"

**Causa**: SQL Server no está disponible en 192.168.59.230

**Soluciones**:
```bash
# 1. Verificar conectividad con ping
ping 192.168.59.230

# 2. Probar conexión ODBC desde terminal
python -c "import pyodbc; conn = pyodbc.connect('Driver={SQL Server};Server=192.168.59.230;Database=sifacturacion;UID=ConexionSistemas;PWD=TU_PASS')"

# 3. Instalar driver ODBC más nuevo
# Descargar: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### ❌ Error: "El PDF está abierto. Ciérrelo antes..."

**Causa**: El PDF generado previamente sigue abierto

**Solución**:
1. Cerrar el PDF en el lector (Adobe Reader, Edge, etc.)
2. Esperar 1-2 segundos
3. Intentar generar de nuevo

### ❌ Error COM: "Microsoft Word no está instalado"

**Causa**: `docx2pdf` requiere Word instalado para conversión

**Soluciones**:
```bash
# 1. Instalar Microsoft Office (versión más reciente)
# Descargar desde: https://www.microsoft.com/office

# 2. Verificar que Word está en PATH:
where winword.exe

# 3. Si sigue fallando, usar programa alternativo (no soportado en v2.0):
# pip install libreoffice  # (alternativa futura)
```

### ❌ Error: "Plantilla ACTA_MEDICAMENTOS.docx no encontrada"

**Causa**: Archivo de plantilla ausente o ruta incorrecta

**Solución**:
1. Verificar que `ACTA_MEDICAMENTOS.docx` está en la raíz del proyecto
2. No comprimirlo en ZIP - debe ser archivo .docx independiente
3. Verificar permisos de lectura:
```bash
ls -la ACTA_MEDICAMENTOS.docx  # Linux/Mac
dir ACTA_MEDICAMENTOS.docx    # Windows
```

### ⚠️ Advertencia: "Archivo temporal no se limpió"

**Causa**: `temp_*.docx` no pudo eliminarse (permiso o archivo bloqueado)

**Impacto**: Mínimo - solo consume espacio en disco (~500KB por acta)

**Limpieza manual**:
```bash
# Limpiar temporales
del temp_*.docx
```

---

## 🔒 Consideraciones de Seguridad

### Credenciales SQL

⚠️ **NUNCA** commit `config.py` con contraseñas hardcodeadas al repositorio Git.

**Solución**:
1. Usar variables de entorno (ver sección Configuración)
2. Agregar `config.py` al `.gitignore`:
   ```
   config.py
   *.db
   *.log
   ```
3. Usar `.gitignore` con:
   ```bash
   echo "config.py" >> .gitignore
   git rm --cached config.py
   ```

### Firmas Digitales

- Se almacenan en SQL Server como `VARBINARY`
- Se convierten a `io.BytesIO()` para insertar en Word
- **No se validan** (validación es responsabilidad del sistema de entrada)

---

## 💡 Mejoras Futuras

- [ ] Impresión directa sin abrir PDF
- [ ] Caché de plantilla Word (mejorar rendimiento)
- [ ] Soporte para múltiples plantillas por sede
- [ ] Generación en batch (100+ actas simultaneas)
- [ ] Exportar directamente a SFTP para archivo
- [ ] Dashboard con estadísticas de entregas
- [ ] Validación de campos obligatorios antes de generar
- [ ] Registro de auditoría en tabla SQL (quién generó, cuándo)

---

## 📞 Soporte y Reportar Bugs

Para reportar problemas:
1. Describir pasos para reproducir
2. Attachar logs si es posible
3. Incluir versión Python: `python --version`
4. Incluir versión driver ODBC: `odbcconf.exe /a {check}`

---

## 📜 Licencia

**Propiedad de Red Medicron IPS**  
Todos los derechos reservados - 2024/2026

---

## 📝 Historial de Cambios

### v2.0.0 (Marzo 2026) - ACTUAL
✅ **Mejorado**:
- Validación robusta de archivos (verificar PDF abierto)
- Progress Bar con indicador de estado en tiempo real
- Threading para no bloquear GUI durante generación
- Manejo exhaustivo de excepciones COM y conexión
- Limpieza automática de temporales (try-finally)
- Mensajes de error amigables con QMessageBox
- Documentación completa

### v1.0.0 (Anterior)
- Versión base con funcionalidad core
- Sin manejo de errores robusto
- Conversión bloqueante a PDF

---

**Desarrollado con ❤️ para Red Medicron IPS**
