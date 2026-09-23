"""
empresa/guia.py
Guía paso a paso para la creación de una empresa en Baja California.
Los pasos son fijos y definidos con base en la investigación local.
El progreso del usuario se almacena en memoria por empresa_id.
"""

# Pasos fijos del proceso de creación de empresa en Baja California
_PASOS: list[dict] = [
    {
        "paso_id": 1,
        "titulo": "Definir nombre y giro de la empresa",
        "descripcion": (
            "Elige el nombre comercial y la actividad principal de tu empresa. "
            "El nombre no debe estar registrado previamente ante el SAT o el IMPI."
        ),
        "documentos_requeridos": [],
    },
    {
        "paso_id": 2,
        "titulo": "Tramitar CURP y RFC del fundador",
        "descripcion": (
            "Obtén tu CURP en la SEGOB y tu RFC en el SAT. "
            "Son indispensables para cualquier trámite fiscal y legal."
        ),
        "documentos_requeridos": ["CURP", "Identificación oficial"],
    },
    {
        "paso_id": 3,
        "titulo": "Elaborar el plan de negocios",
        "descripcion": (
            "Redacta tu plan de ventas, plan financiero y análisis de mercado. "
            "Estos documentos son requeridos para la evaluación de viabilidad."
        ),
        "documentos_requeridos": ["Plan de ventas", "Plan financiero", "Análisis de mercado"],
    },
    {
        "paso_id": 4,
        "titulo": "Determinar el capital inicial y número de empleados",
        "descripcion": (
            "Define cuánto capital inicial aportarás y cuántas personas empleará tu empresa "
            "desde el inicio. Estos datos afectan la forma legal de constitución."
        ),
        "documentos_requeridos": [],
    },
    {
        "paso_id": 5,
        "titulo": "Evaluación de viabilidad",
        "descripcion": (
            "Tu empresa será evaluada con base en los 7 parámetros clave. "
            "Debes obtener una calificación aprobatoria para continuar al registro oficial."
        ),
        "documentos_requeridos": [],
    },
    {
        "paso_id": 6,
        "titulo": "Registro ante el SAT como persona moral o física con actividad empresarial",
        "descripcion": (
            "Acude o ingresa al portal del SAT para inscribir tu empresa en el Registro Federal "
            "de Contribuyentes (RFC) como actividad empresarial."
        ),
        "documentos_requeridos": ["RFC del fundador", "Comprobante de domicilio", "Acta constitutiva (si aplica)"],
    },
    {
        "paso_id": 7,
        "titulo": "Registro en el IMSS (si tienes empleados)",
        "descripcion": (
            "Si tu empresa tiene al menos un empleado, debes registrarla como patrón ante el IMSS "
            "y afiliar a tus trabajadores."
        ),
        "documentos_requeridos": ["RFC de la empresa", "CURP del patrón", "Comprobante de domicilio fiscal"],
    },
    {
        "paso_id": 8,
        "titulo": "Obtener licencia de funcionamiento municipal",
        "descripcion": (
            "Tramita la licencia de funcionamiento ante el Ayuntamiento de tu municipio en Baja California. "
            "El trámite varía según el giro y la ubicación del negocio."
        ),
        "documentos_requeridos": ["RFC", "Comprobante de domicilio del negocio", "Identificación oficial"],
    },
]

# Progreso por empresa: { empresa_id: set(paso_id completados) }
_progreso: dict[str, set] = {}


def obtener_pasos() -> list[dict]:
    """
    Retorna la lista completa de pasos del proceso de creación de empresa.
    """
    return _PASOS


def obtener_paso(paso_id: int) -> dict | None:
    """
    Retorna el detalle de un paso específico por su ID, o None si no existe.
    """
    for paso in _PASOS:
        if paso["paso_id"] == paso_id:
            return paso
    return None


def marcar_paso_completado(empresa_id: str, paso_id: int) -> dict:
    """
    Registra un paso como completado para la empresa indicada.
    Retorna el estado actualizado del progreso.
    """
    if empresa_id not in _progreso:
        _progreso[empresa_id] = set()
    _progreso[empresa_id].add(paso_id)
    return obtener_progreso(empresa_id)


def obtener_progreso(empresa_id: str) -> dict:
    """
    Retorna el progreso del usuario: pasos completados, total de pasos y porcentaje.
    """
    completados = _progreso.get(empresa_id, set())
    total = len(_PASOS)
    return {
        "empresa_id": empresa_id,
        "pasos_completados": sorted(completados),
        "total_pasos": total,
        "porcentaje": round(len(completados) / total * 100, 1) if total > 0 else 0,
    }
