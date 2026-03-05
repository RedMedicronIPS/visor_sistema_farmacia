import pyodbc
from config import CONN_STR

class DataManager:
    """Gestor de datos con conexión a SQL Server.
    
    Maneja todas las consultas a las bases de datos SIFacturacion y RedMedicronIPS.
    """
    
    def _get_connection(self):
        """Abre una conexión a SQL Server con manejo de errores.
        
        Raises:
            Exception: Si no puede conectarse al servidor SQL Server.
        """
        try:
            return pyodbc.connect(CONN_STR)
        except pyodbc.Error as e:
            error_code = e.args[0]
            if "28000" in str(error_code):
                raise Exception(
                    "Error de autenticación SQL Server.\n"
                    "Verifique usuario y contraseña en config.py"
                )
            elif "08001" in str(error_code) or "Connection" in str(e):
                raise Exception(
                    f"Error de conexión al servidor SQL Server (192.168.59.230).\n"
                    f"Verifique que el servidor esté disponible y accesible en la red local.\n\n"
                    f"Detalles: {str(e)}"
                )
            else:
                raise Exception(f"Error de conexión SQL Server: {str(e)}")
    
    def get_entregas(self, id_admision):
        """Busca las diferentes entregas asociadas a una admisión.
        
        Retorna UN SOLO registro por cada número de entrega con datos del funcionario.
        
        Args:
            id_admision (int o str): Identificador de la admisión.
            
        Returns:
            list: Lista de tuplas (numeroEntrega, fechaEntrega, funcionarioNombre).
            
        Raises:
            Exception: Si hay error de conexión o consulta SQL.
        """
        query = """
        SELECT DISTINCT 
            d.numeroEntrega, 
            MAX(d.fechaEntrega) as fechaEntrega,
            ISNULL(u.UsuarioNombre, 'N/A') as funcionarioNombre
        FROM RedMedicronIPS..DispensacionFarmaciaPGP d
        LEFT JOIN RedMedicronIPS..GeneralesUsuario u ON d.usuarioRegistra = u.id
        WHERE d.IdAdmision = ? AND d.estado = 0
        GROUP BY d.numeroEntrega, u.UsuarioNombre
        ORDER BY fechaEntrega DESC
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, (id_admision,)).fetchall()
                if not result:
                    return []
                return result
        except pyodbc.Error as e:
            if "Invalid column" in str(e):
                raise Exception(
                    "Error en la estructura de la tabla DispensacionFarmaciaPGP.\n"
                    "Verifique que existan las columnas: IdAdmision, numeroEntrega, fechaEntrega, estado"
                )
            else:
                raise Exception(f"Error en consulta de entregas: {str(e)}")

    def search_pacientes_by_documento(self, id_usuario):
        """Busca un paciente por número de documento.
        
        Args:
            id_usuario (str): Número de documento del paciente.
            
        Returns:
            tuple: (IdUsuario, NombrePaciente, NoHistoria) o None si no existe.
            
        Raises:
            Exception: Si hay error en la consulta.
        """
        query = """
        SELECT TOP 1 
            p.IdUsuario,
            RTRIM(p.PApellido) + ' ' + RTRIM(ISNULL(p.SApellido,'')) + ' ' + 
            RTRIM(p.PNombre) + ' ' + RTRIM(ISNULL(p.SNombre,'')) as NombrePaciente,
            p.NoHistoria
        FROM SIFacturacion..mPacientes p
        WHERE p.IdUsuario = ?
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, (id_usuario,)).fetchone()
                return result
        except pyodbc.Error as e:
            raise Exception(f"Error al buscar paciente: {str(e)}")

    def get_admisiones_with_entregas(self, id_usuario):
        """Obtiene SOLO las admisiones que tienen entregas registradas.
        
        Args:
            id_usuario (str): Número de documento del paciente.
            
        Returns:
            list: Lista de tuplas (IdAdmision, FechaIngreso, NumeroEntregas).
            
        Raises:
            Exception: Si hay error en la consulta.
        """
        query = """
        SELECT 
            a.IdAdmision,
            CONVERT(VARCHAR(10), a.FechaIngreso, 120) as FechaIngreso,
            COUNT(DISTINCT d.numeroEntrega) as NumeroEntregas
        FROM SIFacturacion..mAdmisiones a
        INNER JOIN RedMedicronIPS..DispensacionFarmaciaPGP d ON a.IdAdmision = d.IdAdmision
        WHERE a.IdUsuario = ? AND d.estado = 0
        GROUP BY a.IdAdmision, a.FechaIngreso
        HAVING COUNT(DISTINCT d.numeroEntrega) > 0
        ORDER BY a.FechaIngreso DESC
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, (id_usuario,)).fetchall()
                return result if result else []
        except pyodbc.Error as e:
            raise Exception(f"Error al obtener admisiones: {str(e)}")

    def get_datos_completos(self, id_admision, n_entrega):
        """Obtiene todos los datos necesarios para generar el acta de entrega.
        
        Realiza 3 consultas SQL:
        1. Encabezado (datos del paciente, institución, funcionario)
        2. Medicamentos entregados vs formulados
        3. Firma digital del paciente
        
        Args:
            id_admision (int o str): Identificador de la admisión.
            n_entrega (int o str): Número de la entrega.
            
        Returns:
            tuple: (header, medicamentos, firma) donde cada uno es resultado de fetchone() o fetchall().
            
        Raises:
            Exception: Si hay error de conexión o consulta SQL.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # CONSULTA 1: Encabezado (datos maestros del paciente)
                header_sql = """
                SELECT TOP 1 
                    p.NoHistoria, 
                    RTRIM(p.PApellido) + ' ' + RTRIM(ISNULL(p.SApellido,'')) + ' ' + 
                    RTRIM(p.PNombre) + ' ' + RTRIM(ISNULL(p.SNombre,'')) as PacienteCompleto,
                    p.IdUsuario, 
                    s.NombreInstitucion, 
                    u.UsuarioNombre as FuncionarioNombre,
                    d.IdAdmision
                FROM RedMedicronIPS..DispensacionFarmaciaPGP d
                INNER JOIN SIFacturacion..mAdmisiones a ON d.IdAdmision = a.IdAdmision
                INNER JOIN SIFacturacion..mPacientes p ON a.IdUsuario = p.IdUsuario 
                INNER JOIN SIFacturacion..cAdministracion s ON a.IdSede = s.IdSede
                INNER JOIN RedMedicronIPS..GeneralesUsuario u ON d.usuarioRegistra = u.id
                WHERE d.IdAdmision = ? AND d.numeroEntrega = ?
                """
                header = cursor.execute(header_sql, (id_admision, n_entrega)).fetchone()
                
                if not header:
                    raise Exception(
                        f"No se encontraron datos para Admisión {id_admision}, Entrega {n_entrega}.\n"
                        "Verifique que la admisión tenga dispensaciones registradas."
                    )

                # CONSULTA 2: Medicamentos (Compara Entregado vs Formulado)
                meds_sql = """
                SELECT 
                    d.nomSuministro, 
                    d.numeroLote, 
                    d.NumeroOrden, 
                    d.cantidadEntregada, 
                    ISNULL(oe.Cantidad, 0) as CantidadFormulada
                FROM RedMedicronIPS..DispensacionFarmaciaPGP d
                LEFT JOIN SIFacturacion..dHCOrdenesExternas oe ON d.IdAdmision = oe.IdAdmision 
                     AND d.NumeroOrden = oe.NoOrden AND d.codSuministro = oe.CodServicio
                WHERE d.IdAdmision = ? AND d.numeroEntrega = ? AND d.estado = 0
                ORDER BY d.nomSuministro
                """
                medicamentos = cursor.execute(meds_sql, (id_admision, n_entrega)).fetchall()

                # CONSULTA 3: Firma del Paciente
                firma_sql = """
                SELECT imagenFirma, fechaFirma, idAdmision 
                FROM RedMedicronIPS..DispensacionFarmaciaPGPFirmaRecibido 
                WHERE idAdmision = ? AND idFirma = ?
                """
                firma = cursor.execute(firma_sql, (id_admision, n_entrega)).fetchone()

                return header, medicamentos, firma
                
        except pyodbc.Error as e:
            if "Invalid object name" in str(e):
                raise Exception(
                    f"Una de las tablas no existe o no tiene permisos de lectura.\n"
                    f"Error: {str(e)}"
                )
            else:
                raise Exception(f"Error en consulta de datos completos: {str(e)}")
        except Exception as e:
            # Re-lanzar excepciones que ya tenemos contexto
            if "No se encontraron datos" in str(e):
                raise
            # Envolver otras excepciones
            raise Exception(f"Error inesperado al obtener datos: {str(e)}")

    def get_sedes(self):
        """Obtiene la lista de todas las sedes disponibles.
        
        Returns:
            list: Lista de tuplas (IdSedeSI, SedeNombre).
            
        Raises:
            Exception: Si hay error en la consulta.
        """
        query = """SELECT IdSedeSI, SedeNombre FROM RedMedicronIPS..GeneralesSede ORDER BY SedeNombre"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query).fetchall()
                return result if result else []
        except pyodbc.Error as e:
            raise Exception(f"Error al obtener sedes: {str(e)}")

    def get_all_entregas_by_cedula(self, id_usuario, id_sede=None):
        """Obtiene TODAS las entregas (UNA SOLA por número de entrega) de un paciente por cédula.
        
        Args:
            id_usuario (str): Número de documento del paciente.
            id_sede (int): ID de sede para filtrar (opcional).
            
        Returns:
            list: Lista de tuplas (IdAdmision, numeroEntrega, fechaEntrega, IdUsuario, nombrePaciente, SedeNombre).
            
        Raises:
            Exception: Si hay error en la consulta.
        """
        query = """
        SELECT
            rn.IdAdmision,
            rn.numeroEntrega,
            CAST(rn.fechaEntrega AS DATE) as fechaEntrega,
            p.IdUsuario,
            RTRIM(p.PApellido) + ' ' + RTRIM(ISNULL(p.SApellido,'')) + ' ' + 
            RTRIM(p.PNombre) + ' ' + RTRIM(ISNULL(p.SNombre,'')) as nombrePaciente,
            ISNULL(s.SedeNombre, 'N/A') as SedeNombre
        FROM (
            SELECT 
                d.IdAdmision,
                d.numeroEntrega,
                d.fechaEntrega,
                d.idSede,
                a.IdUsuario,
                ROW_NUMBER() OVER (PARTITION BY d.numeroEntrega ORDER BY d.fechaEntrega DESC, d.IdAdmision DESC) as rn
            FROM RedMedicronIPS..DispensacionFarmaciaPGP d
            INNER JOIN SIFacturacion..mAdmisiones a ON d.IdAdmision = a.IdAdmision
            WHERE a.IdUsuario = ? AND d.estado = 0
        ) rn
        INNER JOIN SIFacturacion..mPacientes p ON rn.IdUsuario = p.IdUsuario
        LEFT JOIN RedMedicronIPS..GeneralesSede s ON rn.idSede = s.IdSedeSI
        WHERE rn.rn = 1
        """ + (f"AND rn.idSede = {id_sede} " if id_sede else "") + """
        ORDER BY rn.fechaEntrega DESC
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, (id_usuario,)).fetchall()
                return result if result else []
        except pyodbc.Error as e:
            raise Exception(f"Error al obtener entregas masivas por cédula: {str(e)}")

    def get_entregas_by_date_range(self, start_date, end_date, id_sede=None):
        """Obtiene TODAS las entregas en un rango de fechas (UNA SOLA por número de entrega).
        
        Args:
            start_date (str): Fecha inicio en formato 'YYYY-MM-DD'.
            end_date (str): Fecha fin en formato 'YYYY-MM-DD'.
            id_sede (int): ID de sede para filtrar (opcional).
            
        Returns:
            list: Lista de tuplas con los datos de entregas en el período.
            
        Raises:
            Exception: Si hay error en la consulta.
        """
        query = """
        SELECT
            rn.IdAdmision,
            rn.numeroEntrega,
            CAST(rn.fechaEntrega AS DATE) as fechaEntrega,
            p.IdUsuario,
            RTRIM(p.PApellido) + ' ' + RTRIM(ISNULL(p.SApellido,'')) + ' ' + 
            RTRIM(p.PNombre) + ' ' + RTRIM(ISNULL(p.SNombre,'')) as nombrePaciente,
            ISNULL(s.SedeNombre, 'N/A') as SedeNombre
        FROM (
            SELECT 
                d.IdAdmision,
                d.numeroEntrega,
                d.fechaEntrega,
                d.idSede,
                a.IdUsuario,
                ROW_NUMBER() OVER (PARTITION BY d.numeroEntrega ORDER BY d.fechaEntrega DESC, d.IdAdmision DESC) as rn
            FROM RedMedicronIPS..DispensacionFarmaciaPGP d
            INNER JOIN SIFacturacion..mAdmisiones a ON d.IdAdmision = a.IdAdmision
            WHERE CAST(d.fechaEntrega AS DATE) BETWEEN ? AND ? AND d.estado = 0
        ) rn
        INNER JOIN SIFacturacion..mPacientes p ON rn.IdUsuario = p.IdUsuario
        LEFT JOIN RedMedicronIPS..GeneralesSede s ON rn.idSede = s.IdSedeSI
        WHERE rn.rn = 1
        """ + (f"AND rn.idSede = {id_sede} " if id_sede else "") + """
        ORDER BY rn.fechaEntrega DESC
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = cursor.execute(query, (start_date, end_date)).fetchall()
                return result if result else []
        except pyodbc.Error as e:
            raise Exception(f"Error al obtener entregas por rango de fechas: {str(e)}")