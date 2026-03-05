import sys
import os
from threading import Thread
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from database import DataManager
from report_gen import ReportGenerator

class WorkerSignals(QObject):
    """Señales para comunicación entre thread worker y GUI."""
    progress = pyqtSignal(str)  # Mensaje de progreso
    finished = pyqtSignal(str)  # PDF generado exitosamente
    error = pyqtSignal(str)     # Error durante generación

class PDFWorker(Thread):
    """Worker thread para generar PDF sin bloquear la GUI."""
    def __init__(self, db, gen, adm, n_entrega):
        super().__init__()
        self.db = db
        self.gen = gen
        self.admision = adm
        self.numero_entrega = n_entrega
        self.signals = WorkerSignals()
        self.daemon = True
    
    def run(self):
        """Ejecuta la generación de PDF en un hilo separado."""
        try:
            self.signals.progress.emit("Obteniendo datos de la base de datos...")
            h, m, f = self.db.get_datos_completos(self.admision, self.numero_entrega)
            
            if not h:
                self.signals.error.emit(
                    f"No se encontraron datos para Admisión {self.admision}, "
                    f"Entrega {self.numero_entrega}"
                )
                return
            
            self.signals.progress.emit(f"Generando acta para {h.PacienteCompleto}...")
            pdf_path = self.gen.build(h, m, f, self.numero_entrega)
            
            self.signals.progress.emit("Abriendo PDF...")
            if sys.platform == "win32":
                os.startfile(pdf_path)
            
            self.signals.finished.emit(pdf_path)
            
        except PermissionError as e:
            self.signals.error.emit(f"⚠ Permiso Denegado:\n{str(e)}")
        except FileNotFoundError as e:
            self.signals.error.emit(f"📄 Archivo no encontrado:\n{str(e)}")
        except Exception as e:
            self.signals.error.emit(f"⚠ Error inesperado:\n{str(e)}")

class AppFarmacia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Actas de Entrega - Red Medicron IPS")
        self.setGeometry(100, 100, 900, 600)
        
        self.db = DataManager()
        self.gen = ReportGenerator(progress_callback=self._on_progress)
        self.worker = None
        
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Sección de búsqueda
        search_layout = QHBoxLayout()
        self.input_adm = QLineEdit()
        self.input_adm.setPlaceholderText("Escriba el número de admisión...")
        self.input_adm.returnPressed.connect(self.cargar_entregas)  # Buscar al presionar Enter
        
        self.btn_buscar = QPushButton("🔍 Buscar Entregas")
        self.btn_buscar.clicked.connect(self.cargar_entregas)
        
        search_layout.addWidget(QLabel("Admisión:"))
        search_layout.addWidget(self.input_adm)
        search_layout.addWidget(self.btn_buscar)
        
        # Tabla de entregas
        self.tabla = QTableWidget(0, 2)
        self.tabla.setHorizontalHeaderLabels(["Nº Entrega", "Fecha Entrega"])
        self.tabla.setColumnWidth(0, 150)
        self.tabla.setColumnWidth(1, 200)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Sección de generación
        gen_layout = QHBoxLayout()
        self.btn_imprimir = QPushButton("🖨 Generar e Imprimir PDF")
        self.btn_imprimir.clicked.connect(self.generar)
        self.btn_imprimir.setEnabled(False)
        
        gen_layout.addStretch()
        gen_layout.addWidget(self.btn_imprimir)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-size: 10pt;")
        
        # Agregar todo al layout principal
        main_layout.addLayout(search_layout)
        main_layout.addWidget(QLabel("Entregas disponibles:"))
        main_layout.addWidget(self.tabla)
        main_layout.addLayout(gen_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def cargar_entregas(self):
        """Carga las entregas para la admisión especificada."""
        adm = self.input_adm.text().strip()
        if not adm:
            QMessageBox.warning(self, "⚠ Advertencia", "Por favor ingrese un número de admisión.")
            return
        
        self.btn_buscar.setEnabled(False)
        self.status_label.setText("🔍 Buscando entregas...")
        
        try:
            res = self.db.get_entregas(adm)
            self.tabla.setRowCount(0)
            
            if not res:
                QMessageBox.information(
                    self, "📄 Sin Resultados",
                    f"No se encontraron entregas para la admisión: {adm}"
                )
                self.status_label.setText("")
                self.btn_buscar.setEnabled(True)
                return
            
            for i, row in enumerate(res):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row.numeroEntrega)))
                fecha_str = str(row.fechaEntrega)[:10] if row.fechaEntrega else "N/A"
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
            
            self.btn_imprimir.setEnabled(True)
            self.status_label.setText(f"✓ Se encontraron {len(res)} entrega(s)")
            if len(res) == 1:
                self.tabla.selectRow(0)  # Seleccionar automáticamente si hay solo una
                
        except Exception as e:
            QMessageBox.critical(
                self, "❌ Error de Conexión",
                f"No se pudo conectar a la base de datos:\n{str(e)}\n\n"
                f"Verifique que el servidor SQL Server esté disponible en 192.168.59.230"
            )
            self.status_label.setText("❌ Error de conexión a BD")
        finally:
            self.btn_buscar.setEnabled(True)

    def generar(self):
        """Genera el PDF del acta de entrega seleccionada."""
        idx = self.tabla.currentRow()
        if idx < 0:
            QMessageBox.warning(
                self, "⚠ Selección Requerida",
                "Por favor seleccione una entrega de la tabla."
            )
            return
        
        n_entrega = self.tabla.item(idx, 0).text()
        adm = self.input_adm.text().strip()
        
        # Validar que no haya otro proceso en curso
        if self.worker and self.worker.is_alive():
            QMessageBox.warning(
                self, "⚠ Proceso en Curso",
                "Ya hay una generación de PDF en proceso. Espere a que termine."
            )
            return
        
        # Mostrar progress bar
        self.progress_bar.setVisible(True)
        self.btn_buscar.setEnabled(False)
        self.btn_imprimir.setEnabled(False)
        self.input_adm.setEnabled(False)
        self.tabla.setEnabled(False)
        
        # Crear y ejecutar worker
        self.worker = PDFWorker(self.db, self.gen, adm, n_entrega)
        self.worker.signals.progress.connect(self._on_progress)
        self.worker.signals.finished.connect(self._on_success)
        self.worker.signals.error.connect(self._on_error)
        self.worker.start()
    
    def _on_progress(self, message):
        """Maneja actualizaciones de progreso."""
        self.status_label.setText(message)
    
    def _on_success(self, pdf_path):
        """Maneja éxito de generación."""
        self.progress_bar.setVisible(False)
        filename = os.path.basename(pdf_path)
        QMessageBox.information(
            self, "✓ Éxito",
            f"Acta generada exitosamente:\n\n{filename}"
        )
        self.status_label.setText(f"✓ PDF generado: {filename}")
        self._reset_buttons()
    
    def _on_error(self, error_msg):
        """Maneja errores durante generación."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "❌ Error en Generación", error_msg)
        self.status_label.setText("❌ Error al generar PDF")
        self._reset_buttons()
    
    def _reset_buttons(self):
        """Restaura el estado de los botones después de procesar."""
        self.btn_buscar.setEnabled(True)
        self.btn_imprimir.setEnabled(True)
        self.input_adm.setEnabled(True)
        self.tabla.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AppFarmacia()
    win.show()
    sys.exit(app.exec())