import sys
import os
from threading import Thread
from datetime import datetime
from PyPDF2 import PdfMerger
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QProgressBar, QMessageBox, QTabWidget, QDateEdit, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QDate
from PyQt6.QtGui import QIcon, QColor
from database import DataManager
from report_gen import ReportGenerator
from openpyxl import Workbook

class WorkerSignals(QObject):
    """Señales para comunicación entre thread worker y GUI."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    row_update = pyqtSignal(int, dict)  # Actualizar fila con resultado

class PDFWorker(Thread):
    """Worker thread para generar un PDF individual."""
    def __init__(self, db, gen, adm, n_entrega, output_folder=None):
        super().__init__()
        self.db = db
        self.gen = gen
        self.admision = adm
        self.numero_entrega = n_entrega
        self.output_folder = output_folder
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
            pdf_path = self.gen.build(h, m, f, self.numero_entrega, self.output_folder, is_bulk=False)
            
            self.signals.progress.emit("PDF listo")
            self.signals.finished.emit(pdf_path)
            
        except PermissionError as e:
            self.signals.error.emit(f"⚠ Permiso Denegado:\n{str(e)}")
        except FileNotFoundError as e:
            self.signals.error.emit(f"📄 Archivo no encontrado:\n{str(e)}")
        except Exception as e:
            self.signals.error.emit(f"⚠ Error inesperado:\n{str(e)}")

class BulkPDFWorker(Thread):
    """Worker thread para generar PDFs en lote con pausa/cancelación."""
    def __init__(self, db, gen, entregas_list, output_folder):
        super().__init__()
        self.db = db
        self.gen = gen
        self.entregas_list = entregas_list
        self.output_folder = output_folder
        self.signals = WorkerSignals()
        self.daemon = True
        self.resultados = []
        self.paused = False
        self.cancelled = False
    
    def pause(self):
        """Pausa la generación."""
        self.paused = True
    
    def resume(self):
        """Reanuda la generación."""
        self.paused = False
    
    def cancel(self):
        """Cancela la generación."""
        self.cancelled = True
    
    def run(self):
        """Ejecuta la generación de múltiples PDFs."""
        total = len(self.entregas_list)
        
        # Deduplicación especial: 
        # - numeroEntrega = 0: Permitir duplicados (pueden existir múltiples del mismo dia)
        # - numeroEntrega != 0: Una sola entrega por (paciente + numeroEntrega + fecha)
        entregas_filtradas = []
        entregas_vistas = {}  # Para tracking de deduplicación
        
        for idx, (id_adm, n_entrega, fecha_entrega, id_usuario, nombre_paciente, sede_nombre) in enumerate(self.entregas_list):
            if n_entrega == 0 or str(n_entrega).strip() == '0':
                # Si numeroEntrega es 0: permitir duplicados, agregar siempre
                entregas_filtradas.append((id_adm, n_entrega, fecha_entrega, id_usuario, nombre_paciente, sede_nombre))
            else:
                # Para otros números: aplicar deduplicación por (paciente + entrega + fecha)
                clave = (id_usuario, str(n_entrega).strip(), str(fecha_entrega)[:10])
                if clave not in entregas_vistas:
                    entregas_vistas[clave] = True
                    entregas_filtradas.append((id_adm, n_entrega, fecha_entrega, id_usuario, nombre_paciente, sede_nombre))
        
        total_original = total
        total = len(entregas_filtradas)
        
        # Informar si se eliminaron duplicados
        if total < total_original:
            self.signals.progress.emit(f"⚠ Eliminados {total_original - total} duplicados (excepto entregas #0). Procesando {total} entregas...")
        
        for idx, (id_adm, n_entrega, fecha_entrega, id_usuario, nombre_paciente, sede_nombre) in enumerate(entregas_filtradas):
            # Verificar pausa/cancelación
            while self.paused and not self.cancelled:
                import time
                time.sleep(0.5)
            
            if self.cancelled:
                self.signals.finished.emit(f"Proceso cancelado en {idx}/{total}")
                break
            
            try:
                self.signals.progress.emit(
                    f"Generando PDF {idx+1}/{total}: {nombre_paciente}..."
                )
                h, m, f = self.db.get_datos_completos(id_adm, n_entrega)
                # Detectar estado de la firma para el Excel
                estado_firma = "FIRMADO" if f else "SIN FIRMA (Pte. Manual)"
                
                if not h:
                    resultado = {
                        'id_usuario': id_usuario,
                        'nombre_paciente': nombre_paciente,
                        'admision': id_adm,
                        'entrega': n_entrega,
                        'fecha': 'N/A',
                        'archivo': 'SIN DATOS',
                        'estado': 'FALLO',
                        'firma': estado_firma, # <--- Nueva clave para el Excel
                        'color': '#ffcccc', # Verde si tiene firma, amarillo si no
                        'sede': sede_nombre
                    }
                    self.resultados.append(resultado)
                    self.signals.row_update.emit(idx, resultado)
                    continue
                
                pdf_path = self.gen.build(h, m, f, n_entrega, self.output_folder, is_bulk=True)
                filename = os.path.basename(pdf_path)
                fecha_str = str(fecha_entrega)[:10] if fecha_entrega else 'N/A'
                
                resultado = {
                    'id_usuario': id_usuario,
                    'nombre_paciente': nombre_paciente,
                    'admision': id_adm,
                    'entrega': n_entrega,
                    'fecha': fecha_str,
                    'archivo': filename,
                    'estado': 'EXITOSO',
                    'firma': estado_firma,
                    'color': '#ccffcc' if f else '#fff3cd',
                    'sede': sede_nombre
                }
                self.resultados.append(resultado)
                self.signals.row_update.emit(idx, resultado)
                
            except Exception as e:
                resultado = {
                    'id_usuario': id_usuario,
                    'nombre_paciente': nombre_paciente,
                    'admision': id_adm,
                    'entrega': n_entrega,
                    'fecha': 'N/A',
                    'archivo': str(e)[:45],
                    'estado': 'FALLO',
                    'firma': "ERROR PROCESO",
                    'color': '#ffcccc',
                    'sede': sede_nombre
                }
                self.resultados.append(resultado)
                self.signals.row_update.emit(idx, resultado)
        
        self.signals.finished.emit(f"Procesados {total} documentos")

class AppFarmacia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Actas de Entrega - Red Medicron IPS")
        self.setGeometry(100, 100, 1100, 700)
        
        self.db = DataManager()
        self.gen = ReportGenerator(progress_callback=self._on_progress)
        self.worker = None
        self.output_folder = None
        self.sedes = []
        
        self.setup_ui()
        self._cargar_sedes()

    def setup_ui(self):
        """Configura la interfaz con pestañas."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Entrega Individual
        self.tab_individual = QWidget()
        self.setup_tab_individual()
        self.tabs.addTab(self.tab_individual, "📄 Generación Individual")
        
        # Tab 2: Generación Masiva
        self.tab_masiva = QWidget()
        self.setup_tab_masiva()
        self.tabs.addTab(self.tab_masiva, "📦 Generación Masiva")
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-size: 10pt;")
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _cargar_sedes(self):
        """Carga la lista de sedes desde la BD."""
        try:
            self.sedes = self.db.get_sedes()
            self.combo_sede.clear()
            self.combo_sede.addItem("-- Todas las Sedes --", None)
            for sede in self.sedes:
                # sede.id ahora es la PK interna que coincide con idSede en la transacción
                # self.combo_sede.addItem(sede.SedeNombre, sede.id)
                self.combo_sede.addItem(str(sede[1]), sede[0])
        except Exception as e:
            print(f"Error al cargar sedes: {str(e)}")
            self.sedes = []

    def setup_tab_individual(self):
        """Configura la pestaña de generación individual."""
        layout = QVBoxLayout(self.tab_individual)
        
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
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        self.label_folder = QLabel("📁 Carpeta: (Aplicación)")
        self.btn_select_folder = QPushButton("📂 Seleccionar Carpeta")
        self.btn_select_folder.clicked.connect(self._select_output_folder)
        folder_layout.addWidget(self.label_folder)
        folder_layout.addWidget(self.btn_select_folder)
        folder_layout.addStretch()
        
        # Tabla
        self.table_label = QLabel("Admisiones disponibles:")
        self.tabla = QTableWidget(0, 3)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.itemDoubleClicked.connect(self._handle_double_click)
        self.tabla.selectionModel().selectionChanged.connect(self._handle_selection_changed)
        
        # Botones de acción
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
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        
        # Agregar todo al layout
        layout.addLayout(search_layout)
        layout.addLayout(folder_layout)
        layout.addWidget(self.table_label)
        layout.addWidget(self.tabla)
        layout.addLayout(gen_layout)
        layout.addWidget(self.progress_bar)

    def setup_tab_masiva(self):
        """Configura la pestaña de generación masiva."""
        layout = QVBoxLayout(self.tab_masiva)
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        self.label_folder_bulk = QLabel("📁 Carpeta: (Aplicación)")
        self.btn_select_folder_bulk = QPushButton("📂 Seleccionar Carpeta")
        self.btn_select_folder_bulk.clicked.connect(self._select_output_folder_bulk)
        self.btn_unificar = QPushButton("🔄 Unificar PDFs")
        self.btn_unificar.clicked.connect(self._unificar_pdfs)
        folder_layout.addWidget(self.label_folder_bulk)
        folder_layout.addWidget(self.btn_select_folder_bulk)
        folder_layout.addWidget(self.btn_unificar)
        folder_layout.addStretch()
        layout.addLayout(folder_layout)
        
        # Selector de sede (nuevo)
        sede_layout = QHBoxLayout()
        sede_layout.addWidget(QLabel("🏥 Filtrar por Sede:"))
        self.combo_sede = QComboBox()
        self.combo_sede.addItem("-- Todas las Sedes --", None)
        for sede in self.sedes:
            self.combo_sede.addItem(sede.SedeNombre, sede.id)
        sede_layout.addWidget(self.combo_sede)
        sede_layout.addStretch()
        layout.addLayout(sede_layout)
        
        # Opción 1 - Por Cédula
        cedula_layout = QHBoxLayout()
        cedula_layout.addWidget(QLabel("📌 Por Cédula:"))
        self.input_cedula = QLineEdit()
        self.input_cedula.setPlaceholderText("Ingrese cédula del paciente...")
        self.btn_generar_cedula = QPushButton("📥 Descargar Todos sus PDFs")
        self.btn_generar_cedula.clicked.connect(self._generar_masiva_cedula)
        cedula_layout.addWidget(self.input_cedula)
        cedula_layout.addWidget(self.btn_generar_cedula)
        layout.addLayout(cedula_layout)
        
        # Opción 2 - Por Fechas
        fecha_layout = QHBoxLayout()
        fecha_layout.addWidget(QLabel("📅 Rango de Fechas:"))
        
        self.date_inicio = QDateEdit()
        self.date_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.date_inicio.setCalendarPopup(True)
        
        fecha_layout.addWidget(QLabel("Desde:"))
        fecha_layout.addWidget(self.date_inicio)
        
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        
        fecha_layout.addWidget(QLabel("Hasta:"))
        fecha_layout.addWidget(self.date_fin)
        
        self.btn_generar_fecha = QPushButton("📥 Descargar PDFs del Período")
        self.btn_generar_fecha.clicked.connect(self._generar_masiva_fecha)
        fecha_layout.addWidget(self.btn_generar_fecha)
        layout.addLayout(fecha_layout)
        
        # Tabla de resultados (ahora con 8 columnas)
        self.tabla_masiva = QTableWidget(0, 8)
        self.tabla_masiva.setHorizontalHeaderLabels([
            "ID Paciente", "Nombre Paciente", "Admisión", "Entrega", 
            "Fecha Entrega", "Archivo PDF", "Estado", "Sede"
        ])
        layout.addWidget(QLabel("📊 Resultados de Generación:"))
        layout.addWidget(self.tabla_masiva)
        
        # Progress bar masiva
        self.progress_bar_bulk = QProgressBar()
        self.progress_bar_bulk.setVisible(False)
        self.progress_bar_bulk.setRange(0, 0)
        layout.addWidget(self.progress_bar_bulk)
        
        # Botones de control (pausa/cancelar)
        control_layout = QHBoxLayout()
        self.btn_pausar = QPushButton("⏸ Pausar")
        self.btn_pausar.clicked.connect(self._pausar_generacion)
        self.btn_pausar.setEnabled(False)
        
        self.btn_cancelar = QPushButton("⏹ Cancelar")
        self.btn_cancelar.clicked.connect(self._cancelar_generacion)
        self.btn_cancelar.setEnabled(False)
        
        control_layout.addStretch()
        control_layout.addWidget(self.btn_pausar)
        control_layout.addWidget(self.btn_cancelar)
        layout.addLayout(control_layout)
        
        # Botones de acción finales
        bulk_btn_layout = QHBoxLayout()
        self.btn_generar_excel = QPushButton("📊 Generar Excel de Resultados")
        self.btn_generar_excel.clicked.connect(self._generar_excel_resultados)
        self.btn_generar_excel.setEnabled(False)
        bulk_btn_layout.addStretch()
        bulk_btn_layout.addWidget(self.btn_generar_excel)
        layout.addLayout(bulk_btn_layout)

    def _select_output_folder(self):
        """Selecciona carpeta para guardar PDFs (pestaña individual)."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta para Guardar PDFs"
        )
        if folder:
            self.output_folder = folder
            self.label_folder.setText(f"📁 Carpeta: {os.path.basename(folder)}")
        else:
            self.output_folder = None
            self.label_folder.setText("📁 Carpeta: (Aplicación)")

    def _select_output_folder_bulk(self):
        """Selecciona carpeta para guardar PDFs (pestaña masiva)."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta para Guardar PDFs en Lote"
        )
        if folder:
            self.output_folder = folder
            self.label_folder_bulk.setText(f"📁 Carpeta: {os.path.basename(folder)}")
        else:
            self.output_folder = None
            self.label_folder_bulk.setText("📁 Carpeta: (Aplicación)")

    def _unificar_pdfs(self):
        """Combina PDFs duplicados del mismo paciente en un solo archivo.

        Busca en la carpeta todos los archivos Acta_Entrega_*.pdf,
        los agrupa por ID de usuario (número de documento), y para cada
        grupo con múltiples PDFs:
        - Combina todas las páginas en un solo PDF
        - Guarda como Acta_Entrega_<IdUsuario>.pdf
        - Elimina los archivos originales
        """
        folder = self.output_folder
        if not folder:
            QMessageBox.warning(self, "⚠ Carpeta no definida",
                                "Seleccione una carpeta antes de unificar PDFs.")
            return
        try:
            archivos = [f for f in os.listdir(folder)
                        if f.startswith("Acta_Entrega_") and f.lower().endswith(".pdf")]
        except Exception as e:
            QMessageBox.critical(self, "Error de lectura",
                                 f"No se pudo listar la carpeta:\n{str(e)}")
            return
        
        # Agrupar archivos por ID de usuario
        grupos = {}
        for fname in archivos:
            partes = fname.split("_")
            if len(partes) < 3:
                continue
            idusuario = partes[2]  # Acta_Entrega_<ID>_<orden>.pdf
            if idusuario not in grupos:
                grupos[idusuario] = []
            grupos[idusuario].append(fname)
        
        combinados = 0
        eliminados = 0
        
        for idusuario, pdfs in grupos.items():
            if len(pdfs) == 1:
                # Solo un PDF, solo renombrar si es necesario
                fname_orig = pdfs[0]
                fname_final = f"Acta_Entrega_{idusuario}.pdf"
                if fname_orig != fname_final:
                    try:
                        os.rename(os.path.join(folder, fname_orig),
                                  os.path.join(folder, fname_final))
                    except Exception:
                        pass
            else:
                # Múltiples PDFs: combinar
                pdfs_ordenados = sorted(pdfs)  # Orden alfabético
                ruta_final = os.path.join(folder, f"Acta_Entrega_{idusuario}.pdf")
                
                try:
                    merger = PdfMerger()
                    for pdf_name in pdfs_ordenados:
                        ruta_pdf = os.path.join(folder, pdf_name)
                        merger.append(ruta_pdf)
                    
                    merger.write(ruta_final)
                    merger.close()
                    
                    combinados += 1
                    
                    # Eliminar archivos originales tras combinar exitosamente
                    for pdf_name in pdfs_ordenados:
                        try:
                            os.remove(os.path.join(folder, pdf_name))
                            eliminados += 1
                        except Exception:
                            pass
                
                except Exception as e:
                    QMessageBox.warning(self, "Error al combinar",
                                        f"ID {idusuario}: {str(e)}")
                    continue
        
        QMessageBox.information(
            self, "Unificación completa",
            f"Combinados: {combinados}\nEliminados: {eliminados} archivos duplicados"
        )

    def _generar_masiva_cedula(self):
        """Genera todos los PDFs de un paciente por cédula."""
        cedula = self.input_cedula.text().strip()
        if not cedula:
            QMessageBox.warning(self, "⚠ Advertencia", "Ingrese la cédula del paciente.")
            return
        
        try:
            id_sede = self.combo_sede.currentData()
            entregas = self.db.get_all_entregas_by_cedula(cedula, id_sede)
            if not entregas:
                QMessageBox.information(
                    self, "📄 Sin Entregas",
                    f"No se encontraron entregas para el paciente con cédula: {cedula}"
                )
                return
            
            entregas_list = [
                (row.IdAdmision, row.numeroEntrega, row.fechaEntrega, row.IdUsuario, row.nombrePaciente, row.SedeNombre)
                for row in entregas
            ]
            
            self._ejecutar_generacion_bulk(entregas_list)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error en búsqueda:\n{str(e)}")

    def _generar_masiva_fecha(self):
        """Genera todos los PDFs en un rango de fechas."""
        fecha_inicio = self.date_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.date_fin.date().toString("yyyy-MM-dd")
        
        try:
            id_sede = self.combo_sede.currentData()
            entregas = self.db.get_entregas_by_date_range(fecha_inicio, fecha_fin, id_sede)
            if not entregas:
                QMessageBox.information(
                    self, "📄 Sin Entregas",
                    f"No se encontraron entregas en el rango: {fecha_inicio} a {fecha_fin}"
                )
                return
            
            entregas_list = [
                (row.IdAdmision, row.numeroEntrega, row.fechaEntrega, row.IdUsuario, row.nombrePaciente, row.SedeNombre)
                for row in entregas
            ]
            
            self._ejecutar_generacion_bulk(entregas_list)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error en búsqueda:\n{str(e)}")

    def _ejecutar_generacion_bulk(self, entregas_list):
        """Ejecuta la generación de múltiples PDFs."""
        if self.worker and self.worker.is_alive():
            QMessageBox.warning(
                self, "⚠ Proceso en Curso",
                "Ya hay una generación en curso. Espere a que termine."
            )
            return
        
        self.progress_bar_bulk.setVisible(True)
        self.tabla_masiva.setRowCount(len(entregas_list))
        self.btn_generar_excel.setEnabled(False)
        self.btn_pausar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)
        
        self.worker = BulkPDFWorker(self.db, self.gen, entregas_list, self.output_folder)
        self.worker.signals.progress.connect(self._on_progress_bulk)
        self.worker.signals.finished.connect(self._on_success_bulk)
        self.worker.signals.row_update.connect(self._actualizar_fila_resultado)
        self.worker.signals.error.connect(self._on_error_bulk)
        self.worker.start()

    def _actualizar_fila_resultado(self, row_idx, resultado):
        """Actualiza una fila de la tabla con el resultado."""
        if row_idx < self.tabla_masiva.rowCount():
            self.tabla_masiva.setItem(row_idx, 0, QTableWidgetItem(str(resultado['id_usuario'])))
            self.tabla_masiva.setItem(row_idx, 1, QTableWidgetItem(resultado['nombre_paciente']))
            self.tabla_masiva.setItem(row_idx, 2, QTableWidgetItem(str(resultado['admision'])))
            self.tabla_masiva.setItem(row_idx, 3, QTableWidgetItem(str(resultado['entrega'])))
            self.tabla_masiva.setItem(row_idx, 4, QTableWidgetItem(resultado['fecha']))
            self.tabla_masiva.setItem(row_idx, 5, QTableWidgetItem(resultado['archivo']))
            
            estado_item = QTableWidgetItem(resultado['estado'])
            estado_item.setBackground(QColor(resultado.get('color', '#ffffff')))
            self.tabla_masiva.setItem(row_idx, 6, estado_item)
            
            self.tabla_masiva.setItem(row_idx, 7, QTableWidgetItem(resultado.get('sede', '-')))

    def _pausar_generacion(self):
        """Pausa o reanuda la generación."""
        if self.worker:
            if self.worker.paused:
                self.worker.resume()
                self.btn_pausar.setText("⏸ Pausar")
                self.status_label.setText("Reanudado...")
            else:
                self.worker.pause()
                self.btn_pausar.setText("▶ Reanudar")
                self.status_label.setText("Pausado")

    def _cancelar_generacion(self):
        """Cancela la generación en curso."""
        if self.worker:
            resultado = QMessageBox.question(
                self, "Confirmar Cancelación",
                "¿Está seguro que desea cancelar el proceso?\nSe guardará el progreso realizado.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resultado == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.btn_pausar.setEnabled(False)
                self.btn_cancelar.setEnabled(False)
                self.status_label.setText("Cancelando proceso...")

    def _on_progress_bulk(self, message):
        """Actualiza progreso de generación en lote."""
        self.status_label.setText(message)

    def _on_success_bulk(self, message):
        """Completa la generación en lote y muestra resultados."""
        self.progress_bar_bulk.setVisible(False)
        self.btn_pausar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self.btn_pausar.setText("⏸ Pausar")
        
        resultados = self.worker.resultados if self.worker else []
        
        exitosos = sum(1 for r in resultados if r['estado'] == 'EXITOSO')
        fallos = sum(1 for r in resultados if r['estado'] == 'FALLO')
        
        self.status_label.setText(
            f"✓ Procesados: {len(resultados)} | Exitosos: {exitosos} | Fallos: {fallos}"
        )
        self.btn_generar_excel.setEnabled(True)

    def _on_error_bulk(self, error_msg):
        """Maneja errores en generación en lote."""
        self.progress_bar_bulk.setVisible(False)
        QMessageBox.critical(self, "❌ Error en Generación", error_msg)
        self.status_label.setText("❌ Error durante generación")

    def _generar_excel_resultados(self):
        """Genera un archivo Excel con los resultados."""
        if not self.worker or not self.worker.resultados:
            QMessageBox.warning(
                self, "⚠ Advertencia",
                "No hay resultados para exportar."
            )
            return
        
        try:
            archivo_excel = QFileDialog.getSaveFileName(
                self, "Guardar Reporte Excel", "",
                "Archivos Excel (*.xlsx)"
            )[0]
            
            if not archivo_excel:
                return
            
            # Crear workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Reporte Generación"
            
            # Encabezados
            encabezados = [
                "ID Paciente", "Nombre Paciente", "Admisión", "Entrega",
                "Fecha Entrega", "Archivo PDF", "Estado", "Soporte Firma", "Sede"
            ]
            ws.append(encabezados)
            
            # Datos
            for resultado in self.worker.resultados:
                ws.append([
                    resultado['id_usuario'],
                    resultado['nombre_paciente'],
                    resultado['admision'],
                    resultado['entrega'],
                    resultado['fecha'],
                    resultado['archivo'],
                    resultado['estado'],
                    resultado.get('firma', 'N/A'),
                    resultado.get('sede', 'N/A')
                ])
            
            # Ajustar ancho
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                ws.column_dimensions[col].width = 20
            
            wb.save(archivo_excel)
            
            QMessageBox.information(
                self, "✓ Éxito",
                f"Reporte Excel generado:\n\n{os.path.basename(archivo_excel)}"
            )
            
            if sys.platform == "win32":
                os.startfile(archivo_excel)
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al generar Excel:\n{str(e)}")

    # ===== Métodos de la primera pestaña (sin cambios) =====
    def realizar_busqueda(self):
        """Busca según el stage actual."""
        text = self.input_search.text().strip()
        if not text:
            QMessageBox.warning(self, "⚠ Advertencia", "Por favor ingrese un valor.")
            return
        
        self.btn_buscar.setEnabled(False)
        self.status_label.setText("🔍 Buscando...")
        
        try:
            if self.workflow_stage == 0:
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
                self.btn_buscar.setEnabled(False)
                self.btn_accion.setText("▶ Cargar Entregas")
                self.btn_accion.setEnabled(True)
                self.btn_reset.setEnabled(True)
                self.table_label.setText(f"Admisiones del paciente: {paciente.NombrePaciente}")
                self.status_label.setText(f"✓ {len(admisiones)} admisión(es) encontrada(s)")
                
            elif self.workflow_stage == 1:
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
            QMessageBox.critical(self, "❌ Error", f"Error en la búsqueda:\n{str(e)}")
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
                funcionario_str = row.funcionarioNombre if hasattr(row, 'funcionarioNombre') else "N/A"
                self.tabla.setItem(i, 2, QTableWidgetItem(funcionario_str))
            
            self.workflow_stage = 2
            self.current_admision = id_admision
            self.input_search.setPlaceholderText("(Seleccione entrega)")
            self.btn_buscar.setEnabled(False)
            self.btn_accion.setText("🖨 Generar PDF")
            self.btn_accion.setEnabled(True)
            self.btn_volver.setEnabled(True)
            self.table_label.setText(f"Entregas - Admisión {id_admision}")
            self.status_label.setText(f"✓ {len(entregas)} entrega(s) encontrada(s)")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar entregas:\n{str(e)}")

    def realizar_accion(self):
        """Ejecuta la acción del botón según el stage."""
        if self.workflow_stage == 1:
            idx = self.tabla.currentRow()
            if idx < 0:
                QMessageBox.warning(self, "⚠ Selección Requerida", "Por favor seleccione una admisión.")
            else:
                adm = self.tabla.item(idx, 0).text()
                self._cargar_entregas(adm)
        elif self.workflow_stage == 2:
            self.generar_pdf()

    def _handle_double_click(self, item):
        """Permite avanzar con doble clic."""
        if self.workflow_stage == 1:
            self.realizar_busqueda()
        elif self.workflow_stage == 2:
            self.generar_pdf()

    def _handle_selection_changed(self):
        """Carga entregas al seleccionar una admisión."""
        if self.workflow_stage == 1:
            idx = self.tabla.currentRow()
            if idx >= 0:
                adm = self.tabla.item(idx, 0).text()
                self._cargar_entregas_rapido(adm)
        elif self.workflow_stage == 2:
            idx = self.tabla.currentRow()
            self.btn_accion.setEnabled(idx >= 0)

    def _cargar_entregas_rapido(self, id_admision):
        """Carga entregas sin mostrar messageboxes."""
        try:
            entregas = self.db.get_entregas(id_admision)
            if not entregas:
                return
            
            self.tabla.setRowCount(0)
            self.tabla.setColumnCount(4)
            self.tabla.setHorizontalHeaderLabels(["Nº Entrega", "Fecha Entrega", "Funcionario", ""])
            
            for i, row in enumerate(entregas):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row.numeroEntrega)))
                fecha_str = str(row.fechaEntrega)[:10] if row.fechaEntrega else "N/A"
                self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
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
        """Vuelve a la pantalla de admisiones."""
        self.workflow_stage = 1
        self.current_admision = None
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Admisión", "Fecha Ingreso", "Entregas"])
        
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
        
        if self.worker and self.worker.is_alive():
            QMessageBox.warning(
                self, "⚠ Proceso en Curso",
                "Ya hay una generación de PDF en proceso. Espere a que termine."
            )
            return
        
        self.progress_bar.setVisible(True)
        self.btn_buscar.setEnabled(False)
        self.btn_accion.setEnabled(False)
        self.input_search.setEnabled(False)
        self.tabla.setEnabled(False)
        
        self.worker = PDFWorker(self.db, self.gen, self.current_admision, n_entrega, self.output_folder)
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
        if sys.platform == "win32":
            os.startfile(pdf_path)
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
        self.btn_accion.setEnabled(self.workflow_stage > 0)
        self.input_search.setEnabled(True)
        self.tabla.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AppFarmacia()
    win.show()
    sys.exit(app.exec())
