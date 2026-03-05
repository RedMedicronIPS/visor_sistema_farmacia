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
        
        # Estado del workflow (0=documento, 1=admisión, 2=entrega)
        self.workflow_stage = 0
        self.current_documento = None
        self.current_admision = None
        
        # Sección de búsqueda
        search_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Ingrese número de documento...")
        self.input_search.returnPressed.connect(self.realizar_busqueda)
        
        self.btn_buscar = QPushButton("🔍 Buscar")
        self.btn_buscar.clicked.connect(self.realizar_busqueda)
        
        self.btn_reset = QPushButton("↩ Nuevo")
        self.btn_reset.clicked.connect(self._reset_workflow)
        self.btn_reset.setEnabled(False)
        
        search_layout.addWidget(QLabel("Documento:"))
        search_layout.addWidget(self.input_search)
        search_layout.addWidget(self.btn_buscar)
        search_layout.addWidget(self.btn_reset)
        
        # Etiqueta dinámica para la tabla
        self.table_label = QLabel("Admisiones disponibles:")
        
        # Tabla (reutilizada para admisiones o entregas)
        self.tabla = QTableWidget(0, 3)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.itemDoubleClicked.connect(self._handle_double_click)
        self.tabla.selectionModel().selectionChanged.connect(self._handle_selection_changed)
        
        # Sección de generación / siguiente paso
        gen_layout = QHBoxLayout()
        self.btn_accion = QPushButton("▶ Siguiente")
        self.btn_accion.clicked.connect(self.realizar_accion)
        self.btn_accion.setEnabled(False)
        
        self.btn_volver = QPushButton("◀ Volver")
        self.btn_volver.clicked.connect(self._volver_a_admisiones)
        self.btn_volver.setEnabled(False)
        
        gen_layout.addStretch()
        gen_layout.addWidget(self.btn_volver)
        gen_layout.addWidget(self.btn_accion)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-size: 10pt;")
        
        # Agregar todo al layout principal
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table_label)
        main_layout.addWidget(self.tabla)
        main_layout.addLayout(gen_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def realizar_busqueda(self):
        """Busca según el stage actual (documento, admisión o entrega)."""
        text = self.input_search.text().strip()
        if not text:
            QMessageBox.warning(self, "⚠ Advertencia", "Por favor ingrese un valor.")
            return
        
        self.btn_buscar.setEnabled(False)
        self.status_label.setText("🔍 Buscando...")
        
        try:
            if self.workflow_stage == 0:
                # STAGE 0: Buscar paciente por documento
                paciente = self.db.search_pacientes_by_documento(text)
                if not paciente:
                    QMessageBox.information(
                        self, "📄 No encontrado",
                        f"No se encontró paciente con documento: {text}"
                    )
                    self.status_label.setText("")
                    return
                
                self.current_documento = paciente.IdUsuario
                self.tabla.setRowCount(0)
                self.tabla.setHorizontalHeaderLabels(["Admisión", "Fecha Ingreso", "Entregas"])
                
                # Obtener solo admisiones CON entregas
                admisiones = self.db.get_admisiones_with_entregas(paciente.IdUsuario)
                if not admisiones:
                    QMessageBox.information(
                        self, "📄 Sin Entregas",
                        f"El paciente {paciente.NombrePaciente}\nno tiene entregas registradas."
                    )
                    self.status_label.setText("")
                    return
                
                for i, row in enumerate(admisiones):
                    self.tabla.insertRow(i)
                    self.tabla.setItem(i, 0, QTableWidgetItem(str(row.IdAdmision)))
                    self.tabla.setItem(i, 1, QTableWidgetItem(str(row.FechaIngreso)))
                    self.tabla.setItem(i, 2, QTableWidgetItem(str(row.NumeroEntregas)))
                
                self.workflow_stage = 1
                self.input_search.clear()
                self.input_search.setPlaceholderText("(Seleccione admisión arriba)")
                self.btn_buscar.setText("🔍 Buscar")
                self.btn_buscar.setEnabled(False)  # Sin usar en stage 1
                self.btn_accion.setText("▶ Cargar Entregas")
                self.btn_accion.setEnabled(True)
                self.btn_reset.setEnabled(True)
                self.table_label.setText(f"Admisiones del paciente: {paciente.NombrePaciente}")
                self.status_label.setText(f"✓ {len(admisiones)} admisión(es) encontrada(s)")
                
            elif self.workflow_stage == 1:
                # STAGE 1: Debe seleccionar admisión de la tabla
                idx = self.tabla.currentRow()
                if idx < 0:
                    QMessageBox.warning(
                        self, "⚠ Selección Requerida",
                        "Por favor seleccione una admisión de la lista."
                    )
                else:
                    adm = self.tabla.item(idx, 0).text()
                    self._cargar_entregas(adm)
                    
        except Exception as e:
            QMessageBox.critical(
                self, "❌ Error",
                f"Error en la búsqueda:\n{str(e)}"
            )
            self.status_label.setText("❌ Error en búsqueda")
        finally:
            self.btn_buscar.setEnabled(True)

    def _cargar_entregas(self, id_admision):
        """Carga las entregas de una admisión."""
        try:
            entregas = self.db.get_entregas(id_admision)
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(4)
            self.tabla.setHorizontalHeaderLabels(["Nº Entrega", "Fecha Entrega", "Funcionario", ""])
            
            if not entregas:
                QMessageBox.information(
                    self, "📄 Sin Entregas",
                    f"No hay entregas registradas para admisión {id_admision}"
                )
                return
            
            for i, row in enumerate(entregas):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row.numeroEntrega)))
                fecha_str = str(row.fechaEntrega)[:10] if row.fechaEntrega else "N/A"
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
                # Agregar nombre del funcionario
                funcionario_str = row.funcionarioNombre if hasattr(row, 'funcionarioNombre') else "N/A"
                self.tabla.setItem(i, 2, QTableWidgetItem(funcionario_str))
            
            self.workflow_stage = 2
            self.current_admision = id_admision
            self.input_search.setPlaceholderText("(Seleccione entrega)")
            self.btn_buscar.setEnabled(False)  # Sin usar en stage 2
            self.btn_accion.setText("🖨 Generar PDF")
            self.btn_accion.setEnabled(True)
            self.btn_volver.setEnabled(True)
            self.table_label.setText(f"Entregas - Admisión {id_admision}")
            self.status_label.setText(f"✓ {len(entregas)} entrega(s) encontrada(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar entregas:\n{str(e)}")
            self.status_label.setText("❌ Error al cargar entregas")

    def realizar_accion(self):
        """Ejecuta la acción del botón según el stage."""
        if self.workflow_stage == 1:
            # Stage 1: Seleccionar y cargar entregas desde tabla
            idx = self.tabla.currentRow()
            if idx < 0:
                QMessageBox.warning(self, "⚠ Selección Requerida", "Por favor seleccione una admisión.")
            else:
                adm = self.tabla.item(idx, 0).text()
                self._cargar_entregas(adm)
        elif self.workflow_stage == 2:
            # Stage 2: Generar PDF
            self.generar_pdf()

    def _handle_double_click(self, item):
        """Permite avanzar con doble clic en la tabla."""
        if self.workflow_stage == 1:
            self.realizar_busqueda()
        elif self.workflow_stage == 2:
            self.generar_pdf()

    def _handle_selection_changed(self):
        """Automáticamente carga entregas cuando selecciona una admisión en stage 1."""
        if self.workflow_stage == 1:
            # Auto-cargar entregas cuando selecciona una admisión
            idx = self.tabla.currentRow()
            if idx >= 0:
                adm = self.tabla.item(idx, 0).text()
                self._cargar_entregas_rapido(adm)
        elif self.workflow_stage == 2:
            # Solo habilitar botón cuando hay selección en stage 2
            idx = self.tabla.currentRow()
            self.btn_accion.setEnabled(idx >= 0)

    def _cargar_entregas_rapido(self, id_admision):
        """Versión rápida que carga entregas sin mostrar messageboxes."""
        try:
            entregas = self.db.get_entregas(id_admision)
            if not entregas:
                # Si no hay entregas, no cambiar de stage
                return
            
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(4)
            self.tabla.setHorizontalHeaderLabels(["Nº Entrega", "Fecha Entrega", "Funcionario", ""])
            
            for i, row in enumerate(entregas):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row.numeroEntrega)))
                fecha_str = str(row.fechaEntrega)[:10] if row.fechaEntrega else "N/A"
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
                # Agregar nombre del funcionario
                funcionario_str = row.funcionarioNombre if hasattr(row, 'funcionarioNombre') else "N/A"
                self.tabla.setItem(i, 2, QTableWidgetItem(funcionario_str))
            
            self.workflow_stage = 2
            self.current_admision = id_admision
            self.input_search.clear()
            self.input_search.setPlaceholderText("(Seleccione entrega)")
            self.btn_buscar.setEnabled(False)
            self.btn_accion.setText("🖨 Generar PDF")
            self.btn_accion.setEnabled(True)
            self.btn_volver.setEnabled(True)
            self.table_label.setText(f"Entregas - Admisión {id_admision}")
            self.status_label.setText(f"✓ {len(entregas)} entrega(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar entregas:\n{str(e)}")
            self.status_label.setText("❌ Error al cargar entregas")

    def _reset_workflow(self):
        """Vuelve al inicio del workflow."""
        self.workflow_stage = 0
        self.current_documento = None
        self.current_admision = None
        self.input_search.setText("")
        self.input_search.setPlaceholderText("Ingrese número de documento...")
        self.btn_buscar.setText("🔍 Buscar")
        self.btn_buscar.setEnabled(True)
        self.btn_accion.setText("▶ Siguiente")
        self.btn_accion.setEnabled(False)
        self.btn_volver.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.table_label.setText("Admisiones disponibles:")
        self.tabla.setRowCount(0)
        self.status_label.setText("")
    
    def _volver_a_admisiones(self):
        """Vuelve a la pantalla de admisiones sin resetear el documento."""
        self.workflow_stage = 1
        self.current_admision = None
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Admisión", "Fecha Ingreso", "Entregas"])
        
        # Recargar las admisiones del documento actual
        try:
            admisiones = self.db.get_admisiones_with_entregas(self.current_documento)
            for i, row in enumerate(admisiones):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row.IdAdmision)))
                self.tabla.setItem(i, 1, QTableWidgetItem(str(row.FechaIngreso)))
                self.tabla.setItem(i, 2, QTableWidgetItem(str(row.NumeroEntregas)))
            
            self.input_search.setPlaceholderText("(Seleccione admisión arriba)")
            self.btn_buscar.setEnabled(False)
            self.btn_accion.setText("▶ Cargar Entregas")
            self.btn_accion.setEnabled(True)
            self.btn_volver.setEnabled(False)
            self.btn_reset.setEnabled(True)
            self.table_label.setText("Admisiones disponibles:")
            self.status_label.setText(f"✓ {len(admisiones)} admisión(es) disponible(s)")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al recargar admisiones:\n{str(e)}")
            self.status_label.setText("❌ Error al recargar admisiones")

    def generar_pdf(self):
        """Genera el PDF de la entrega seleccionada."""
        idx = self.tabla.currentRow()
        if idx < 0:
            QMessageBox.warning(
                self, "⚠ Selección Requerida",
                "Por favor seleccione una entrega de la tabla."
            )
            return
        
        n_entrega = self.tabla.item(idx, 0).text()
        
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
        self.btn_accion.setEnabled(False)
        self.input_search.setEnabled(False)
        self.tabla.setEnabled(False)
        
        # Crear y ejecutar worker
        self.worker = PDFWorker(self.db, self.gen, self.current_admision, n_entrega)
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
        self.btn_accion.setEnabled(self.workflow_stage > 0)  # Habilitar solo si no está en stage 0
        self.input_search.setEnabled(True)
        self.tabla.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AppFarmacia()
    win.show()
    sys.exit(app.exec())