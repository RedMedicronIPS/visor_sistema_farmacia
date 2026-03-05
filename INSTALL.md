# 📦 Guía de Instalación - Sistema de Actas de Entrega

Guía completa paso a paso para instalar y configurar el sistema.

---

## 📋 Requierimientos Previos

Antes de comenzar, verifique que tiene:

- [ ] **Windows 10 o superior** (Windows 11 recomendado)
- [ ] **Python 3.12.x** instalado y en PATH
- [ ] **Microsoft Word 2016 o superior** (cualquier versión de Office)
- [ ] **SQL Server Native Client 11.0 o ODBC Driver 17+** instalado
- [ ] **Acceso de red** a servidor SQL Server (192.168.59.230)
- [ ] **250 MB** de espacio libre en disco

### Verificar Requisitos

Abra **PowerShell** (como Administrador) y copie estos comandos:

```powershell
# Verificar Python
python --version
# Esperado: Python 3.12.x o superior

# Verificar Word
where winword.exe
# Esperado: C:\Program Files\...\WINWORD.EXE

# Verificar Driver ODBC
Get-OdbcDriver | findstr "SQL"
# Esperado: SQL Server, SQL Server Native Client, o ODBC Driver 17
```

Si alguno **NO está instalado**:

| Requisito | Acción |
|-----------|--------|
| Python 3.12 faltante | Descargar de https://www.python.org/downloads/ |
| Word faltante | Instalar desde https://www.microsoft.com/office |
| ODBC faltante | Descargar de https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server |

---

## 🚀 Instalación Paso a Paso

### Paso 1: Descargar/Clonar Proyecto

```powershell
# Opción A: Si tienes Git
git clone https://[repositorio]/SistemaFarmacia.git
cd SistemaFarmacia

# Opción B: Si descargaste ZIP
# 1. Descargar archivo ZIP desde repositorio
# 2. Descomprimir en C:\Proyectos\SistemaFarmacia
# 3. Abrir PowerShell en esa ubicación
cd "C:\Proyectos\SistemaFarmacia"
```

Verifica que ves estos archivos:

```
├── config.py              ✓
├── database.py            ✓
├── main.py                ✓
├── report_gen.py          ✓
├── requirements.txt       ✓
├── ACTA_MEDICAMENTOS.docx ✓
├── README.md              ✓
└── .gitignore             ✓
```

---

### Paso 2: Crear Entorno Virtual

```powershell
# Crear carpeta virtual environment
python -m venv venv

# Activar el entorno
venv\Scripts\activate

# Esperado: Verás (venv) al inicio de la línea en PowerShell
```

**Si tienes error**: `venv\Scripts\activate: File not found`

Intenta:
```powershell
# Para PowerShell Core
venv\Scripts\Activate.ps1

# Si aún falla, permitir ejecución de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

---

### Paso 3: Instalar Dependencias

Con el entorno virtual **activado** (vea `(venv)` en PowerShell):

```powershell
# Actualizar pip (recomendado)
pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt

# Espere 2-3 minutos. Verá:
# Successfully installed PyQt6-6.6.0 pyodbc-5.0.0 docxtpl-0.16.0 docx2pdf-1.3.0
```

**Mensaje de éxito esperado**:
```
Successfully installed PyQt6 pyodbc python-docx docxtpl docx2pdf
```

**Si algo falla**:
```powershell
# Instalar paquetes uno por uno para ver cuál falla
pip install PyQt6
pip install pyodbc
pip install docxtpl
pip install docx2pdf

# Si pyodbc falla, instalar build tools
pip install --upgrade setuptools wheel
pip install pyodbc --no-cache-dir
```

---

### Paso 4: Configurar Credenciales SQL Server

Abre el archivo `config.py` con tu editor favorito:

```powershell
# Abrir con Notepad++
notepad++ config.py

# O con VS Code
code config.py

# O con Notepad simplemente
notepad config.py
```

El archivo verá así:

```python
# config.py
CONN_STR = (
    "Driver={SQL Server};"
    "Server=192.168.59.230;"
    "Database=sifacturacion;"
    "UID=ConexionSistemas;"
    "PWD=SI.Admin.23$%*;"
)
```

**Actualiza con tus credenciales reales**:

| Campo | Cambiar a | Ejemplo |
|-------|-----------|---------|
| `Server` | IP del SQL Server en red local | 192.168.59.230 |
| `Database` | Nombre de base de datos | sifacturacion |
| `UID` | Usuario SQL Server | admin_ips |
| `PWD` | Contraseña usuario | MiPassword123! |

**Ejemplo después de actualizar**:

```python
CONN_STR = (
    "Driver={SQL Server};"
    "Server=192.168.59.230;"
    "Database=sifacturacion;"
    "UID=admin_ips;"
    "PWD=MiPassword123!;"
)
```

⚠️ **IMPORTANTE**: NO commit este archivo a Git (credenciales privadas). Está en `.gitignore`.

**Guardar cambios**: `Ctrl+S` en el editor

---

### Paso 5: Verificar Plantilla Word

Asegúrate que `ACTA_MEDICAMENTOS.docx` está en la **raíz** del proyecto:

```powershell
# Listar archivos y buscar la plantilla
dir *.docx

# Esperado:
# ACTA_MEDICAMENTOS.docx (archivo debe estar aquí)
```

Si falta:
1. Descargar de repositorio o servidor compartido
2. Copiar a `C:\Proyectos\SistemaFarmacia\ACTA_MEDICAMENTOS.docx`
3. Verificar con `dir *.docx` de nuevo

---

### Paso 6: Test de Conexión SQL Server

Antes de ejecutar app, verifica que la conexión SQL funciona:

```powershell
# Ejecutar script de prueba
python -c "
import pyodbc
from config import CONN_STR
try:
    conn = pyodbc.connect(CONN_STR)
    print('✓ Conexión SQL Server exitosa')
    conn.close()
except Exception as e:
    print(f'✗ Error: {e}')
"
```

**Resultado esperado**:
```
✓ Conexión SQL Server exitosa
```

**Si da error**:
- Ver sección „Solución de Problemas" abajo

---

### Paso 7: Ejecutar Aplicación

```powershell
# Asegúrate que entorno virtual está activado (vea "(venv)" en PowerShell)
python main.py
```

**Esperado**:
- Se abre ventana con título "Generador de Actas de Entrega - Red Medicron IPS"
- Campo de entrada para "Admisión"
- Botón "🔍 Buscar Entregas"
- Tabla vacía (esperado al inicio)

Si se abre: ✅ **¡Instalación completada exitosamente!**

---

## 🧪 Prueba el Sistema (Test)

Una vez abierta la aplicación:

### Test 1: Búsqueda

1. Escribe un número de admisión válido (ej: 54321)
2. Presiona `Enter` o click en "🔍 Buscar"
3. **Esperado**: Tabla muestra 1+ entregas

Si no muestra resultados:
- Es posible que no haya datos para esa admisión
- Probar con otro número de admisión

### Test 2: Generación PDF

1. Si hay entregas, selecciona una (click en fila)
2. Click en "🖨️ Generar e Imprimir PDF"
3. Verá barra de progreso
4. Después de 3-5 segundos: PDF se abre automáticamente

**Esperado**:
- Archivo `Acta_Entrega_123.pdf` aparece en carpeta del proyecto
- Se abre en lector PDF (Adobe Reader, Edge, etc.)

---

## ⚡ Arranque Rápido (Después de Instalación)

Próximas veces que usar el sistema:

```powershell
# 1. Abrir PowerShell en carpeta del proyecto
cd "C:\Proyectos\SistemaFarmacia"

# 2. Activar entorno virtual
venv\Scripts\Activate.ps1

# 3. Ejecutar app
python main.py
```

O crear un **acceso directo** en Windows:
1. Click derecho en escritorio → "Nuevo" → "Acceso directo"
2. Ubicación del elemento:
   ```
   powershell.exe -NoExit -Command "cd 'C:\Proyectos\SistemaFarmacia' && venv\Scripts\Activate.ps1 && python main.py"
   ```
3. Nombre: "Actas de Entrega"
4. Aceptar

Próximas veces: Solo doble-click en acceso directo.

---

## 🆘 Solución de Problemas de Instalación

### Problema: "Python no reconocido"

```
'python' is not recognized as an internal or external command
```

**Solución**:
1. Descargar Python desde https://www.python.org/downloads/ (seleccionar Python 3.12+)
2. Durante instalación: ✅ **Marcar casilla "Add Python to PATH"**
3. Reiniciar PowerShell
4. Verificar: `python --version`

---

### Problema: "-ExecutionPolicy"

```
venv\Scripts\Activate.ps1: File not found
```

**Solución**:
```powershell
# Permitir ejecución de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego try de nuevo
venv\Scripts\Activate.ps1
```

---

### Problema: pip instala paquetes pero falta módulo

```
ModuleNotFoundError: No module named 'PyQt6'
```

**Solución**:
```powershell
# Verificar que entorno virtual está activado (debe ver "(venv)" en PowerShell)
which python
# Esperado: C:\Proyectos\SistemaFarmacia\venv\Scripts\python.exe

# Si no está en venv, activar:
venv\Scripts\Activate.ps1

# Re-instalar
pip install PyQt6
```

---

### Problema: "pyodbc" no se instala

```
ERROR: Microsoft Visual C++ 14.0 is required
```

**Solución**:
```powershell
# Instalar build tools
pip install --upgrade setuptools wheel
pip install --upgrade pip

# Luego re-intentar
pip install pyodbc --no-cache-dir
```

O descargar desde: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

### Problema: SQL Server "No disponible" o "Connection timeout"

```
Error: ('08001', '[08001] [Microsoft]... Connection timeout expired')
```

**Verificaciones**:
```powershell
# 1. Ping al servidor
ping 192.168.59.230

# 2. Probar puerto 1433 (SQL Server)
Test-NetConnection 192.168.59.230 -Port 1433

# 3. Probar con sqlcmd
sqlcmd -S 192.168.59.230 -U ConexionSistemas -P "TuPassword" -Q "SELECT @@VERSION"
```

Si ping/puerto fallan: SQL Server no está disponible en red. Contactar admin red.

---

### Problema: Microsoft Word no está instalado

```
Error: pywintypes.com_error (docx2pdf requires Microsoft Word)
```

**Solución**:
1. Instalar Microsoft Office desde https://www.microsoft.com/office
2. O si ya tienes: Reparar Office
   - Control Panel → Programs → Programs and Features
   - Buscar "Microsoft Office" → Click → "Change" → "Quick Repair"

---

## 📋 Verificación Final (Checklist)

Antes de usar en producción:

- [ ] `python --version` muestra 3.12+
- [ ] `pip install -r requirements.txt` completó sin errores
- [ ] `config.py` tiene credenciales correctas
- [ ] `ACTA_MEDICAMENTOS.docx` existe en raíz
- [ ] Test conexión SQL: `✓ Conexión SQL Server exitosa`
- [ ] App se abre sin errores: `python main.py`
- [ ] Búsqueda retorna resultados (admisión válida)
- [ ] Generación de PDF completa en 3-5 segundos
- [ ] PDF se abre automáticamente

✅ Si todos están check: **¡Sistema listo para usar!**

---

## 🆘 Soporte

Si tienes problemas:

1. Leer [README.md](README.md) - Documentación general
2. Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 10+ soluciones comunes
3. Contactar al equipo de TI de Red Medicron IPS

---

**Última actualización**: Marzo 2026  
**Versión Sistema**: 2.0.0
