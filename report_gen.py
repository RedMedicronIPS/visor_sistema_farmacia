import io
import os
import sys
import time
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from docx2pdf import convert

class ReportGenerator:
    def __init__(self, progress_callback=None):
        """Inicializa el generador de reportes.
        
        Args:
            progress_callback: Función para reportar progreso (ej: lambda msg: print(msg))
        """
        self.progress_callback = progress_callback
    
    def _log_progress(self, message):
        """Registra progreso si hay callback disponible."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def _is_file_locked(self, filepath):
        """Verifica si un archivo está abierto/bloqueado en Windows."""
        if not os.path.exists(filepath):
            return False
        try:
            # Intenta abrir el archivo en modo exclusivo
            with open(filepath, 'rb') as f:
                pass
            return False
        except IOError:
            return True
    
    def _wait_for_file_release(self, filepath, max_attempts=10, delay=0.5):
        """Espera a que un archivo se libere (útil después de docx2pdf)."""
        for attempt in range(max_attempts):
            if not self._is_file_locked(filepath):
                return True
            time.sleep(delay)
        return False
    
    def _cleanup_temp_file(self, filepath):
        """Intenta eliminar un archivo temporal de forma robusta."""
        if not os.path.exists(filepath):
            return True
        
        try:
            # Esperar a que el archivo se libere
            if self._wait_for_file_release(filepath):
                os.remove(filepath)
                self._log_progress(f"✓ Archivo temporal limpiado: {filepath}")
                return True
        except Exception as e:
            self._log_progress(f"⚠ No se pudo eliminar temporal {filepath}: {str(e)}")
        
        return False
    
    def _check_pdf_exists_and_locked(self, pdf_path):
        """Verifica si el PDF ya existe y está abierto."""
        if os.path.exists(pdf_path):
            if self._is_file_locked(pdf_path):
                raise PermissionError(
                    f"El PDF '{os.path.basename(pdf_path)}' está abierto. "
                    "Ciérrelo antes de generar un nuevo acta."
                )
            else:
                self._log_progress(f"⚠ Sobreescribiendo PDF existente: {pdf_path}")
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    raise PermissionError(f"No se pudo eliminar el PDF anterior: {str(e)}")
    
    def build(self, header, meds, firma_data, id_entrega):
        """Genera el PDF del acta de entrega.
        
        Args:
            header: Datos del encabezado (paciente, admisión, etc)
            meds: Lista de medicamentos entregados
            firma_data: Datos de la firma digital del paciente
            id_entrega: Identificador único de la entrega
            
        Returns:
            str: Ruta del PDF generado
            
        Raises:
            FileNotFoundError: Si no existe la plantilla Word
            PermissionError: Si el PDF de salida está abierto
            Exception: Si hay errores COM o en la conversión a PDF
        """
        base_path = os.path.dirname(os.path.abspath(__file__))
        template_name = "ACTA_MEDICAMENTOS.docx"
        template_path = os.path.join(base_path, template_name)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"No se encontró la plantilla en: {template_path}")
        
        temp_word = os.path.join(base_path, f"temp_{id_entrega}.docx")
        pdf_final = os.path.join(base_path, f"Acta_Entrega_{header.IdUsuario}_{id_entrega}.pdf")
        
        try:
            # 1. Validar que el PDF de salida no esté abierto
            self._log_progress("Validando archivo de salida...")
            self._check_pdf_exists_and_locked(pdf_final)
            
            # 2. Cargar plantilla y generar DOCX
            self._log_progress("Cargando plantilla Word...")
            doc = DocxTemplate(template_path)
            
            # Procesamiento de la firma
            self._log_progress("Procesando firma digital...")
            img_firma = None
            if firma_data and firma_data.imagenFirma:
                img_stream = io.BytesIO(firma_data.imagenFirma)
                img_firma = InlineImage(doc, img_stream, width=Mm(45))
            
            # Mapeo de campos
            context = {
                'hc': header.NoHistoria,
                'paciente': header.PacienteCompleto,
                'doc_id': header.IdUsuario,
                'sede': header.NombreInstitucion,
                'funcionario': header.FuncionarioNombre,
                'id_entrega': id_entrega,
                'admision': header.IdAdmision if hasattr(header, 'IdAdmision') else id_entrega,
                'fecha_firma': firma_data.fechaFirma.strftime('%d/%m/%Y %H:%M') if firma_data else "",
                'medicamentos': [
                    {
                        'nombre': m.nomSuministro,
                        'lote': m.numeroLote,
                        'orden': m.NumeroOrden,
                        'entregado': m.cantidadEntregada,
                        'ordenado': m.CantidadFormulada,
                        'pendiente': m.CantidadFormulada - m.cantidadEntregada
                    } for m in meds
                ],
                'firma_paciente': img_firma
            }
            
            self._log_progress("Renderizando plantilla (Jinja2)...")
            doc.render(context)
            
            # 3. Guardar DOCX temporal
            self._log_progress("Guardando documento temporal...")
            doc.save(temp_word)
            
            # 4. Convertir DOCX a PDF con manejo de errores COM
            self._log_progress("Convirtiendo a PDF (esto puede tardar unos segundos)...")
            try:
                convert(temp_word, pdf_final)
            except Exception as com_error:
                # Errores típicos de docx2pdf: pywintypes.com_error
                error_msg = str(com_error).lower()
                if "com" in error_msg or "word" in error_msg:
                    raise Exception(
                        f"Error COM (Microsoft Word): {str(com_error)}\n"
                        "Posibles causas:\n"
                        "  • Microsoft Word no está instalado\n"
                        "  • Hay una instancia de Word bloqueada\n"
                        "  • Problemas de permisos en el sistema de archivos"
                    )
                else:
                    raise Exception(f"Error durante conversión PDF: {str(com_error)}")
            
            self._log_progress("✓ PDF generado exitosamente")
            
            return pdf_final
            
        finally:
            # SIEMPRE intentar limpiar el DOCX temporal, incluso si algo falla
            self._log_progress("Limpiando archivos temporales...")
            self._cleanup_temp_file(temp_word)