import os
import io
import sys
import time
import imghdr
import subprocess
import gc
from pathlib import Path
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import win32com.client

# HTML rendering and conversion
from jinja2 import Environment, FileSystemLoader
import base64

# PDF conversion library (pure Python)
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None  # will be checked at runtime


# detectar si Word está disponible (intenta iniciar y salir)
def _word_installed() -> bool:
    try:
        app = win32com.client.gencache.EnsureDispatch('Word.Application')
        app.Quit()
        return True
    except Exception:
        return False


# conversión DOCX→PDF usando COM directamente en lugar de docx2pdf;
# esto evita problemas dentro de un ejecutable "onefile" donde la
# biblioteca docx2pdf puede comportarse mal.
def _convert_with_word(input_path: str, output_path: str):
    """Convierte DOCX a PDF usando Microsoft Word via COM.
    
    Args:
        input_path: Ruta al archivo .docx
        output_path: Ruta donde guardar el PDF
    """
    # convertir a rutas absolutas para evitar problemas de resolución
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo: {input_path}")
    
    wdFormatPDF = 17
    word = None
    doc = None
    
    try:
        # crear instancia de Word con opciones específicas
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = False  # suprimir diálogos
        
        # abrir documento con parámetros explícitos
        doc = word.Documents.Open(
            FileName=input_path,
            ReadOnly=False,
            AddToRecentFiles=False,
            ConfirmConversions=False
        )
        
        # guardar como PDF
        doc.SaveAs(
            FileName=output_path,
            FileFormat=wdFormatPDF,
            AddToRecentFiles=False
        )
        
        # cerrar documento sin guardar (ya se guardó como PDF)
        doc.Close(SaveChanges=False)
        doc = None
        
        # espera significativa para que termine la escritura a disco
        time.sleep(1.0)
        
        # cerrar Word
        word.Quit(SaveChanges=False)
        word = None
        
        # fuerza liberación de referencias en Python
        import gc
        gc.collect()
        
        # pequeña pausa adicional para que Word termine completamente
        time.sleep(0.5)
        
    except Exception as e:
        # limpiar recursos en caso de error
        if doc:
            try:
                doc.Close(SaveChanges=False)
            except:
                pass
        if word:
            try:
                word.Quit(SaveChanges=False)
            except:
                pass
        
        # forzar liberación
        import gc
        gc.collect()
        time.sleep(0.5)
        
        raise Exception(f"Error en conversión COM: {str(e)}")
    
    finally:
        # como medida final, intenta matar procesos Word zombie si los hay
        import subprocess
        try:
            subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL,
                          timeout=2)
        except:
            pass


def _resource_path(relative_path: str) -> str:
    """Resuelve la ruta de recursos, funciona en dev y en bundle de PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)

class ReportGenerator:
    def __init__(self, progress_callback=None):
        """Inicializa el generador de reportes.
        
        Args:
            progress_callback: Función para reportar progreso (ej: lambda msg: print(msg))
        """
        self.progress_callback = progress_callback
    
    def _log_progress(self, message):
        """Registra progreso si hay callback disponible.
        Se protege contra errores de codificación (por ejemplo cuando la
        consola no soporta caracteres Unicode como ✓) para evitar que la
        aplicación se bloquee durante el registro de mensajes.
        """
        try:
            if self.progress_callback:
                self.progress_callback(message)
            else:
                print(message)
        except Exception:
            # último recurso: intentar imprimir reemplazando los caracteres
            try:
                print(message.encode('utf-8', 'backslashreplace').decode('ascii'))
            except Exception:
                pass
    
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
    
    def build(self, header, meds, firma_data, id_entrega, output_folder=None, is_bulk=False):
        """Genera el PDF del acta de entrega.
        
        Args:
            header: Datos del encabezado (paciente, admisión, etc)
            meds: Lista de medicamentos entregados
            firma_data: Datos de la firma digital del paciente
            id_entrega: Identificador único de la entrega
            output_folder: Ruta de carpeta de salida (opcional, usa carpeta actual si es None)
            is_bulk: Si es True, no abre automáticamente el PDF (para descarga masiva)
            
        Returns:
            str: Ruta del PDF generado
            
        Raises:
            FileNotFoundError: Si no existe la plantilla Word
            PermissionError: Si el PDF de salida está abierto
            Exception: Si hay errores COM o en la conversión a PDF
        """
        base_path = output_folder if output_folder else os.path.dirname(os.path.abspath(__file__))
        # elegir método -> HTML si existe, de lo contrario Word
        html_template = _resource_path(os.path.join('templates', 'acta_entrega.html'))
        word_template = _resource_path("ACTA_MEDICAMENTOS.docx")

        # Nombre único del PDF con timestamp para evitar conflictos
        import time
        timestamp = int(time.time() * 1000) % 1000000  # Micro timestamp único
        temp_word = os.path.join(base_path, f"temp_{id_entrega}_{timestamp}.docx")
        pdf_final = os.path.join(base_path, f"Acta_Entrega_{header.IdUsuario}_{id_entrega}.pdf")

        # helper to turn image file OR binary data into base64 data URI
        def _img_datauri(data):
            if data is None:
                return ''
            
            # Si es bytes (BLOB binario de BD), convertir directamente
            if isinstance(data, bytes):
                import imghdr
                img_type = imghdr.what(None, h=data)
                mime = f'image/{img_type}' if img_type else 'image/png'
                b64_data = base64.b64encode(data).decode('ascii')
                return f"data:{mime};base64,{b64_data}"
            
            # Si es string (ruta de archivo)
            if isinstance(data, str):
                if not os.path.exists(data):
                    return ''
                ext = os.path.splitext(data)[1].lstrip('.').lower()
                mime = 'image/png' if ext == 'png' else 'image/jpeg' if ext in ('jpg','jpeg') else 'image/png'
                with open(data, 'rb') as f:
                    b64_data = base64.b64encode(f.read()).decode('ascii')
                return f"data:{mime};base64,{b64_data}"
            
            return ''

        try:
            # 1. Validar que el PDF de salida no esté abierto
            self._log_progress("Validando archivo de salida...")
            self._check_pdf_exists_and_locked(pdf_final)

            if os.path.exists(html_template):
                # procesa usando plantilla HTML
                self._log_progress("Generando acta a partir de plantilla HTML...")
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
                    'logo1': _img_datauri(_resource_path(os.path.join('public','logoRedMedicronIPS.png'))),
                    'logo2': _img_datauri(_resource_path(os.path.join('public','logoRedMedicronIPS.png'))),
                    'logo_pie': _img_datauri(_resource_path(os.path.join('public','piedepagina.png'))),
                    'firma_paciente': _img_datauri(firma_data.imagenFirma) if firma_data and firma_data.imagenFirma else ''
                }
                env = Environment(loader=FileSystemLoader(os.path.dirname(html_template)))
                tpl = env.get_template(os.path.basename(html_template))
                html = tpl.render(context)

                if pisa is None:
                    raise ImportError("La librería xhtml2pdf no está instalada. Instale 'xhtml2pdf' para usar la plantilla HTML.")
                with open(pdf_final, 'wb') as pdf_file:
                    result = pisa.CreatePDF(io.StringIO(html), dest=pdf_file)
                    if result.err:
                        raise Exception(f"Error al convertir HTML a PDF: {result.err}")

                self._log_progress("✓ PDF generado exitosamente (HTML)")
                if not is_bulk and sys.platform == "win32":
                    try:
                        os.startfile(pdf_final)
                    except Exception as e:
                        self._log_progress(f"⚠ No se pudo abrir el PDF automáticamente: {str(e)}")
                return pdf_final
            else:
                # plantilla Word (ruta legacy)
                if not os.path.exists(word_template):
                    raise FileNotFoundError(f"No se encontró la plantilla en: {word_template}")
                self._log_progress("Cargando plantilla Word...")
                doc = DocxTemplate(word_template)
                self._log_progress("Procesando firma digital...")
                img_firma = None
                if firma_data and firma_data.imagenFirma:
                    img_stream = io.BytesIO(firma_data.imagenFirma)
                    img_firma = InlineImage(doc, img_stream, width=Mm(45))
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
                self._log_progress("Guardando documento temporal...")
                doc.save(temp_word)
                if not _word_installed():
                    raise Exception(
                        "Microsoft Word no está instalado o no se puede iniciar. "
                        "La conversión a PDF requiere Word."
                    )
                self._log_progress("Convirtiendo a PDF (esto puede tardar unos segundos)...")
                try:
                    _convert_with_word(temp_word, pdf_final)
                except Exception as com_error:
                    error_msg = str(com_error).lower()
                    if "com" in error_msg or "word" in error_msg or "nonetype" in error_msg:
                        raise Exception(
                            f"Error COM (Microsoft Word): {str(com_error)}\n"
                            "Posibles causas:\n"
                            "  • Microsoft Word no está instalado o no es accesible\n"
                            "  • Hay una instancia de Word bloqueada\n"
                            "  • El usuario no tiene permisos para automatizar Word\n"
                        )
                    else:
                        raise Exception(f"Error durante conversión PDF: {str(com_error)}")
                self._log_progress("✓ PDF generado exitosamente")
                if not is_bulk and sys.platform == "win32":
                    try:
                        os.startfile(pdf_final)
                    except Exception as e:
                        self._log_progress(f"⚠ No se pudo abrir el PDF automáticamente: {str(e)}")
                return pdf_final

        finally:
            # SIEMPRE intentar limpiar el DOCX temporal, incluso si algo falla
            self._log_progress("Limpiando archivos temporales...")
            self._cleanup_temp_file(temp_word)