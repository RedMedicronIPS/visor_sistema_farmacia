# 🏗️ Arquitectura Técnica

Documentación para desarrolladores que mantienen o extienden el sistema.

---

## Visión General

Sistema de 3 capas diseñado para máxima responsabilidad y testabilidad:

```
┌────────────────────────────────┐
│ GUI Layer (PyQt6)              │ ← main.py
│ - Interfaz usuario             │    PDFWorker, WorkerSignals
│ - Threading                    │
│ - Manejo de eventos            │
└────────────┬────────────────────┘
             │ (Datos, Callbacks)
             ▼
┌────────────────────────────────┐
│ Business Logic (Report Gen)    │ ← report_gen.py
│ - Procesamiento plantilla      │    ReportGenerator
│ - Validaciones                 │
│ - Conversión PDF               │
└────────────┬────────────────────┘
             │ (SQL, BytesIO)
             ▼
┌────────────────────────────────┐
│ Data Access Layer (SQL)        │ ← database.py
│ - Consultas SQL                │    DataManager
│ - Conexiones ODBC              │
│ - Manejo de errores DB         │
└────────────┬────────────────────┘
             │
             ▼
         SQL Server
```

---

## 📁 Estructura de Módulos

### `config.py` - Configuración
**Responsabilidad**: Credenciales y constantes globales

```python
CONN_STR = "Driver=...;Server=...;"  # Conexión SQL Server
```

**Cambiar para**: 
- Diferentes ambientes (dev, staging, prod)
- Variables de entorno en producción

### `database.py` - Acceso a Datos
**Responsabilidad**: Consultas SQL, abstraer BD

```python
class DataManager:
    def _get_connection()        # Encapsula conexión ODBC
    def get_entregas()           # SELECT entregas por admisión
    def get_datos_completos()    # SELECT cabecera, medicamentos, firma
```

**Return Types**:
- `get_entregas()` → `list[Row]` (Row = (numeroEntrega, fechaEntrega))
- `get_datos_completos()` → `tuple[Row, list[Row], Row|None]`
  - Row = Objeto nombrado con atributos por columna SQL

**Errores Levantados**:
- `pyodbc.Error` → Traducido a Exception con mensaje español
- `Exception("No se encontraron datos...")` → Error lógico

---

### `report_gen.py` - Generación de Reportes
**Responsabilidad**: Word → Jinja2 → PDF

```python
class ReportGenerator:
    def __init__(progress_callback)      # Callback para UI
    def build(header, meds, firma, id) → str  # Ruta PDF generado
```

**Métodos Privados (Helpers)**:
- `_is_file_locked(filepath)` → bool (archivo abierto?)
- `_wait_for_file_release(filepath)` → bool (esperar liberación?)
- `_cleanup_temp_file(filepath)` → bool (limpiar temporal?)
- `_check_pdf_exists_and_locked(filepath)` → None (validar salida?)
- `_log_progress(msg)` → None (callback → UI)

**Flujo de `build()`**:
1. Validar plantilla existe
2. Validar PDF salida no está abierto
3. Cargar plantilla DOCX
4. Procesar firma (binario → InlineImage)
5. Mapear contexto (dict con variables)
6. Renderizar Jinja2
7. Guardar DOCX temporal
8. Convertir a PDF (docx2pdf + Word)
9. Limpiar temporal (finally)
10. Retornar ruta PDF

**Manejo de Excepciones**:
- `FileNotFoundError` → Plantilla ausente
- `PermissionError` → PDF abierto o permisos insuficientes
- `Exception` → Error COM de Word (sin Word instalado)
- Todo se captura, se log, se levanta con contexto

---

### `main.py` - Interfaz de Usuario
**Responsabilidad**: PyQt6 GUI, threading, eventos

```python
class AppFarmacia(QMainWindow):
    def setup_ui()               # Widget, layouts, conexiones
    def cargar_entregas()        # Buscar en BD
    def generar()                # Iniciar PDFWorker
    def _on_progress(msg)        # Recibir updates
    def _on_success(pdf)         # Éxito, mostrar dialogo
    def _on_error(error)         # Error, mostrar error
    def _reset_buttons()         # Habilitar botones

class PDFWorker(Thread):
    def run()                    # Ejecutar en hilo separado
    # Emite: signals.progress, signals.finished, signals.error

class WorkerSignals(QObject):    # Emisor de señales PyQt
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
```

**Flujo de Eventos**:
```
Usuario ingresa admisión
    ↓
Click "Buscar"
    ↓
cargar_entregas()
    ↓
database.get_entregas()
    ↓
Tabla se llena
    ↓
Usuario selecciona entrega + click "Generar"
    ↓
generar():
  - Deshabilitar botones
  - Mostrar progress bar
  - Crear PDFWorker
  - worker.start() ← Nuevo thread
    │
    ├─→ PDFWorker.run()
    │    - database.get_datos_completos()
    │    - report_gen.build()
    │    - Emitir: progress, finished/error
    │
    ├─→ Signals conectan a callbacks:
    │    - progress → _on_progress() → actualizar label
    │    - finished → _on_success() → dialogo OK, habilitar botones
    │    - error → _on_error() → dialogo error, habilitar botones
    │
    └─→ Main thread continúa responsivo
```

---

## 🔄 Flujo de Datos (End-to-End)

```
┌─────────────────────────────────────────────────────────┐
│                    USER INPUT                           │
│  Escribe "54321" (Número de Admisión) + Click Buscar   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  main.py             │
            │ cargar_entregas()    │
            │                      │
            │ 1. get_text()        │
            │ 2. db.get_entregas() │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────────────┐
            │ database.py                  │
            │ get_entregas(id_admision)    │
            │                              │
            │ SELECT numeroEntrega,        │
            │        fechaEntrega          │
            │ FROM DispensacionFarmaciaPGP │
            │ WHERE IdAdmision = 54321     │
            └──────────┬───────────────────┘
                       │ Retorna:
                       │ [(1, 2024-03-01),
                       │  (2, 2024-03-05)]
                       ▼
            ┌──────────────────────┐
            │  main.py            │
            │ tabla.insertRow()   │
            │ tabla.setItem()     │
            │                     │
            │ Mostrar tabla:      │
            │ Nº    Fecha         │
            │ ──────────────────  │
            │ 1 │ 2024-03-01     │
            │ 2 │ 2024-03-05     │
            └──────────┬──────────┘
                       │
                       ▼ (Usuario selecciona fila 1, click "Generar")
            ┌──────────────────────────┐
            │  main.py                │
            │ generar()               │
            │                         │
            │ PDFWorker.start()       │
            │ (Nuevo Thread)          │
            └──────────┬──────────────┘
                       │
         ┌─────────────┴──────────────┐
         │ (MAIN THREAD)              │ (WORKER THREAD)
         │ GUI sigue responsivo       │ Procesa PDF
         │                            │
         │                            ▼
         │              ┌─────────────────────────┐
         │              │ PDFWorker.run()         │
         │              │                         │
         │              │ 1. db.get_datos_        │
         │              │    completos()          │
         │              │                         │
         │              │ SELECT p.*, s.*,        │
         │              │        u.* (JOIN)       │
         │              │ WHERE IdAdmision=54321, │
         │              │       numeroEntrega=1   │
         │              │                         │
         │              │ Retorna:                │
         │              │ (header, meds, firma)   │
         │              └────────┬────────────────┘
         │                       │
         │                       ▼ Emit signal: progress
         │              ┌─────────────────────────┐
         │              │ signals.progress.emit() │
         │              │ "Generando PDF..."      │
         │              └────────┬────────────────┘
         │                       │
         │                       ▼ Signal conectado
         │              ┌─────────────────────────┐
         │              │ main.py:                │
         │              │ _on_progress(msg)       │
         │              │ status_label.setText()  │
         │              └────────┬────────────────┘
         │                       │
         │                       ▼ GUI actualizada
         │              status_label:
         │              "✓ Generando PDF..."
         │                       │
         │                       ▼
         │              ┌──────────────────────┐
         │              │ report_gen.py:       │
         │              │ build(h, m, f, id)   │
         │              │                      │
         │              │ 1. Check PDF abierto │
         │              │ 2. Load plantilla    │
         │              │ 3. Procesar firma    │
         │              │ 4. Render Jinja2     │
         │              │ 5. Guardar DOCX      │
         │              │ 6. Convert → PDF     │
         │              │ 7. Cleanup temporal  │
         │              │                      │
         │              │ Retorna:             │
         │              │ "Acta_54321.pdf"     │
         │              └────────┬─────────────┘
         │                       │
         │                       ▼ Emit signal: finished
         │              ┌──────────────────────┐
         │              │ signals.finished.    │
         │              │ emit(pdf_path)       │
         │              └────────┬─────────────┘
         │                       │
         │ ┌────────────────────┘│
         │ │ Signal conectado   │
         │ ▼                    │
         │ _on_success()        │
         │ │                    │
         │ ├─ progress_bar.hide()
         │ ├─ QMessageBox.info("Éxito")
         │ ├─ status.setText("✓ PDF generado")
         │ ├─ _reset_buttons()
         │ └─ os.startfile(pdf) → Abre PDF
         │                    │
         │                    ▼
         │              PDF abierto en lector
         └────────────────────────────────────┘
```

---

## 🧪 Testing

### Test Manual

```python
# test_manual.py
from database import DataManager
from report_gen import ReportGenerator

# 1. Test conexión
db = DataManager()
entregas = db.get_entregas(54321)
assert len(entregas) > 0, "No hay entregas"

# 2. Test datos completos
header, meds, firma = db.get_datos_completos(54321, 1)
assert header is not None, "No hay header"
assert len(meds) > 0, "No hay medicamentos"

# 3. Test generación PDF
gen = ReportGenerator()
pdf = gen.build(header, meds, firma, 1)
assert os.path.exists(pdf), "PDF no se creó"
```

### Future: Unit Tests (pytest)

```python
# tests/test_database.py
import pytest
from database import DataManager
from config import CONN_STR

class TestDataManager:
    @pytest.fixture
    def db(self):
        return DataManager()
    
    def test_get_entregas_valid(self, db):
        result = db.get_entregas(54321)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_entregas_invalid(self, db):
        result = db.get_entregas(999999999)
        assert isinstance(result, list)
        assert len(result) == 0

# tests/test_report_gen.py
class TestReportGenerator:
    def test_build_creates_pdf(self):
        # Obtener datos mock
        h = ... # header mock
        m = ... # medicamentos mock
        f = None # firma
        
        gen = ReportGenerator()
        pdf = gen.build(h, m, f, 1)
        
        assert os.path.exists(pdf)
        assert pdf.endswith(".pdf")
```

---

## 🔧 Extensiones Comunes

### Agregar nuevo campo a plantilla Word

1. **Planilla Word** (ACTA_MEDICAMENTOS.docx):
   - Editar plantilla
   - Agregar etiqueta: `{{ nuevo_campo }}`

2. **database.py**:
   ```python
   def get_datos_completos(...):
       # En header_sql agregar column:
       header_sql = """
       SELECT ..., nuevo_campo
       FROM ...
       """
   ```

3. **report_gen.py**:
   ```python
   context = {
       ...
       'nuevo_campo': header.nuevo_campo,  # ← Agregar línea
       ...
   }
   ```

### Cambiar tabla de medicamentos a por lotes

En `report_gen.py`:
```python
# Actual:
'medicamentos': [
    {'nombre': m.nomSuministro, 'lote': m.numeroLote, ...}
    for m in meds
]

# Cambiado (agrupar por lote):
from itertools import groupby

medicamentos_grouped = []
for lote, items in groupby(meds, key=lambda m: m.numeroLote):
    medicamentos_grouped.append({
        'lote': lote,
        'items': list(items)
    })

context = {
    ...
    'medicamentos': medicamentos_grouped
}
```

Luego en plantilla Word:
```jinja2
{% for lote_group in medicamentos %}
  <h3>Lote: {{ lote_group.lote }}</h3>
  {% for m in lote_group.items %}
    ...
  {% endfor %}
{% endfor %}
```

### Agregar impresión directa (sin abrir PDF)

En `main.py`:
```python
def _on_success(self, pdf_path):
    # En lugar de os.startfile, usar:
    if self.auto_print:
        os.startfile(pdf_path, "print")
    else:
        os.startfile(pdf_path)  # Abrir
```

---

## 🐛 Debugging

### Habilitar logs en tiempo real

```python
# En report_gen.py
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler("app.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def _log_progress(self, message):
    logger.debug(message)
    if self.progress_callback:
        self.progress_callback(message)
```

### Inspeccionar PDFWorker

```python
# En main.py PDFWorker.run()
import traceback

try:
    ...
except Exception as e:
    traceback.print_exc()  # Mostrar stack trace completo
    self.signals.error.emit(f"Error:\n{traceback.format_exc()}")
```

---

## 📈 Performance

### Tiempos típicos (en desarrollo):

- `db.get_entregas()`: 0.2-0.5s (RED local)
- `db.get_datos_completos()`: 0.5-1.0s (3 JOINs)
- `gen.build()`: 2-4s (conversión Word → PDF más lenta)
- **Total**: 3-5 segundos

### Optimizaciones futuras:

1. Cachear plantilla (no recargar cada vez)
   ```python
   self.doc_template = None  # Cache
   if not self.doc_template:
       self.doc_template = DocxTemplate(template_path)
   ```

2. Usar multiprocessing para múltiples PDFs
3. Pre-renderizar contexto Word  
4. Usar LibreOffice en lugar de Word (más rápido)

---

## 🔒 Seguridad

### SQL Injection Prevention
✅ Uso de parámetros SQL:
```python
cursor.execute("WHERE IdAdmision = ?", (id_admision,))  # Safe
# NO: cursor.execute(f"WHERE IdAdmision = {id_admision}")  # Unsafe
```

### Credenciales
⚠️ **NUNCA** hardcodear en código:
```python
# Usar variables de entorno
import os
PWD = os.getenv('SQL_PASSWORD')  # Desde .env o system
```

### Firma Digital
⚠️ No se valida en este sistema (validación en punto de entrada)

---

**Última actualización**: Marzo 2026
