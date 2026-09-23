"""
empresa/registro.py
Proceso de registro legal oficial de la empresa.

Solo es accesible para empresas que aprobaron la evaluación de viabilidad.
Genera un resumen estructurado con los datos necesarios para el trámite
ante las autoridades de Baja California.
"""

from datetime import datetime
from empresa import perfil as mod_perfil
from empresa import parametros as mod_parametros
from empresa import evaluacion as mod_evaluacion

# Estado de registro por empresa: { empresa_id: dict }
_registros: dict[str, dict] = {}


def verificar_elegibilidad_registro(empresa_id: str) -> tuple[bool, str]:
    """
    Verifica que la empresa cumple los prerequisitos para el registro:
      1. El perfil existe.
      2. Los parámetros están completos.
      3. La última evaluación tiene calificación aprobatoria.

    Retorna (elegible: bool, motivo: str).
    """
    empresa = mod_perfil.obtener_empresa(empresa_id)
    if empresa is None:
        return False, "El perfil de la empresa no existe."

    if not mod_parametros.parametros_completos(empresa_id):
        return False, "Los parámetros de evaluación no han sido completados."

    historial = mod_evaluacion.obtener_historial_evaluaciones(empresa_id)
    if not historial:
        return False, "La empresa aún no ha sido evaluada."

    ultima_evaluacion = historial[-1]
    if not ultima_evaluacion.get("aprobado", False):
        calificacion = ultima_evaluacion.get("calificacion", 0)
        return (
            False,
            f"La empresa no aprobó la evaluación (calificación: {calificacion:.1f}). "
            "Revisa el feedback y vuelve a intentarlo.",
        )

    return True, "La empresa es elegible para el registro."


def preparar_documento_registro(empresa_id: str) -> dict:
    """
    Compila todos los datos de la empresa en un resumen estructurado
    listo para el trámite oficial de registro.

    Retorna el documento o un dict con clave 'error' si la empresa
    no es elegible.
    """
    elegible, motivo = verificar_elegibilidad_registro(empresa_id)
    if not elegible:
        return {"error": motivo}

    empresa = mod_perfil.obtener_empresa(empresa_id)
    params = mod_parametros.obtener_parametros(empresa_id)
    historial = mod_evaluacion.obtener_historial_evaluaciones(empresa_id)
    ultima_evaluacion = historial[-1]

    documento = {
        "empresa_id": empresa_id,
        "nombre_empresa": empresa.get("nombre"),
        "giro_sector": empresa.get("giro") or params.get("giro_sector"),
        "fundador": empresa.get("fundador"),
        "curp_rfc": empresa.get("curp_rfc"),
        "capital_inicial_mxn": params.get("capital_inicial"),
        "num_empleados": params.get("num_empleados"),
        "calificacion_viabilidad": ultima_evaluacion.get("calificacion"),
        "fecha_evaluacion": ultima_evaluacion.get("fecha"),
        "fecha_documento": datetime.utcnow().isoformat(),
        "tramites_pendientes": [
            "Registro ante el SAT (RFC como actividad empresarial)",
            "Registro patronal en el IMSS (si aplica)",
            "Licencia de funcionamiento municipal en Baja California",
        ],
    }

    return documento


def confirmar_registro(empresa_id: str) -> dict:
    """
    Marca la empresa como oficialmente registrada.
    Solo puede ejecutarse si la empresa es elegible.
    Retorna el estado actualizado o un dict con clave 'error'.
    """
    elegible, motivo = verificar_elegibilidad_registro(empresa_id)
    if not elegible:
        return {"error": motivo}

    _registros[empresa_id] = {
        "empresa_id": empresa_id,
        "estado": "registrada",
        "fecha_registro": datetime.utcnow().isoformat(),
    }

    # Actualizar el estado en el perfil
    mod_perfil.actualizar_empresa(empresa_id, {"estado": "registrada"})

    return _registros[empresa_id]


def obtener_estado_registro(empresa_id: str) -> dict:
    """
    Retorna el estado actual del proceso de registro de la empresa.
    """
    if empresa_id in _registros:
        return _registros[empresa_id]

    elegible, motivo = verificar_elegibilidad_registro(empresa_id)
    return {
        "empresa_id": empresa_id,
        "estado": "pendiente",
        "elegible": elegible,
        "motivo": motivo,
    }
