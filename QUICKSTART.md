# ⚡ Quick Start - 5 Minutos para Usar

Si ya tienes Python y Word instalados, este es el camino más rápido.

---

## 1️⃣ Preparación (1 minuto)

```powershell
# Abrir PowerShell
# Navegar a carpeta del proyecto
cd "C:\Proyectos\SistemaFarmacia"

# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\Activate.ps1
```

---

## 2️⃣ Instalar (2 minutos)

```powershell
pip install -r requirements.txt
```

---

## 3️⃣ Configurar (1 minuto)

Edita `config.py` con tus credenciales SQL (cambiar IP, usuario, password):

```python
CONN_STR = (
    "Driver={SQL Server};"
    "Server=192.168.59.230;"      # ← IP del servidor SQL
    "Database=sifacturacion;"
    "UID=ConexionSistemas;"        # ← Tu usuario
    "PWD=SI.Admin.23$%*;"          # ← Tu contraseña
)
```

---

## 4️⃣ Ejecutar (1 minuto)

```powershell
python main.py
```

Se abre la ventana → Escribe admisión → Click "Buscar" → Click "Generar PDF"

---

## ✅ Listo

¡Eso es todo! PDF se genera automáticamente.

---

**Para más detalles**: Ver [README.md](README.md) o [INSTALL.md](INSTALL.md)
