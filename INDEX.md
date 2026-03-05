# 📚 Documentación Completa - Índice

Bienvenido a la documentación del Sistema de Generación de Actas de Entrega de Red Medicron IPS.

Selecciona el documento según tu necesidad:

---

## 🎯 Por Rol/Necesidad

### 👨‍💼 Si eres Usuario (Farmacéutico/Administrativo)

Necesitas **usar** la aplicación:

1. **[QUICKSTART.md](QUICKSTART.md)** ⚡
   - 5 minutos para ejecutar
   - Paso a paso simple si todo ya está instalado
   - **Comenzar aquí si es tu primer uso**

2. **[INSTALL.md](INSTALL.md)** 📦
   - Instalación completa desde cero
   - Verificación de requisitos
   - Troubleshooting de instalación
   - Acceso directo en Windows

3. **[README.md](README.md)** 📖
   - Guía de uso completa (flujo de usuario)
   - Variables de contexto en plantilla
   - Soluciones a problemas comunes
   - Preguntas frecuentes

4. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** 🆘
   - Diagnóstico de errores
   - Checklists de verificación
   - Scripts de test
   - Soluciones detalladas para cada error

---

### 👨‍💻 Si eres Desarrollador (Mantenencia/Extensión)

Necesitas **entender o modificar** el código:

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** 🏗️
   - Diseño de 3 capas (GUI, Business Logic, Data)
   - Flujo de datos end-to-end
   - Diagramas ASCII de interacción
   - Cómo agregar features

2. **Código fuente con docstrings**:
   - [config.py](config.py) - Configuración simple
   - [database.py](database.py) - Queries SQL con manejo errores
   - [report_gen.py](report_gen.py) - Procesamiento Word/PDF
   - [main.py](main.py) - UI con threading

3. **[CHANGELOG.md](CHANGELOG.md)** 📝
   - Cada cambio de v1.0 → v2.0
   - Qué se mejoró
   - Por qué se mejoraron

---

### 🚀 Si estás configurando por primera vez

Seguir este orden:

1. Leer [QUICKSTART.md](QUICKSTART.md) (análisis rápido)
2. Si necesitas detalle → [INSTALL.md](INSTALL.md)
3. Para troubleshooting → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. Para entender el código → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📄 Documentos Disponibles

| Documento | Propósito | Audiencia | Tiempo Lectura |
|-----------|-----------|-----------|----------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Ejecutar en 5 min | Todo el mundo | 5 min |
| **[INSTALL.md](INSTALL.md)** | Instalación paso a paso | Nuevos usuarios | 15-20 min |
| **[README.md](README.md)** | Guía completa + uso | Usuarios | 20-30 min |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Solucionar errores | Usuarios con problemas | 10-30 min (según error) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Diseño técnico | Desarrolladores | 30-40 min |
| **[CHANGELOG.md](CHANGELOG.md)** | Historial cambios | QA/Desarrolladores | 10-15 min |
| **[.env.example](.env.example)** | Variables de entorno | DevOps/Admin | 2 min |
| **[.gitignore](.gitignore)** | Control de versión | Desarrolladores | 1 min |
| **[requirements.txt](requirements.txt)** | Dependencias Python | Desarrolladores | 1 min |

---

## 🗂️ Estructura Proyecto

```
SistemaFarmacia/
│
├── 📄 Archivo de Código
├── config.py                    # Credenciales SQL Server
├── database.py                  # Consultas SQL + DataManager
├── report_gen.py               # Generación Word→PDF
├── main.py                      # Interfaz PyQt6
│
├── 📋 Plantilla
├── ACTA_MEDICAMENTOS.docx      # Plantilla Word (Jinja2)
│
├── 📦 Configuración
├── requirements.txt             # Dependencias Python
├── .env.example                 # Variables de entorno (template)
├── .gitignore                   # Archivos no versionados
│
├── 📚 Documentación
├── README.md                    # Guía principal
├── INSTALL.md                  # Instalación paso a paso
├── QUICKSTART.md               # 5 minutos para ejecutar
├── TROUBLESHOOTING.md          # Solución de problemas
├── ARCHITECTURE.md             # Diseño técnico
├── CHANGELOG.md                # Historial de cambios
├── INDEX.md                    # Este archivo
│
├── 📁 Directorios
├── venv/                        # Entorno virtual Python
├── __pycache__/                 # Cache compilado
└── templates/                   # (Opcional) Plantillas adicionales
```

---

## 🚨 Errores Comunes y Dónde Buscar Solución

| Error | Dónde Buscar | Documento |
|-------|-------------|-----------|
| "Python no reconocido" | Paso 1 de instalación | [INSTALL.md](INSTALL.md#problema-python-no-reconocido) |
| "No se puede conectar a BD" | Validación conexión | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#síntoma-2-servidor-sql-server-no-disponible) |
| "Word no está instalado" | Requisitos previos | [INSTALL.md](INSTALL.md#problema-microsoft-word-no-está-instalado) |
| "PDF está abierto" | Cerrar lector PDF | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#síntoma-2-el-pdf-está-abierto) |
| "Plantilla no encontrada" | Copiar archivo | [TROUBLESHOOTING.md](TROUBLESHOOTING.md#síntoma-3-plantilla-acta_medicamentosdocx-no-encontrada) |
| "¿Cómo agregar un campo nuevo?" | Entender arquitectura | [ARCHITECTURE.md](ARCHITECTURE.md#extensiones-comunes) |

---

## 📞 Guía de Contacto por Tipo de Problema

**Problema de Instalación**
→ Leer [INSTALL.md](INSTALL.md) → TROUBLESHOOTING.md

**Problema de Uso**
→ Leer [README.md](README.md) → TROUBLESHOOTING.md

**Problema Técnico/Desarrollo**
→ Leer [ARCHITECTURE.md](ARCHITECTURE.md) → código fuente

**Necesito extender funcionalidad**
→ [ARCHITECTURE.md](ARCHITECTURE.md#extensiones-comunes)

**Algo no funciona después de actualizar**
→ [CHANGELOG.md](CHANGELOG.md) para ver qué cambió

---

## 🔄 Flujo Recomendado de Lectura

### Primer Uso (Usuario)
```
QUICKSTART (5 min) 
    ↓ Si funciona ✓
  Listo, usar directamente
    ↓ Si falla ✗
INSTALL (detalle de error)
    ↓
TROUBLESHOOTING (solucionar)
    ↓ ✓
Usar normalmente
```

### Configuración Nueva (Admin/DevOps)
```
INSTALL (paso a paso completo)
    ↓
.env.example (configurar credenciales)
    ↓
config.py (actualizar valores)
    ↓
TROUBLESHOOTING (test de conexión)
    ↓ ✓
README (explicar a usuarios)
```

### Desarrollo/Mantenimiento
```
README (entender qué hace)
    ↓
ARCHITECTURE (cómo está estructurado)
    ↓
Código fuente con docstrings
    ↓
CHANGELOG (qué cambió últimamente)
    ↓
Modificar/extender según necesidad
```

---

## ✨ Versión Actual

- **Versión**: 2.0.0 (Estable)
- **Lanzamiento**: Marzo 2026
- **Estado**: Production-Ready ✓
- **Python**: 3.12+ requerido
- **Licencia**: Propiedad de Red Medicron IPS

---

## 🎓 Conceptos Clave

### Threading (No-Blocking)
- GUI no se congela durante generación PDF
- Usa `PDFWorker` en hilo separado
- Comunicación via PyQt Signals

### Validación de Archivos
- Verifica si PDF está abierto antes de sobrescribir
- Espera a que archivo temporal se libere
- Limpieza robusta même en caso de error

### Manejo de Excepciones
- Erros COM traducidos a español
- Errores ODBC con códigos específicos
- Mensajes amigables para usuario

### Variables de Entorno
- Credenciales en `.env` (nunca hardcodear)
- `config.py` lee desde `os.getenv()`
- Más seguro para producción

---

## 🔗 Enlaces Útiles

- **Repositorio**: [Git URL]
- **Issues/Bugs**: [GitHub Issues URL]
- **Wiki**: [Confluence o GitLab Wiki]
- **Contacto**: it@redmedicron.com

---

## 📅 Historial de Versiones

- **v2.0.0** (Actual) - Threading, validaciones, documentación
- **v1.0.0** - Versión inicial funcional

---

## 🤝 Contribuir

Para actualizar documentación o código:

1. Crear rama: `git checkout -b feature/descripcion`
2. Hacer cambios + tests
3. Commit con mensaje claro
4. Push + Pull Request
5. Revisar con equipo

---

**Última actualización**: Marzo 5, 2026

¿Necesitas ayuda? 👉 Comienza con [QUICKSTART.md](QUICKSTART.md) o [README.md](README.md)
