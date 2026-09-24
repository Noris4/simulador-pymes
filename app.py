from flask import Flask, jsonify, request, render_template
from empresa import perfil, guia, parametros, evaluacion, registro

app = Flask(__name__)


# ── Páginas HTML ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/parametros-page")
def parametros_page():
    return render_template("parametros.html")

@app.route("/evaluacion-page")
def evaluacion_page():
    return render_template("evaluacion.html")

@app.route("/registro-page")
def registro_page():
    return render_template("registro.html")


# ── Perfil ──────────────────────────────────────────────────────────────────

@app.route("/empresa", methods=["POST"])
def route_crear_empresa():
    datos = request.get_json(force=True)
    resultado = perfil.crear_empresa(datos)
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


# ── Evaluación ───────────────────────────────────────────────────────────────

@app.route("/empresa/<empresa_id>/evaluar", methods=["POST"])
def route_evaluar_empresa(empresa_id):
    resultado = evaluacion.evaluar_empresa(empresa_id)
    if "error" in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)


@app.route("/empresa/<empresa_id>/evaluaciones", methods=["GET"])
def route_historial_evaluaciones(empresa_id):
    return jsonify(evaluacion.obtener_historial_evaluaciones(empresa_id))


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
