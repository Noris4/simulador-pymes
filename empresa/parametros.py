"""
empresa/parametros.py
Captura y validación de los 7 parámetros evaluables de la empresa.
Persistencia: diccionario en memoria (intercambiable por BD en el futuro).
"""

# Almacén en memoria: { empresa_id: dict }
_parametros: dict[str, dict] = {}

# Giros/sectores válidos para Baja California
GIROS_VALIDOS = [
    "comercio",
    "manufactura",
    "servicios",
    "tecnologia",
    "turismo",
    "agroindustria",
    "construccion",
    "salud",
    "educacion",
    "otro",
]


def validar_parametros(datos: dict) -> list[str]:
    """
    Valida los 7 parámetros evaluables.
    Retorna una lista de mensajes de error; lista vacía si todo es válido.
    """
    errores = []

    # 1. capital_inicial
    capital = datos.get("capital_inicial")
    if capital is None:
        errores.append("capital_inicial es requerido.")
    elif not isinstance(capital, (int, float)) or capital < 0:
        errores.append("capital_inicial debe ser un número positivo (en MXN).")

    # 2. giro_sector
    giro = datos.get("giro_sector")
    if giro is None:
        errores.append("giro_sector es requerido.")
    elif giro not in GIROS_VALIDOS:
        errores.append(f"giro_sector debe ser uno de: {', '.join(GIROS_VALIDOS)}.")

    # 3. num_empleados
    empleados = datos.get("num_empleados")
    if empleados is None:
        errores.append("num_empleados es requerido.")
    elif not isinstance(empleados, int) or empleados < 0:
        errores.append("num_empleados debe ser un entero positivo.")

    # 4. plan_ventas
    plan_ventas = datos.get("plan_ventas")
    if plan_ventas is None:
        errores.append("plan_ventas es requerido.")
    elif not isinstance(plan_ventas, str) or len(plan_ventas.strip()) < 10:
        errores.append("plan_ventas debe ser una descripción de al menos 10 caracteres.")

    # 5. plan_financiero
    plan_financiero = datos.get("plan_financiero")
    if plan_financiero is None:
        errores.append("plan_financiero es requerido.")
    elif not isinstance(plan_financiero, str) or len(plan_financiero.strip()) < 10:
        errores.append("plan_financiero debe ser una descripción de al menos 10 caracteres.")

    # 6. analisis_mercado
    analisis = datos.get("analisis_mercado")
    if analisis is None:
        errores.append("analisis_mercado es requerido.")
    elif not isinstance(analisis, str) or len(analisis.strip()) < 10:
        errores.append("analisis_mercado debe ser una descripción de al menos 10 caracteres.")

    # 7. registro_legal
    registro = datos.get("registro_legal")
    if registro is None:
        errores.append("registro_legal es requerido (true/false).")
    elif not isinstance(registro, bool):
        errores.append("registro_legal debe ser un booleano (true o false).")

    return errores


def guardar_parametros(empresa_id: str, datos: dict) -> dict:
    """
    Persiste los parámetros para la empresa indicada.
    Sobreescribe cualquier valor previo.
    Retorna los parámetros guardados.
    """
    _parametros[empresa_id] = {
        "empresa_id": empresa_id,
        "capital_inicial": datos["capital_inicial"],
        "giro_sector": datos["giro_sector"],
        "num_empleados": datos["num_empleados"],
        "plan_ventas": datos["plan_ventas"].strip(),
        "plan_financiero": datos["plan_financiero"].strip(),
        "analisis_mercado": datos["analisis_mercado"].strip(),
        "registro_legal": datos["registro_legal"],
    }
    return _parametros[empresa_id]


def obtener_parametros(empresa_id: str) -> dict | None:
    """
    Retorna los parámetros actuales de la empresa, o None si no existen.
    """
    return _parametros.get(empresa_id)


def parametros_completos(empresa_id: str) -> bool:
    """
    Retorna True si los 7 parámetros han sido guardados para la empresa.
    Es un prerequisito para iniciar la evaluación.
    """
    return empresa_id in _parametros
