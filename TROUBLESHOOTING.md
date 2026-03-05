# Guía de Diagnóstico y Troubleshooting

## 🔧 Herramientas de Diagnóstico

### 1. Verificar Versión Python y Paquetes Requeridos

```bash
# Ver versión Python
python --version
# Esperado: Python 3.12.x

# Ver paquetes instalados
pip list | findstr "PyQt6 pyodbc docxtpl docx2pdf"

# Ver versión específica
pip show PyQt6
pip show pyodbc
pip show docxtpl
pip show docx2pdf
```

---

## 🌐 Problemas de Conexión SQL Server

### Síntoma 1: "Error de Autenticación SQL Server"

**Código de Error**: `28000`

**Checklist**:
1. ✓ Credenciales correctas en `config.py`
   ```python
   UID=ConexionSistemas  # Usuario correcto?
   PWD=SI.Admin.23$%*    # Contraseña correcta?
   ```

2. ✓ Usuario tiene permisos en SIFacturacion y RedMedicronIPS
   ```sql
   -- Ejecutar en SQL Server Management Studio
   USE sifacturacion;
   EXEC sp_helprolemember 'db_datareader';
   -- Verificar que ConexionSistemas aparece en la lista
   ```

3. ✓ Usuario no está bloqueado
   ```sql
   -- En SQL Server
   SELECT name, is_disabled FROM sys.sql_logins WHERE name='ConexionSistemas';
   -- is_disabled debe ser 0 (falso)
   ```

**Test de conexión desde PowerShell**:
```powershell
# Test 1: ODBC
$ConnectionString = "Driver={SQL Server Native Client 11.0};Server=192.168.59.230;Database=sifacturacion;UID=ConexionSistemas;PWD=SI.Admin.23$%*"
$Connection = New-Object System.Data.Odbc.OdbcConnection($ConnectionString)
$Connection.Open()
Write-Host "✓ Conexión exitosa"
$Connection.Close()

# Test 2: Python
python -c "
import pyodbc
try:
    conn = pyodbc.connect('Driver={SQL Server Native Client 11.0};Server=192.168.59.230;Database=sifacturacion;UID=ConexionSistemas;PWD=SI.Admin.23\$%*')
    print('✓ Conexión exitosa desde Python')
    conn.close()
except Exception as e:
    print(f'✗ Error: {e}')
"
```

---

### Síntoma 2: "Servidor SQL Server no disponible" o "Connection timeout"

**Código de Error**: `08001` o similar

**Checklist**:
1. ✓ Servidor está encendido (ping desde terminal)
   ```cmd
   ping 192.168.59.230
   # Esperado: respuesta con TTL
   ```

2. ✓ SQL Server está ejecutándose
   ```cmd
   # Conectarse a servidor remoto
   sqlcmd -S 192.168.59.230 -U ConexionSistemas -P "SI.Admin.23$%*" -Q "SELECT @@VERSION"
   ```

3. ✓ Firewall permite conexión en puerto 1433
   ```cmd
   # Test conectividad puerto
   Test-NetConnection 192.168.59.230 -Port 1433
   # Esperado: TcpTestSucceeded: True
   ```

4. ✓ SQL Server Browser está ejecutándose (si usa instancia nombrada)
   ```cmd
   # Verificar servicio
   Get-Service MSSQLSERVER | Select-Object Status
   Get-Service SQLBrowser | Select-Object Status
   # Status debe ser "Running"
   ```

5. ✓ Driver ODBC correctamente instalado
   ```cmd
   # Listar drivers disponibles
   odbcconf /a {QueristDrivers}
   # Debe aparecer: SQL Server, SQL Server Native Client 11.0, o ODBC Driver 17/18
   ```

---

### Síntoma 3: "Invalid object name" (Tabla no encontrada)

**Código de Error**: En `get_datos_completos()` consulta SQL

**Debug**:
```sql
-- Verificar que tablas existen
USE sifacturacion;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%mPacientes%';
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%mAdmisiones%';

-- Verificar esquema
USE RedMedicronIPS;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Dispensacion%';
```

**Solución**:
- Ajustar nombres de tablas en `database.py` según esquema actual
- Usar `sys.tables` para listar todas las tablas y sus esquemas

---

## 📄 Problemas con Generación de PDF

### Síntoma 1: "Error COM: Microsoft Word no está instalado"

**Causa**: `docx2pdf` requiere Word para conversión

**Soluciones**:
1. Instalar Microsoft Word 2016 o superior
   - Opción A: Microsoft 365
   - Opción B: Office 2021 perpetua
   - Opción C: Office 2019

2. Verificar que Word está accesible desde línea de comandos
   ```cmd
   where winword.exe
   # Esperado: C:\Program Files\Microsoft Office\...
   ```

3. Reparar instalación de Office
   - Control Panel → Programs → Programs and Features
   - Seleccionar Microsoft Office → Change
   - Seleccionar "Quick Repair" o "Online Repair"

4. Alternativa (docx2pdf con LibreOffice) - NO SOPORTADO en v2.0
   ```bash
   # Futuro: soporte para LibreOffice
   pip install libreoffice
   ```

---

### Síntoma 2: "El PDF está abierto. Ciérrelo antes..."

**Causa**: PDF anterior aún está abierto en un programa

**Verificar archivos abiertos**:
```powershell
# Mostrar archivos abiertos por Word
Get-Process | Where-Object {$_.ProcessName -like "*word*"} | Select-Object ProcessName, Id

# Forzar cerrar si es necesario (último recurso)
Stop-Process -Name WINWORD -Force
```

**Solución**:
1. Cerrar manualmente PDF (Adobe Reader, Edge, etc.)
2. Esperar 2-3 segundos
3. Reintentar generación

---

### Síntoma 3: "Plantilla ACTA_MEDICAMENTOS.docx no encontrada"

**Debug**:
```python
import os
base_path = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(base_path, "ACTA_MEDICAMENTOS.docx")
print(f"Ruta esperada: {template_path}")
print(f"Existe: {os.path.exists(template_path)}")

# Listar archivos en directorio actual
for f in os.listdir(base_path):
    if "ACTA" in f.upper() or f.endswith(".docx"):
        print(f"  Encontrado: {f}")
```

**Solución**:
1. Copiar `ACTA_MEDICAMENTOS.docx` a la **raíz** del proyecto
2. Asegurar que no está en carpeta `templates/` incorrectamente
3. Verificar permisos de lectura:
   ```cmd
   icacls "ACTA_MEDICAMENTOS.docx"
   # Crear permiso si es necesario
   icacls "ACTA_MEDICAMENTOS.docx" /grant "%USERNAME%:F"
   ```

---

### Síntoma 4: "Error en renderización Jinja2"

**Mensajes comunes**:
- `UndefinedError: 'medicamentos' is undefined`
- `TypeError: cannot iterate over NoneType`

**Causa**: Variable falta en contexto de `report_gen.py`

**Debug**:
```python
# En report_gen.py método build():
print("Context a enviar:")
for k, v in context.items():
    print(f"  {k}: {type(v).__name__} = {repr(v)[:100]}")
```

**Solución**:
- Asegurar que `database.py` retorna tuplas/objetos con todos los campos esperados
- Verificar que `medicamentos` es lista (no None):
  ```python
  if medicamentos is None:
      medicamentos = []
  ```

---

## 🖥️ Problemas con Interfaz (GUI)

### Síntoma 1: "La aplicación se congela durante generación"

**Causa**: Operación bloqueante en thread principal

**Estado en v2.0.0**: ✅ **RESUELTO** con `PDFWorker` (threading)

**Verificación**:
```python
# main.py debe tener:
# - Clase PDFWorker(Thread)
# - self.worker.start() en generar()
# - Señales de comunicación (progress, finished, error)
```

---

### Síntoma 2: "Progress Bar no muestra"

**Cause**: Callback no está conectado

**Debug en main.py**:
```python
# Verificar:
self.gen = ReportGenerator(progress_callback=self._on_progress)
# ✓ Pasar callback al constructor

# Verificar método existe:
def _on_progress(self, message):
    self.status_label.setText(message)
```

---

### Síntoma 3: "Botones deshabilitados permanentemente"

**Causa**: Excepción en worker sin llamar a `_reset_buttons()`

**Solución**: Asegurar que:
1. `PDFWorker.run()` tiene try-except completo
2. Todos los caminos emiten `signals.error()` o `signals.finished()`
3. Main está conectado a ambas señales:
   ```python
   self.worker.signals.error.connect(self._on_error)
   self.worker.signals.finished.connect(self._on_success)
   ```

---

## 📊 Verificación de Datos en SQL

### Script para validar estructura de base de datos

```sql
-- Ejecutar en SQL Server Management Studio

-- 1. Verificar tablas principales
USE sifacturacion;
SELECT 'mPacientes' as Tabla, COUNT(*) as Registros FROM mPacientes;
SELECT 'mAdmisiones' as Tabla, COUNT(*) as Registros FROM mAdmisiones;
SELECT 'cAdministracion' as Tabla, COUNT(*) as Registros FROM cAdministracion;
SELECT 'dHCOrdenesExternas' as Tabla, COUNT(*) as Registros FROM dHCOrdenesExternas;

-- 2. Verificar tablas RedMedicronIPS
USE RedMedicronIPS;
SELECT 'DispensacionFarmaciaPGP' as Tabla, COUNT(*) as Registros FROM DispensacionFarmaciaPGP;
SELECT 'DispensacionFarmaciaPGPFirmaRecibido' as Tabla, COUNT(*) as Registros FROM DispensacionFarmaciaPGPFirmaRecibido;
SELECT 'GeneralesUsuario' as Tabla, COUNT(*) as Registros FROM GeneralesUsuario;

-- 3. Buscar una admisión específica
DECLARE @IdAdmision INT = 54321; -- Cambiar por número real
SELECT * FROM DispensacionFarmaciaPGP WHERE IdAdmision = @IdAdmision;
SELECT * FROM DispensacionFarmaciaPGPFirmaRecibido WHERE idAdmision = @IdAdmision;

-- 4. Verificar campos específicos
EXEC sp_columns 'DispensacionFarmaciaPGP';
EXEC sp_columns 'DispensacionFarmaciaPGPFirmaRecibido';
```

---

## 🧪 Test Unitario Manual

```python
# Crear archivo test_diagnóstico.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import CONN_STR
from database import DataManager
from report_gen import ReportGenerator

def test_conexion():
    print("✓ Test 1: Conexión SQL Server")
    db = DataManager()
    try:
        entregas = db.get_entregas(54321)  # Cambiar por ID real
        print(f"  ✓ Conexión OK. Entregas encontradas: {len(entregas)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def test_datos_completos():
    print("\n✓ Test 2: Obtener datos completos")
    db = DataManager()
    try:
        h, m, f = db.get_datos_completos(54321, 1)  # Cambiar valores
        print(f"  ✓ Header: {h.PacienteCompleto if h else 'None'}")
        print(f"  ✓ Medicamentos: {len(m) if m else 0}")
        print(f"  ✓ Firma: {'Sí' if f and f.imagenFirma else 'No'}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def test_generacion():
    print("\n✓ Test 3: Generación PDF")
    db = DataManager()
    gen = ReportGenerator()
    try:
        h, m, f = db.get_datos_completos(54321, 1)  # Cambiar valores
        pdf_path = gen.build(h, m, f, 1)
        print(f"  ✓ PDF generado: {pdf_path}")
        print(f"  ✓ Existe: {os.path.exists(pdf_path)}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    test_conexion()
    test_datos_completos()
    test_generacion()
```

Ejecutar con:
```bash
python test_diagnóstico.py
```

---

## 📋 Checklist Pre-Producción

- [ ] `config.py` tiene credenciales correctas (no hardcodeadas en git)
- [ ] `ACTA_MEDICAMENTOS.docx` está en raíz del proyecto
- [ ] Python 3.12+ instalado
- [ ] Todas las dependencias en `requirements.txt` instaladas
- [ ] Microsoft Word 2016+ instalado
- [ ] Conectividad SQL Server verificada (ping + sqlcmd)
- [ ] Script de diagnóstico pasó sin errores
- [ ] Prueba manual con datos reales funciona
- [ ] PDF se abre automáticamente después de generación
- [ ] No hay archivos `temp_*.docx` huérfanos

---

**¡Documentación actualizada a Marzo 2026!**
