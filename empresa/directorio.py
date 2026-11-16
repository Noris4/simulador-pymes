"""Directorio de prueba: ejemplos identificados y aprobaciones vigentes en memoria."""
from empresa import perfil, parametros, evaluacion

GIROS = {
    "tecnologia": "Tecnología", "comercio": "Comercio", "servicios": "Servicios",
    "manufactura": "Manufactura", "turismo": "Turismo", "agroindustria": "Agroindustria",
    "construccion": "Construcción", "salud": "Salud", "educacion": "Educación", "otro": "Otro",
}
NECESIDADES = {"financiamiento": "Financiamiento", "inversion": "Inversión", "empleados": "Personal"}

# No han sido evaluadas por IBM: son exclusivamente ejemplos para probar las tarjetas.
_EJEMPLOS = [
    ("Norte Digital", "tecnologia", 6, 92, "Software y automatización para pequeños comercios.", False, True, True),
    ("Café Bruma", "comercio", 8, 88, "Café de especialidad y pan de elaboración local.", True, False, True),
    ("Taller Forma", "manufactura", 12, 91, "Mobiliario modular para oficinas y espacios de trabajo.", True, True, True),
    ("Ruta Pacífico", "turismo", 5, 86, "Experiencias de naturaleza y recorridos en grupos pequeños.", False, True, False),
    ("Huerto Horizonte", "agroindustria", 14, 94, "Producción y distribución de hortalizas de temporada.", True, True, True),
    ("Obra Clara", "construccion", 18, 90, "Remodelación de locales con planeación y seguimiento de obra.", True, False, True),
    ("Bienestar Cercano", "salud", 7, 89, "Servicios de bienestar y atención preventiva para la comunidad.", False, True, True),
    ("Aula Abierta", "educacion", 4, 93, "Capacitación práctica en habilidades digitales para adultos.", False, False, True),
    ("Logística Faro", "servicios", 10, 87, "Coordinación de entregas locales para tiendas independientes.", True, True, True),
    ("Circular Baja", "manufactura", 9, 95, "Diseño de empaques reutilizables para negocios locales.", False, True, False),
    ("Mercado Raíz", "comercio", 3, 84, "Productos de proveedores regionales en un solo punto de venta.", True, False, False),
    ("Estudio Marea", "servicios", 2, 90, "Diseño de identidad y comunicación para emprendimientos.", False, False, False),
]


def listar_empresas():
    empresas = []
    for numero, (nombre, giro, empleados, nota, descripcion, financiamiento, inversion, personal) in enumerate(_EJEMPLOS):
        empresas.append({
            "empresa_id": f"ejemplo-{numero}", "nombre": nombre, "giro": giro,
            "num_empleados": empleados, "calificacion": nota, "descripcion": descripcion,
            "financiamiento": financiamiento, "inversion": inversion, "empleados": personal,
            "es_ejemplo": True,
        })
    for empresa_id, empresa in list(perfil._empresas.items()):
        permitido, _ = evaluacion.acceso_aprobado(empresa_id)
        if not permitido:
            continue
        params = parametros.obtener_parametros(empresa_id)
        ultima = evaluacion.obtener_historial_evaluaciones(empresa_id)[-1]
        oportunidades = empresa.get("oportunidades_directorio", {})
        empresas.append({
            "empresa_id": empresa_id, "nombre": empresa["nombre"], "giro": params["giro_sector"],
            "num_empleados": params["num_empleados"], "calificacion": ultima["calificacion"],
            "descripcion": oportunidades.get("descripcion", "Empresa con evaluación vigente aprobada en este programa."),
            **{clave: oportunidades.get(clave, False) for clave in NECESIDADES},
            "es_ejemplo": False,
        })
    return empresas


def filtrar_empresas(empresas, busqueda="", giro="", necesidad="", origen=""):
    busqueda = busqueda.strip().casefold()
    return [e for e in empresas
            if (not busqueda or busqueda in (e["nombre"] + " " + e["descripcion"] + " " + GIROS.get(e["giro"], e["giro"])).casefold())
            and (not giro or e["giro"] == giro)
            and (not necesidad or (necesidad in NECESIDADES and e.get(necesidad) is True))
            and (not origen or (origen == "ejemplos" and e["es_ejemplo"]) or (origen == "evaluadas" and not e["es_ejemplo"]))]


def guardar_oportunidades(empresa_id, datos):
    if not isinstance(datos, dict):
        return {"error": "Se esperaba un objeto con las oportunidades."}
    if any(type(datos.get(clave)) is not bool for clave in NECESIDADES):
        return {"error": "Indica sí o no para financiamiento, inversión y personal."}
    descripcion = datos.get("descripcion", "")
    if not isinstance(descripcion, str) or not 10 <= len(descripcion.strip()) <= 400:
        return {"error": "La descripción debe tener entre 10 y 400 caracteres."}
    empresa = perfil.obtener_empresa(empresa_id)
    if empresa is None:
        return {"error": "Empresa no encontrada."}
    empresa["oportunidades_directorio"] = {
        "descripcion": descripcion.strip(), **{clave: datos[clave] for clave in NECESIDADES},
    }
    return empresa["oportunidades_directorio"]
