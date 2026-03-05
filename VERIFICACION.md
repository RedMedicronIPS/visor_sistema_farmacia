# ✔️ Checklist de Verificación - Sistema v2.0.0

**Fecha**: Marzo 5, 2026  
**Versión**: 2.0.0  
**Estado**: ✅ PRODUCCIÓN

Usa este checklist para verificar que el sistema está correctamente instalado y funcional.

---

## 📋 Fase 1: Requisitos (Ambiente)

- [ ] **Python 3.12+** instalado
  ```powershell
  python --version
  # Esperado: Python 3.12.x
  ```

- [ ] **Microsoft Word 2016+** instalado
  ```powershell
  where winword.exe
  # Esperado: C:\Program Files\...\WINWORD.EXE
  ```

- [ ] **SQL Server** disponible en 192.168.59.230
  ```powershell
  ping 192.168.59.230
  # Esperado: Respuesta OK
  ```

- [ ] **ODBC Driver 11.0 o 17+** instalado
  ```powershell
  Get-OdbcDriver | findstr "SQL"
  # Esperado: SQL Server, SQL Server Native Client, o ODBC Driver
  ```

**Resultado Fase 1**: ☐ Pasa / ☐ Falla

Si alguno falla → Ver [INSTALL.md](INSTALL.md)

---

## 📦 Fase 2: Instalación

- [ ] **Carpeta proyecto** en lugar correcto
  - ☐ `g:\Desarollo Red Medicron IPS\SistemaFarmacia\`

- [ ] **Entorno virtual creado**
  ```powershell
  Test-Path "venv\Scripts\Activate.ps1"
  # Esperado: True
  ```

- [ ] **Paquetes Python instalados**
  ```powershell
  pip show PyQt6 pyodbc docxtpl docx2pdf
  # Esperado: 4 paquetes encontrados
  ```

- [ ] **Plantilla Word existe**
  ```powershell
  Test-Path "ACTA_MEDICAMENTOS.docx"
  # Esperado: True (tamaño: ~100KB)
  ```

- [ ] **config.py actualizado**
  ```python
  # Abrir config.py y verificar:
  # - Server: Correcta IP
  # - Database: sifacturacion
  # - UID: Usuario correcto
  # - PWD: Contraseña correcta
  ```

**Resultado Fase 2**: ☐ Pasa / ☐ Falla

Si falla → Seguir [INSTALL.md](INSTALL.md#paso-a-paso) nuevamente

---

## 🔗 Fase 3: Conectividad

- [ ] **Conexión ODBC al SQL Server**
  ```powershell
  python -c "
  import pyodbc
  from config import CONN_STR
  try:
      conn = pyodbc.connect(CONN_STR)
      print('✓ Conexión exitosa')
      conn.close()
  except Exception as e:
      print(f'✗ Error: {e}')
  "
  # Esperado: ✓ Conexión exitosa
  ```

- [ ] **Base de datos accesible**
  ```sql
  -- Ejecutar en SQL Server Management Studio:
  SELECT COUNT(*) FROM sifacturacion..mPacientes
  SELECT COUNT(*) FROM RedMedicronIPS..DispensacionFarmaciaPGP
  -- Esperado: Ambas retornan números > 0
  ```

- [ ] **Query de entregas funciona**
  ```powershell
  python -c "
  from database import DataManager
  db = DataManager()
  entregas = db.get_entregas(54321)  # Cambiar por ID válido
  print(f'Entregas encontradas: {len(entregas)}')
  "
  # Esperado: 1+ entregas, sin errores
  ```

**Resultado Fase 3**: ☐ Pasa / ☐ Falla

Si falla → Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md#síntoma-2-servidor-sql-server-no-disponible)

---

## 🖥️ Fase 4: Interfaz Gráfica

- [ ] **Aplicación inicia sin errores**
  ```powershell
  python main.py
  # Esperado: Ventana se abre con título correcto
  ```

- [ ] **Ventana muestra componentes**
  - [ ] Campo de entrada "Escriba el número de admisión..."
  - [ ] Botón "🔍 Buscar Entregas"
  - [ ] Tabla vacía (0 filas)
  - [ ] Botón "🖨️ Generar e Imprimir PDF" (deshabilitado)

- [ ] **Búsqueda funciona**
  1. Escribir número de admisión válido
  2. Press Enter (o click Buscar)
  3. **Esperado**: Tabla se llena con entregas

- [ ] **Tabla muestra datos**
  - [ ] Columna "Nº Entrega" con números
  - [ ] Columna "Fecha Entrega" con fechas

- [ ] **Botón Generar se habilita**
  - [ ] Click en fila de tabla
  - [ ] **Esperado**: Botón "🖨️ Generar" se activa (habilitado)

**Resultado Fase 4**: ☐ Pasa / ☐ Falla

Si falla → Ver [README.md](README.md#guía-de-uso) para troubleshooting

---

## 📄 Fase 5: Generación de PDF

- [ ] **PDF se genera sin errores**
  1. Seleccionar entrega en tabla
  2. Click "🖨️ Generar e Imprimir PDF"
  3. **Esperado**: 
     - Progress bar aparece (animada)
     - Status label actualiza: "Validando...", "Cargando...", "Convirtiendo..."
     - Después 3-5 segundos: PDF abierto en lector

- [ ] **Archivo PDF se creó**
  ```powershell
  Get-ChildItem *.pdf | Where-Object {$_.Name -like "Acta_*"}
  # Esperado: 1+ archivos Acta_Entrega_*.pdf
  ```

- [ ] **Pdf contiene datos correctos**
  - [ ] Nombre paciente visible
  - [ ] Número admisión correcto
  - [ ] Tabla medicamentos con entregas
  - [ ] Firma digital (si existe)

- [ ] **Archivo temporal se limpió**
  ```powershell
  Get-ChildItem temp_*.docx
  # Esperado: Sin resultados (o lista vacía)
  ```

**Resultado Fase 5**: ☐ Pasa / ☐ Falla

Si falla → Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md#error-pdf-está-abierto)

---

## 🛡️ Fase 6: Manejo de Errores

**Test 1: Admisión inválida**
- [ ] Escribir número de admisión que no existe: 999999999
- [ ] Click Buscar
- **Esperado**: Mensaje "📄 Sin Resultados - No se encontraron entregas..."

**Test 2: Sin seleccionar entrega**
- [ ] Click "🖨️ Generar PDF" SIN seleccionar fila
- **Esperado**: Mensaje "⚠ Selección Requerida - Por favor seleccione una entrega"

**Test 3: PDF abierto anterior**
- [ ] Generar un PDF
- [ ] Abrir PDF en lector (Acta_1.pdf)
- [ ] Intentar generar MISMO PDF de nuevo
- **Esperado**: Mensaje "⚠ PDF está abierto. Ciérrelo antes..."

**Test 4: Cerrar y reintentar**
- [ ] Cerrar PDF (dejar abierto del test anterior)
- [ ] Click "Generar" de nuevo
- **Esperado**: Segundo PDF se genera sin problemas

**Test 5: Sin conexión SQL**
- [ ] Apagar/aislar SQL Server temporalmente
- [ ] Click "Buscar"
- **Esperado**: Mensaje "❌ Error de Conexión - Verifique servidor SQL..." (con detalles útiles)

**Resultado Fase 6**: ☐ Pasa (todos) / ☐ Falla (especificar cuál)

---

## 📚 Fase 7: Documentación

- [ ] **Archivos de documentación existen**
  ```powershell
  Get-ChildItem *.md
  # Esperado: 10+ archivos .md
  ```

- [ ] **Documentos principales accesibles**
  - [ ] README.md (existe)
  - [ ] INSTALL.md (existe)
  - [ ] QUICKSTART.md (existe)
  - [ ] TROUBLESHOOTING.md (existe)
  - [ ] ARCHITECTURE.md (existe)
  - [ ] INDEX.md (existe)

- [ ] **Pueden abrirse en editor**
  ```powershell
  notepad README.md
  # Esperado: Archivo se abre con contenido
  ```

**Resultado Fase 7**: ☐ Pasa / ☐ Falla

Si falta alguno → Regenerar desde documentación

---

## 🔒 Fase 8: Seguridad

- [ ] **.gitignore protege config.py**
  ```powershell
  Get-Content .gitignore | findstr "config.py"
  # Esperado: "config.py" está en .gitignore
  ```

- [ ] **config.py NO está en repositorio**
  ```powershell
  git status config.py 2>$null
  # Esperado: No aparece en cambios (si usa git)
  ```

- [ ] **.env.example NO tiene secretos**
  ```powershell
  Get-Content .env.example
  # Esperado: SQL_PASSWORD=... (SIN valor real)
  ```

**Resultado Fase 8**: ☐ Pasa / ☐ Falla

---

## 📊 Resumen Final

Completar según resultados:

```
FASE 1 (Requisitos):        ☐ PASA  ☐ FALLA
FASE 2 (Instalación):       ☐ PASA  ☐ FALLA
FASE 3 (Conectividad):      ☐ PASA  ☐ FALLA
FASE 4 (GUI):               ☐ PASA  ☐ FALLA
FASE 5 (PDF):               ☐ PASA  ☐ FALLA
FASE 6 (Errores):           ☐ PASA  ☐ FALLA
FASE 7 (Documentación):     ☐ PASA  ☐ FALLA
FASE 8 (Seguridad):         ☐ PASA  ☐ FALLA
─────────────────────────────────────────
ESTADO FINAL: ☐ LISTO PARA PRODUCCIÓN
              ☐ NECESITA AJUSTES
```

---

## ✅ Criterios de Aprobación

**Sistema está LISTO si**:
- ✅ Fases 1-7 todas PASAN
- ✅ Fase 8 (Seguridad) PASA o PARCIAL (si no usa git)
- ✅ Puede generar PDF sin errores
- ✅ Documentación accesible

**Sistema NECESITA TRABAJO si**:
- ❌ Cualquier fase crítica (1-5) FALLA
- ❌ Errores no capturados correctamente
- ❌ SQL Server no accesible

---

## 🆘 Si Falla Alguna Fase

| Fase | Problema | Solución |
|------|----------|----------|
| 1 | Python no instalado | [INSTALL.md - Python](INSTALL.md#problema-python-no-reconocido) |
| 1 | Word no existe | [INSTALL.md - Word](INSTALL.md#problema-microsoft-word-no-está-instalado) |
| 2 | pip install falla | [TROUBLESHOOTING.md - pyodbc](TROUBLESHOOTING.md) |
| 3 | SQL no conecta | [TROUBLESHOOTING.md - SQL](TROUBLESHOOTING.md#síntoma-2-servidor-sql-server-no-disponible) |
| 4 | Ventana no abre | [README.md - GUI](README.md) |
| 5 | PDF no se genera | [TROUBLESHOOTING.md - PDF](TROUBLESHOOTING.md#síntoma-3-plantilla-acta_medicamentosdocx-no-encontrada) |
| 6 | Errores mal formateados | Revisar [report_gen.py](report_gen.py) manejo excepciones |
| 7 | Documentación falta | Regenerar desde doc templates |
| 8 | Seguridad falla | Revisar [.gitignore](.gitignore) |

---

## 💾 Salvar Progreso

Después de completar el checklist:

```powershell
# Crear punto de restauración
git add -A
git commit -m "Sistema v2.0.0 verificación completada"

# Crear rama stable
git branch stable
git tag v2.0.0
```

---

## 📅 Próximos Pasos

1. ✅ Completar este checklist
2. ✅ Resolver cualquier FALLA
3. ✅ Informar al equipo que v2.0.0 está LISTO
4. ✅ Comenzar usar en PRODUCCIÓN
5. ✅ Monitorear logs por 1-2 semanas
6. ✅ Recopilar feedback para v2.1

---

**Fecha Verificación**: _________________  
**Verificado Por**: _________________  
**Estado Final**: ☐ PRODUCCIÓN ☐ DESARROLLO

---

**Documento**: Sistema de Actas de Entrega v2.0.0  
**Última actualización**: Marzo 5, 2026  
**Propósito**: Verificación pre-producción
