from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env", encoding="utf-8-sig")

import os
import secrets
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from empresa import perfil, guia, parametros, evaluacion, registro, tramitologia
from empresa import directorio
from empresa import documentos, informes_pdf

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    return jsonify({'error': 'El archivo supera el límite de 10 MB permitido para importar.'}), 413


@app.before_request
def proteger_pasos_avanzados():
    paginas = {"tramitologia_page", "registro_page"}
    endpoints = {"route_tramitologia", "route_documento_registro", "route_confirmar_registro", "route_estado_registro", "route_guardar_oportunidades"}
    es_pagina = request.endpoint in paginas
    paso = (request.view_args or {}).get("paso_id", 0)
    es_api = request.endpoint in endpoints or (request.endpoint == "route_marcar_paso_completado" and paso >= 4)
    if not es_pagina and not es_api:
        return None
    activa = session.get("empresa_id")
    empresa_id = activa if es_pagina or request.endpoint == "route_guardar_oportunidades" else (request.view_args or {}).get("empresa_id")
    if not activa or empresa_id != activa:
        permitido, motivo = False, "Crea una empresa en esta sesión y aprueba su evaluación rigurosa."
    else:
        permitido, motivo = evaluacion.acceso_aprobado(empresa_id)
    if not permitido:
        if es_pagina:
            return redirect(url_for("evaluacion_page", bloqueo="evaluacion"))
        return jsonify({"error": motivo, "estado": "bloqueado"}), 403


# ── Páginas HTML ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("bienvenida.html")


@app.route("/registrar-empresa")
def registrar_empresa_page():
    return render_template("index.html")

@app.route("/parametros-page")
def parametros_page():
    return render_template("parametros.html")

@app.route("/evaluacion-page")
def evaluacion_page():
    return render_template("evaluacion.html")

@app.route("/tramitologia-page")
def tramitologia_page():
    return render_template("tramitologia.html")

@app.route("/registro-page")
def registro_page():
    return render_template("registro.html")


@app.route("/directorio-page")
def directorio_page():
    empresas = directorio.listar_empresas()
    filtros = {"q": request.args.get("q", "")[:200], "giro": request.args.get("giro", ""),
               "necesidad": request.args.get("necesidad", ""), "origen": request.args.get("origen", "")}
    filtradas = directorio.filtrar_empresas(empresas, filtros["q"], filtros["giro"], filtros["necesidad"], filtros["origen"])
    empresa_id = session.get("empresa_id")
    activa = perfil.obtener_empresa(empresa_id) or {}
    puede_editar, _ = evaluacion.acceso_aprobado(empresa_id)
    return render_template("directorio.html", empresas=filtradas, filtros=filtros,
                           total_evaluadas=sum(not e["es_ejemplo"] for e in empresas),
                           total_ejemplos=sum(e["es_ejemplo"] for e in empresas),
                           total_giros=len({e["giro"] for e in empresas}),
                           giros=directorio.GIROS, necesidades=directorio.NECESIDADES,
                           oportunidades=activa.get("oportunidades_directorio", {}),
                           puede_editar=puede_editar,
                           editar=request.args.get("editar") == "1" or request.args.get("guardado") == "1")


@app.route("/empresa/activa/oportunidades", methods=["PUT"])
def route_guardar_oportunidades():
    resultado = directorio.guardar_oportunidades(session["empresa_id"], request.get_json(force=True))
    return jsonify(resultado), 400 if "error" in resultado else 200


# ── Perfil ──────────────────────────────────────────────────────────────────

@app.route("/empresa", methods=["POST"])
def route_crear_empresa():
    datos = request.get_json(force=True)
    resultado = perfil.crear_empresa(datos)
    session["empresa_id"] = resultado["empresa_id"]
    return jsonify(resultado), 201


@app.route("/empresa/<empresa_id>", methods=["GET"])
def route_obtener_empresa(empresa_id):
    resultado = perfil.obtener_empresa(empresa_id)
    if resultado is None:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>", methods=["PUT"])
def route_actualizar_empresa(empresa_id):
    datos = request.get_json(force=True)
    resultado = perfil.actualizar_empresa(empresa_id, datos)
    if resultado is None:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(resultado)


# ── Guía de pasos ────────────────────────────────────────────────────────────

@app.route("/pasos", methods=["GET"])
def route_obtener_pasos():
    return jsonify(guia.obtener_pasos())


@app.route("/pasos/<int:paso_id>", methods=["GET"])
def route_obtener_paso(paso_id):
    resultado = guia.obtener_paso(paso_id)
    if resultado is None:
        return jsonify({"error": "Paso no encontrado"}), 404
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/pasos/<int:paso_id>/completar", methods=["POST"])
def route_marcar_paso_completado(empresa_id, paso_id):
    resultado = guia.marcar_paso_completado(empresa_id, paso_id)
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/progreso", methods=["GET"])
def route_obtener_progreso(empresa_id):
    return jsonify(guia.obtener_progreso(empresa_id))


# ── Parámetros ───────────────────────────────────────────────────────────────

@app.route("/empresa/<empresa_id>/parametros", methods=["POST"])
def route_guardar_parametros(empresa_id):
    datos = request.get_json(force=True)
    errores = parametros.validar_parametros(datos)
    if errores:
        return jsonify({"error": "Datos inválidos", "detalle": errores}), 400
    resultado = parametros.guardar_parametros(empresa_id, datos)
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/parametros", methods=["GET"])
def route_obtener_parametros(empresa_id):
    resultado = parametros.obtener_parametros(empresa_id)
    if resultado is None:
        return jsonify({"error": "Parámetros no encontrados"}), 404
    return jsonify(resultado)


@app.route('/empresa/<empresa_id>/importar-documento', methods=['POST'])
def route_importar_documento(empresa_id):
    if session.get('empresa_id') != empresa_id or perfil.obtener_empresa(empresa_id) is None:
        return jsonify({'error': 'Primero crea una empresa en esta sesión.'}), 403
    archivo = request.files.get('archivo')
    if archivo is None:
        return jsonify({'error': 'Selecciona un archivo PDF o Word .docx.'}), 400
    try:
        campos = documentos.importar_archivo(archivo, request.form.get('campo', ''))
    except documentos.ErrorDocumento as error:
        return jsonify({'error': str(error)}), 400
    return jsonify({'campos': campos, 'mensaje': 'Texto importado. Revísalo y pulsa Guardar para usarlo en la evaluación.'})


@app.route('/empresa/<empresa_id>/evaluaciones/<evaluacion_id>/pdf', methods=['GET'])
def route_descargar_evaluacion_pdf(empresa_id, evaluacion_id):
    if session.get('empresa_id') != empresa_id:
        return jsonify({'error': 'El informe pertenece a otra sesión.'}), 403
    resultado = next((r for r in evaluacion.obtener_historial_evaluaciones(empresa_id)
                      if r.get('evaluacion_id') == evaluacion_id and r.get('estado') == 'completada'), None)
    if resultado is None:
        return jsonify({'error': 'La evaluación ya no está disponible. Vuelve a evaluar para generar un informe nuevo.'}), 404
    nombre = resultado.get('nombre_empresa') or (perfil.obtener_empresa(empresa_id) or {}).get('nombre', 'Empresa')
    archivo = informes_pdf.crear_informe(resultado, nombre)
    return send_file(archivo, mimetype='application/pdf', as_attachment=True,
                     download_name=f'evaluacion-{evaluacion_id[:12]}.pdf', max_age=0)


@app.route('/ejemplo-prueba.pdf', methods=['GET'])
def descargar_ejemplo_pdf():
    archivo = Path(app.root_path) / 'ejemplos' / 'norte-continuo' / 'Norte-Continuo-TI.pdf'
    if not archivo.exists():
        return jsonify({'error': 'El documento de prueba todavía no está disponible.'}), 404
    return send_file(archivo, mimetype='application/pdf', as_attachment=True, download_name=archivo.name)


# ── Evaluación ───────────────────────────────────────────────────────────────

@app.route("/empresa/<empresa_id>/acceso", methods=["GET"])
def route_acceso(empresa_id):
    if session.get("empresa_id") != empresa_id:
        return jsonify({"permitido": False, "motivo": "Primero crea una empresa en esta sesión."})
    permitido, motivo = evaluacion.acceso_aprobado(empresa_id)
    return jsonify({"permitido": permitido, "motivo": motivo})


@app.route("/sesion/acceso", methods=["GET"])
def route_acceso_sesion():
    empresa_id = session.get("empresa_id")
    permitido, motivo = evaluacion.acceso_aprobado(empresa_id)
    return jsonify({"permitido": permitido, "motivo": motivo})

@app.route("/empresa/<empresa_id>/evaluar", methods=["POST"])
def route_evaluar_empresa(empresa_id):
    resultado = evaluacion.evaluar_empresa(empresa_id)
    if "error" in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/evaluaciones", methods=["GET"])
def route_historial_evaluaciones(empresa_id):
    return jsonify(evaluacion.obtener_historial_evaluaciones(empresa_id))


@app.route("/empresa/<empresa_id>/tramitologia", methods=["GET"])
def route_tramitologia(empresa_id):
    resultado = tramitologia.generar_tramitologia(empresa_id)
    if "error" in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)


# ── Registro ─────────────────────────────────────────────────────────────────

@app.route("/empresa/<empresa_id>/registro/documento", methods=["GET"])
def route_documento_registro(empresa_id):
    resultado = registro.preparar_documento_registro(empresa_id)
    if "error" in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/registro/confirmar", methods=["POST"])
def route_confirmar_registro(empresa_id):
    resultado = registro.confirmar_registro(empresa_id)
    if "error" in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/registro/estado", methods=["GET"])
def route_estado_registro(empresa_id):
    return jsonify(registro.obtener_estado_registro(empresa_id))


if __name__ == "__main__":
    app.run(debug=True)
