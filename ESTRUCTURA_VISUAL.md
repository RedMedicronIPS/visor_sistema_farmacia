# 🗂️ Estructura del Proyecto - Referencia Visual

```
SistemaFarmacia/
│
├─ 🐍 CÓDIGO FUENTE
│  ├─ config.py                    # ⚙️  Credenciales SQL Server
│  │  └─ CONN_STR = "Driver=...;Server=192.168.59.230;..."
│  │
│  ├─ database.py                  # 🗄️  Capa de Datos
│  │  └─ class DataManager:
│  │     ├─ _get_connection()       # Manejo conexión ODBC
│  │     ├─ get_entregas()          # SELECT entregas por admisión
│  │     └─ get_datos_completos()   # SELECT header, meds, firma
│  │
│  ├─ report_gen.py                # 📄 Generador PDF
│  │  └─ class ReportGenerator:
│  │     ├─ __init__(callback)      # Inicializar con callback UI
│  │     ├─ build()                 # Main: Word→Jinja2→PDF
│  │     ├─ _is_file_locked()       # ✨ Detectar PDF abierto
│  │     ├─ _check_pdf_exists_and_locked()  # ✨ Validar salida
│  │     ├─ _wait_for_file_release()        # ✨ Esperar liberación
│  │     ├─ _cleanup_temp_file()           # ✨ Limpiar temporal
│  │     └─ _log_progress()         # Emitir estado a GUI
│  │
│  └─ main.py                      # 🖥️  Interfaz PyQt6
│     ├─ class AppFarmacia(QMainWindow):
│     │  ├─ setup_ui()              # Construir widgets
│     │  ├─ cargar_entregas()       # Buscar en BD
│     │  ├─ generar()               # Iniciar worker
│     │  ├─ _on_progress()          # Callback: updates
│     │  ├─ _on_success()           # Callback: PDF generado
│     │  ├─ _on_error()             # Callback: error
│     │  └─ _reset_buttons()        # Re-habilitar UI
│     │
│     ├─ class PDFWorker(Thread):   # ✨ Threading
│     │  ├─ run()                   # Ejecuta en thread separado
│     │  └─ signals.progress/finished/error  # Comunicación
│     │
│     └─ class WorkerSignals(QObject):
│        ├─ progress = pyqtSignal(str)      # "Cargando..."
│        ├─ finished = pyqtSignal(str)      # PDF generado
│        └─ error = pyqtSignal(str)         # Error message
│
├─ 📋 PLANTILLA
│  └─ ACTA_MEDICAMENTOS.docx       # Plantilla Jinja2 Word
│     ├─ Variables: {{ hc }}, {{ paciente }}, {{ doc_id }}, ...
│     ├─ Tabla dinámica: {% for m in medicamentos %}...{% endfor %}
│     └─ Firma: {{ firma_paciente }} (InlineImage)
│
├─ ⚙️  CONFIGURACIÓN
│  ├─ requirements.txt              # Dependencias versionadas
│  │  ├─ PyQt6>=6.6.0
│  │  ├─ pyodbc>=5.0.0
│  │  ├─ docxtpl>=0.16.0
│  │  └─ docx2pdf>=1.3.0
│  │
│  ├─ .env.example                  # Template variables entorno
│  │  ├─ SQL_SERVER=192.168.59.230
│  │  ├─ SQL_USER=ConexionSistemas
│  │  ├─ SQL_PASSWORD=...
│  │  └─ DEBUG=False
│  │
│  ├─ .gitignore                    # Archivos no versionados ⚠️
│  │  ├─ config.py                  (credenciales privadas)
│  │  ├─ .env                       (secretos)
│  │  ├─ temp_*.docx                (temporales)
│  │  ├─ *.log                      (debug)
│  │  └─ venv/                      (entorno local)
│  │
│  ├─ pyproject.toml                (futuro: configuración setuptools)
│  └─ setup.py                      (futuro: instalación como paquete)
│
├─ 📚 DOCUMENTACIÓN
│  ├─ INDEX.md                      # 🗺️  Guía de navegación
│  │
│  ├─ QUICKSTART.md                 # ⚡ 5 minutos para ejecutar
│  │  └─ Para usuarios con todo instalado
│  │
│  ├─ INSTALL.md                   # 📦 Instalación paso a paso
│  │  └─ Verificar requisitos, pip install, config
│  │
│  ├─ README.md                    # 📖 Guía completa
│  │  ├─ Descripción general
│  │  ├─ Stack técnico
│  │  ├─ Uso (flujo usuario)
│  │  ├─ Variables contexto
│  │  ├─ Troubleshooting
│  │  └─ FAQ
│  │
│  ├─ TROUBLESHOOTING.md           # 🆘 Solución problemas
│  │  ├─ Problemas conexión SQL
│  │  ├─ Problemas Word/PDF
│  │  ├─ Problemas GUI
│  │  ├─ Scripts diagnóstico
│  │  └─ Test unitarios
│  │
│  ├─ ARCHITECTURE.md              # 🏗️  Diseño técnico (devs)
│  │  ├─ 3 capas: GUI / Business / Data
│  │  ├─ Flujo end-to-end con diagramas
│  │  ├─ Extensiones (agregar campos)
│  │  ├─ Performance tips
│  │  └─ Testing
│  │
│  ├─ CHANGELOG.md                 # 📝 Historial v1.0→v2.0
│  │  ├─ ✨ Agregado (5 features)
│  │  ├─ 🔧 Cambiado (refactoring)
│  │  ├─ 🐛 Arreglado (4 bugs)
│  │  └─ 📚 Documentación (8 nuevos docs)
│  │
│  ├─ RESUMEN_CAMBIOS.md           # ✅ Resumen ejecutivo
│  │  └─ Todos los objetivos completados
│  │
│  └─ ARCHITECTURE.md              # 🏗️  Para desarrolladores
│     └─ Cómo extender el sistema
│
├─ 📁 DIRECTORIOS
│  ├─ venv/                        # 🐍 Entorno virtual Python
│  │  ├─ Scripts/
│  │  │  ├─ python.exe
│  │  │  ├─ pip.exe
│  │  │  └─ Activate.ps1
│  │  ├─ Lib/
│  │  │  └─ site-packages/
│  │  │     ├─ PyQt6/
│  │  │     ├─ pyodbc/
│  │  │     ├─ docxtpl/
│  │  │     └─ docx2pdf/
│  │  └─ pyvenv.cfg
│  │
│  ├─ __pycache__/                # 🔄 Cache compilado Python
│  │  ├─ config.cpython-312.pyc
│  │  ├─ database.cpython-312.pyc
│  │  ├─ report_gen.cpython-312.pyc
│  │  └─ main.cpython-312.pyc
│  │
│  └─ templates/                  # 📋 (Opcional) Plantillas adicionales
│     ├─ ACTA_MEDICAMENTOS_tableta.docx  (futuro: variante mobile)
│     └─ ACTA_MEDICAMENTOS_english.docx  (futuro: inglés)
│
├─ 📊 ARCHIVOS GENERADOS (en ejecución)
│  ├─ Acta_Entrega_*.pdf          # PDFs generados (salida)
│  ├─ temp_*.docx                 # Temporales Word (se limpian)
│  ├─ app.log                      # Debug (futuro: logging)
│  └─ Actas.db                     # Caché BD (futuro: SQLite cache)
│
└─ 📋 ROOT FILES
   ├─ LICENSE                      # (futuro) Licencia Red Medicron
   ├─ MANIFEST.in                  # (futuro) Qué incluir en distribución
   ├─ setup.py                     # (futuro) Para 'pip install'
   └─ Makefile                     # (futuro) Automatización: make test, make build
```

---

## 🔀 Flujo de Datos Completo

```
USUARIO
   │
   ├─ Escribe admisión "54321"
   ├─ Click "🔍 Buscar"
   │  │
   │  └─→ main.py: cargar_entregas()
   │      │
   │      ├─→ database.py: get_entregas(54321)
   │      │  │
   │      │  └─→ SQL Server
   │      │     SELECT numeroEntrega, fechaEntrega
   │      │     FROM DispensacionFarmaciaPGP
   │      │     WHERE IdAdmision = 54321
   │      │
   │      └─→ Retorna: [(1, "2024-03-01"), (2, "2024-03-05")]
   │         │
   │         └─→ main.py: tabla.insertRow()
   │            Tabla muestra:
   │            ┌──────────────────────┐
   │            │ Nº │ Fecha            │
   │            │ 1  │ 2024-03-01      │
   │            │ 2  │ 2024-03-05      │
   │            └──────────────────────┘
   │
   ├─ Selecciona fila 1
   ├─ Click "🖨️ Generar e Imprimir"
   │  │
   │  └─→ main.py: generar()
   │      │
   │      ├─ Mostrar: progress_bar, status_label
   │      ├─ Deshabilitar: botones, tabla
   │      │
   │      └─→ PDFWorker.start() ← NUEVO THREAD
   │         │
   │         ├─→ Emit: progress("Obteniendo datos...")
   │         │   │
   │         │   └─→ main._on_progress() → status_label updates
   │         │
   │         ├─→ database.py: get_datos_completos(54321, 1)
   │         │  │
   │         │  ├─→ Query 1: Header (paciente, funcionario, etc)
   │         │  ├─→ Query 2: Medicamentos (entregados vs formulados)
   │         │  └─→ Query 3: Firma (bytes binarios)
   │         │     │
   │         │     └─→ Retorna: (header, meds, firma)
   │         │
   │         ├─→ Emit: progress("Generando acta...")
   │         │
   │         ├─→ report_gen.py: build(header, meds, firma, 1)
   │         │  │
   │         │  ├─ Validar: PDF_anterior no está abierto
   │         │  ├─ Cargar: plantilla ACTA_MEDICAMENTOS.docx
   │         │  ├─ Procesar: firma binaria → InlineImage
   │         │  ├─ Mapear: contexto con variables
   │         │  ├─ Renderizar: Jinja2
   │         │  ├─ Guardar: temp_1.docx
   │         │  │
   │         │  ├─→ Emit: progress("Convirtiendo a PDF...")
   │         │  │
   │         │  ├─ Convertir: docx2pdf (Word)
   │         │  │  └─→ convert(temp_1.docx, Acta_1.pdf)
   │         │  │
   │         │  └─→ Finally: limpiar temp_1.docx
   │         │     │
   │         │     └─→ Retorna: "Acta_1.pdf"
   │         │
   │         ├─→ Emit: progress("Abriendo PDF...")
   │         ├─→ os.startfile("Acta_1.pdf")  ← Abre automáticamente
   │         │
   │         └─→ Emit: finished("Acta_1.pdf")
   │            │
   │            └─→ main._on_success()
   │               ├─ progress_bar.hide()
   │               ├─ QMessageBox.info("✓ Éxito")
   │               ├─ status_label.setText("✓ PDF generado")
   │               └─ _reset_buttons()
   │
   └─ PDF abierto en lector (Adobe Reader, Edge, etc)
      Archivo: C:\Proyectos\SistemaFarmacia\Acta_1.pdf
```

---

## 🛠️ Tecnologías por Capa

```
┌────────────────────────────────────────────────┐
│ PRESENTACIÓN (GUI)                             │
├────────────────────────────────────────────────┤
│ PyQt6 6.6+                                    │
│ ├─ QMainWindow, QWidget                       │
│ ├─ QLineEdit, QPushButton, QTableWidget       │
│ ├─ QProgressBar, QLabel                       │
│ ├─ QMessageBox, QDialog                       │
│ └─ Threading (QThread, pyqtSignal)            │
└────────────────────────────────────────────────┘
           ↓ (Datos + Callbacks)
┌────────────────────────────────────────────────┐
│ LÓGICA DE NEGOCIO                              │
├────────────────────────────────────────────────┤
│ python-docx 0.8.11                            │
│ ├─ Lectura: DocxTemplate                      │
│ └─ Edición: renderizado con Jinja2            │
│                                                │
│ docx2pdf 1.3+                                 │
│ └─ Conversión: Word (COM) → PDF               │
│                                                │
│ io.BytesIO                                    │
│ └─ Firma: binario (BD) → imagen incrustada    │
│                                                │
│ Validaciones:                                  │
│ ├─ Archivo abierto (open + IOError)           │
│ ├─ Manejo try-finally                         │
│ └─ Callbacks para UI                          │
└────────────────────────────────────────────────┘
           ↓ (SQL + Parámetros)
┌────────────────────────────────────────────────┐
│ DATOS                                          │
├────────────────────────────────────────────────┤
│ pyodbc 5.0+                                   │
│ ├─ ODBC Driver: SQL Server Native Client 11.0 │
│ ├─ Puerto: 1433 (default)                     │
│ └─ Auth: UID/PWD en CONN_STR                  │
│                                                │
│ SQL Server 2016+                              │
│ ├─ Base: SIFacturacion                        │
│ │  ├─ mPacientes (datos maestros)             │
│ │  ├─ mAdmisiones (puente)                    │
│ │  ├─ cAdministracion (sedes)                 │
│ │  └─ dHCOrdenesExternas (órdenes médico)     │
│ │                                              │
│ └─ Base: RedMedicronIPS                       │
│    ├─ DispensacionFarmaciaPGP (entregas)      │
│    ├─ DispensacionFarmaciaPGPFirmaRecibido    │
│    └─ GeneralesUsuario (farmacéuticos)        │
│                                                │
│ Características:                               │
│ ├─ Parámetros SQL (prevents injection)        │
│ ├─ RTRIM + ISNULL (manejo nulos)              │
│ ├─ JOINs inteligentes (puente mAdmisiones)    │
│ └─ Errores ODBC específicos (28000, 08001)    │
└────────────────────────────────────────────────┘
```

---

## 📈 Ciclo de Vida de una Generación

```
Estado                  Componente              UI Visual
──────────────────────────────────────────────────────────
1. Idle                 Main thread            Botones habilitados
                        All systems ready      Status: vacío

2. Click "Generar"      main.generar()         Button: disabled
   Comienza             Deshabilita UI         ProgressBar: visible
                        PDFWorker.start()      Label: "Procesando..."

3. Conectando BD        PDFWorker.run()        Label: "Conectando BD"
                        database.get_()        ProgressBar: animada

4. Obteniendo datos     DataManager            Label: "Buscando..."
                        3 queries SQL

5. Cargando plantilla   report_gen.build()     Label: "Cargando template"
                        DocxTemplate(path)

6. Procesando firma     BytesIO → InlineImage  Label: "Firma..."

7. Renderizando         Jinja2 context         Label: "Renderizando"
                        doc.render(context)

8. Convirtiendo         docx2pdf convert()     Label: "Convirtiendo..."
                        (LENTO: 2-3s)

9. Limpiando            finally block          Label: "Limpiando..."
                        cleanup_temp_file()

10. Abriendo            os.startfile()         PDF en lector

11. Finalizando         Emit: finished         ProgressBar: hidden
                        _on_success()          Button: enabled
                                               Label: "✓ Éxito"
                                               MessageBox: OK

Error en algún paso     Emit: error            All buttons: enabled
                        _on_error()            Label: "❌ ERROR"
                                               MessageBox: Error detail
```

---

## 🔍 Mapa de Responsabilidades

```
┌─────────────────────────────────────────────────────────┐
│                    USUARIO                              │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ main.py (AppFarmacia GUI)                               │
│ ✓ Mostrar interfaz                                      │
│ ✓ Capturar eventos (clicks, Enter)                      │
│ ✓ Validación entrada usuario                            │
│ ✓ Threading (PDFWorker.start())                         │
│ ✓ Callbacks (progress, success, error)                  │
│ ✓ Actualizar widgets (label, progressbar, tabla)        │
│ ✓ Mostrar diálogos (QMessageBox)                        │
│ ✗ NO hace: Queries SQL directas, conversión PDF         │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                                     │
┌───────▼────────────────┐         ┌────────▼────────────────┐
│ database.py (DataMgr)  │         │ report_gen.py (GenRep)  │
│ ✓ Conexión ODBC        │         │ ✓ Cargar plantilla      │
│ ✓ Queries SQL          │         │ ✓ Mapear variables      │
│ ✓ Error handling ODBC  │         │ ✓ Renderizar Jinja2     │
│ ✓ Retornar datos       │         │ ✓ Convertir Word→PDF    │
│ ✓ Abstraer base datos  │         │ ✓ Validar archivos      │
│ ✗ NO hace: PDFs        │         │ ✓ Limpiar temporales    │
│                        │         │ ✓ Callbacks de progreso │
│                        │         │ ✗ NO hace: UI, BD       │
└─────────┬──────────────┘         └────────┬────────────────┘
          │                                 │
          └─────────────┬───────────────────┘
                        │
          ┌─────────────▼────────────────────┐
          │ config.py (Configuración)       │
          │ - CONN_STR (credenciales)       │
          │ - Constantes globales           │
          └─────────────────────────────────┘
```

---

**Diagrama actualizado**: Marzo 2026  
**Versión**: 2.0.0  
**Estado**: ✅ Completo y funcional
