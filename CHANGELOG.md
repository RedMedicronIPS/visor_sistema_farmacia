# CHANGELOG - Sistema de Generación de Actas de Entrega

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [2.0.0] - Marzo 2026 ⭐ RELEASE ACTUAL

### ✨ Agregado

#### report_gen.py - Generador de Reportes Mejorado

1. **Validación de Archivos Abiertos**
   - Nueva función `_is_file_locked()`: Verifica si un PDF está abierto antes de generarlo
   - Nueva función `_check_pdf_exists_and_locked()`: Evita generar si PDF ya existe y está abierto
   - Error amigable: "El PDF 'Acta_Entrega_123.pdf' está abierto. Ciérrelo antes..."
   - **Beneficio**: Previene crashes inesperados y errores COM

2. **Manejo Robusto de Excepciones COM**
   - Try-except específico para `docx2pdf` (errores COM de Word)
   - Detecta y traduce errores genéricos de COM a mensajes útiles:
     ```
     Error COM (Microsoft Word):
     • Microsoft Word no está instalado
     • Hay una instancia de Word bloqueada
     • Problemas de permisos en el sistema de archivos
     ```
   - **Beneficio**: Usuario entiende qué falló sin código técnico

3. **Limpieza Automática con Try-Finally**
   - Bloque `finally` garantiza eliminación de `temp_*.docx` incluso si hay excepciones
   - Función `_wait_for_file_release()`: Espera a que archivo temporal se libere
   - Función `_cleanup_temp_file()`: Limpieza robusta con reintentos
   - **Beneficio**: Ahorra espacio disco, no quedan huérfanos `temp_*.docx`

4. **Sistema de Callbacks de Progreso**
   - Nuevo parámetro `progress_callback` en constructor
   - Función `_log_progress()`: Emite mensajes de estado en tiempo real
   - Mensajes informan: Validación → Carga Plantilla → Procesamiento Firma → Renderizado → Conversión
   - **Beneficio**: GUI responde con actualizaciones de estado durante proceso lento

5. **Documentación Exhaustiva**
   - Docstrings detallados para cada método
   - Secciones "Returns", "Raises", "Args" en formato Google
   - Explicación de excepciones específicas levantadas
   - **Beneficio**: Código auto-documentado, fácil de mantener

#### main.py - Interfaz PyQt6 Completamente Refactorizada

1. **Threading para Operaciones No-Bloqueantes**
   - Nueva clase `PDFWorker(Thread)`: Genera PDF en hilo separado
   - Nueva clase `WorkerSignals(QObject)`: Emite 3 señales:
     - `progress`: Actualiza barra de progreso
     - `finished`: PDF generado exitosamente
     - `error`: Error durante generación
   - **Beneficio**: Interfaz responsiva, no se congela mientras se genera PDF

2. **Progress Bar Indeterminado**
   - Barra de progreso con `setRange(0, 0)` (animación)
   - Se muestra solo durante generación
   - Se oculta al finalizar (éxito o error)
   - **Beneficio**: Feedback visual que proceso está en marcha

3. **Indicador de Estado Dinámico**
   - Label con estado en tiempo real
   - Emojis para claridad: 🔍 🖨️ ✓ ❌ ⚠️
   - Ejemplos:
     ```
     🔍 Buscando entregas...
     ✓ Se encontraron 3 entrega(s)
     ✓ PDF generado: Acta_Entrega_123.pdf
     ❌ Error al generar PDF
     ```
   - **Beneficio**: Usuario siempre sabe qué está pasando

4. **Cuadros de Diálogo (QMessageBox) para Errores**
   - `QMessageBox.warning()` para validaciones
   - `QMessageBox.information()` para resultados sin datos
   - `QMessageBox.critical()` para errores graves
   - Mensajes contextualizados:
     ```
     ❌ Error de Conexión
     Verifique que el servidor SQL Server esté disponible en 192.168.59.230
     ```
   - **Beneficio**: Usuario entiende error y cómo solucionarlo

5. **Mejoras UX**
   - Entrada permite buscar presionando Enter (no solo botón)
   - Si hay 1 sola entrega, se auto-selecciona
   - Botones deshabilitados durante procesamiento (evita clicks accidentales)
   - Iconos emoji en botones: 🔍 Buscar, 🖨️ Imprimir
   - Tabla con columnas mas anchas y mejor espaciado
   - Título de ventana descriptivo: "Generador de Actas de Entrega - Red Medicron IPS"
   - Validación de selección antes de generar

6. **Manejo de Excepciones Granular**
   - Try-except en `cargar_entregas()` para errores conexión
   - Try-except en `PDFWorker.run()` diferenciando:
     - `PermissionError`: Permisos o archivo bloqueado
     - `FileNotFoundError`: Plantilla ausente
     - `Exception`: Otros errores COM, BD, etc.
   - Cada tipo de error muestra mensaje específico
   - **Beneficio**: Debugging más fácil, errores informativos

#### database.py - Gestor de Datos Mejorado

1. **Sistema de Conexión Robusto**
   - Nuevo método `_get_connection()`: Encapsula conexión con errores específicos
   - Detecta 3 tipos de errores ODBC:
     ```
     28000 → Error de autenticación (usuario/contraseña)
     08001 → Error de conexión (servidor no disponible)
     Otros → Problemas genéricos de conexión
     ```
   - Mensajes de error traducen códigos ODBC a español
   - **Beneficio**: Usuario sabe exactamente qué configurar

2. **Validación de Consultas SQL**
   - Nueva validación en `get_entregas()`: Retorna `[]` si no hay resultados
   - Detecta errores de columnas no válidas en tablas
   - **Beneficio**: No revientas con excepciones silenciosas

3. **Documentación de Consultas**
   - Docstrings explicando cada parámetro
   - Secciones "Returns", "Raises" detalladas
   - Notas sobre estructura datos que retorna
   - **Beneficio**: Fácil usar los métodos sin leer SQL

4. **Handles Nulos y Vacíos**
   - `ISNULL()` y `RTRIM()` en concatenación de paciente
   - Manejo de firmas ausentes (puede ser None)
   - Orden medicamentos por `nomSuministro` (consistencia)
   - **Beneficio**: Menos errores por datos incompletos en BD

#### requirements.txt - Dependencias Versionadas

- Especifica versiones mínimas de cada paquete
- Asegura compatibilidad con Python 3.12+
- Documentación clara sobre dependencias opcionales

#### Nuevo: README.md - Documentación Completa

- 500+ líneas de documentación
- Secciones:
  - Descripción general del proyecto
  - Instalación paso a paso
  - Configuración (incluyendo variables de entorno)
  - Guía de uso (flujo de usuario)
  - Arquitectura y diagrama de datos
  - Variables contexto para plantilla Word
  - Solución de problemas (7 escenarios comunes)
  - Consideraciones de seguridad
  - Mejoras futuras
  - Historial de cambios

#### Nuevo: TROUBLESHOOTING.md - Guía de Diagnóstico

- Checklist y soluciones para 10+ problemas comunes
- Scripts de test para verificar conexión SQL
- Comandos ODBC para diagnosticar drivers
- Verificación de permisos SQL Server
- Test firewall y conectividad red
- Debugging de plantilla Word y Jinja2
- Script de test unitario manual

#### Nuevo: .env.example - Variables de Entorno

- Ejemplo de archivo `.env` para credenciales
- Instrucciones de uso
- Seguridad: NO commitear `.env` a git

#### Nuevo: .gitignore - Protección de Repositorio

- Ignora `config.py` (con credenciales) ⚠️
- Ignora archivos temporales: `temp_*.docx`
- Ignora PDFs generados: `Acta_Entrega_*.pdf`
- Ignora `.env`, `*.log`, `*.db`
- Ignora IDE/Sistema: `.vscode/`, `.idea/`, `__pycache__/`

### 🔧 Cambiado

#### report_gen.py
- **Antes**: Excepción genérica en conversión COM
- **Ahora**: Traducción de errores COM a español con causas y soluciones

- **Antes**: Eliminación fija de `temp_*.docx` (podría fallar)
- **Ahora**: Limpieza con reintentos y logging

- **Antes**: Constructor sin parámetros
- **Ahora**: Acepta `progress_callback` para conectar con GUI

#### main.py
- **Antes**: Operación bloqueante (convert genera PDF, GUI congela)
- **Ahora**: Threading con `PDFWorker`, GUI responsiva

- **Antes**: Sin feedback de progreso
- **Ahora**: Progress bar + status label con actualizaciones en tiempo real

- **Antes**: Print() solamente en consola
- **Ahora**: `QMessageBox` con errores claros para usuario

- **Antes**: Botones siempre habilitados (peligro de clicks múltiples)
- **Ahora**: Deshabilitar durante procesamiento, re-habilitar después

#### database.py
- **Antes**: Conexión con try-except genérico
- **Ahora**: Especifico para cada código error ODBC (28000, 08001, etc.)

- **Antes**: Sin validación si datos existen
- **Ahora**: Retorna lista vacía `[]` si no hay entregas

### 🐛 Arreglado

1. **Error COM "pywintypes.com_error"**
   - Wrapped en try-except con mensaje interpretable
   - Sugiere instalar Word si es necesario

2. **Archivo "file already exists" no se puede sobrescribir**
   - Verifica si PDF está abierto antes de generar
   - Intenta eliminar PDF anterior si está cerrado

3. **Archivo temporal `temp_*.docx` quedan huérfanos**
   - Bloque `finally` garantiza limpieza
   - Reintentos si archivo está bloqueado

4. **GUI se cuelga durante conversión (3-5 segundos)**
   - Threading con `PDFWorker` permite actualizar UI
   - Sin bloqueos, usuario puede cancelar si quiere

5. **Errores de conexión congelas la GUI**
   - Errores de DB capturados en `PDFWorker.run()`
   - Se emiten como `signals.error` sin bloquear

6. **Mensajes de error técnicos sin contexto**
   - Todos los errores ahora tienen msg español + solución

### 📚 Documentación

- Documentación completa: README.md (500+ líneas)
- Guía de troubleshooting: TROUBLESHOOTING.md (300+ líneas)
- Inline docstrings en código (Google style)
- Ejemplos de conexión SQL y test
- Matriz de errores y soluciones

---

## [1.0.0] - Anterior

### ✨ Agregado

- Interfaz básica PyQt6 con búsqueda y tabla
- Conexión a SQL Server (SIFacturacion, RedMedicronIPS)
- Generación de Word con docxtpl (Jinja2)
- Conversión a PDF con docx2pdf
- Autura de firma digital (InlineImage)
- Abrir PDF automático al terminar

### ⚠️ Conocidos Limitaciones v1.0.0

- GUI bloqueada durante conversión PDF
- Sin manejo específico de errores COM
- Sin validación de archivo PDF abierto
- Archivos temporales no se limpian si error
- Mensajes de error técnicos sin contexto
- Sin indicador de progreso

---

## Referencias de Cambio

Para cada sección utiliza emojis:
- ✨ Agregado: nuevas características
- 🔧 Cambiado: cambios en funcionalidad existente
- 🐛 Arreglado: bugs resueltos
- 🚀 Performance: mejoras de rendimiento
- ⚠️ Deprecated: será removido próximamente
- 🔒 Security: arreglos de seguridad
- 📚 Documentación: cambios en docs

---

**Última actualización**: Marzo 5, 2026  
**Mantenedor**: Red Medicron IPS  
**Estado**: ✅ Stable / Production Ready
