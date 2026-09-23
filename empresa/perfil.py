"""
empresa/perfil.py
Gestión del perfil básico de la empresa.
Persistencia: diccionario en memoria (intercambiable por BD en el futuro).
"""

import uuid
from datetime import datetime

# Almacén en memoria: { empresa_id: dict }
_empresas: dict[str, dict] = {}


def crear_empresa(datos: dict) -> dict:
    """
    Crea un nuevo perfil de empresa.

    Parámetros esperados en `datos`:
        - nombre (str): Nombre comercial de la empresa.
        - giro (str): Sector o giro de la empresa.
        - fundador (str): Nombre completo del fundador.
        - curp_rfc (str, opcional): CURP o RFC del fundador.

    Retorna el perfil creado con su empresa_id generado.
    """
    empresa_id = str(uuid.uuid4())
    perfil = {
        "empresa_id": empresa_id,
        "nombre": datos.get("nombre", ""),
        "giro": datos.get("giro", ""),
        "fundador": datos.get("fundador", ""),
        "curp_rfc": datos.get("curp_rfc", ""),
        "fecha_creacion": datetime.utcnow().isoformat(),
        "estado": "en_proceso",  # posibles: en_proceso | aprobado | registrado
    }
    _empresas[empresa_id] = perfil
    return perfil


def obtener_empresa(empresa_id: str) -> dict | None:
    """
    Retorna el perfil de la empresa o None si no existe.
    """
    return _empresas.get(empresa_id)


def actualizar_empresa(empresa_id: str, datos: dict) -> dict | None:
    """
    Actualiza los campos del perfil indicados en `datos`.
    No permite modificar empresa_id ni fecha_creacion.
    Retorna el perfil actualizado o None si la empresa no existe.
    """
    empresa = _empresas.get(empresa_id)
    if empresa is None:
        return None

    campos_protegidos = {"empresa_id", "fecha_creacion"}
    for clave, valor in datos.items():
        if clave not in campos_protegidos:
            empresa[clave] = valor

    return empresa
