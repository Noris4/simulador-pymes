"""Cliente compartido de IBM. Las credenciales se leen del entorno, nunca del código."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class ErrorWatsonx(Exception):
    pass


def _peticion(url, payload, headers):
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as respuesta:
            return json.load(respuesta)
    except urllib.error.HTTPError as exc:
        mensajes = {
            400: "IBM rechazó la solicitud. Revisa modelo, región y proyecto.",
            401: "IBM no autorizó la consulta. Revisa tu API key.",
            403: "No tienes permisos o acceso al modelo en IBM.",
            429: "Se alcanzó un límite de uso de IBM. Inténtalo más tarde.",
        }
        raise ErrorWatsonx(mensajes.get(exc.code, "IBM no está disponible. Inténtalo más tarde.")) from None
    except (OSError, ValueError):
        raise ErrorWatsonx("No se pudo obtener una respuesta de IBM. Revisa tu conexión e inténtalo de nuevo.") from None


def llamar_chat(instrucciones, datos, max_tokens=2000):
    clave = os.getenv("WATSONX_API_KEY", "").strip()
    proyecto = os.getenv("WATSONX_PROJECT_ID", "").strip()
    base = os.getenv("WATSONX_BASE_URL", "").strip().rstrip("/")
    modelo = os.getenv("WATSONX_MODEL", "").strip()
    if not all((clave, proyecto, base, modelo)) or clave == "PEGA_AQUI_TU_CLAVE":
        raise ErrorWatsonx("Falta configurar IBM en el archivo .env. La evaluación queda pendiente.")
    destino = urllib.parse.urlsplit(base)
    if (destino.scheme != "https" or not destino.hostname
            or not destino.hostname.endswith(".ml.cloud.ibm.com")
            or destino.username or destino.password or destino.query
            or destino.fragment or destino.path not in ("", "/")):
        raise ErrorWatsonx("WATSONX_BASE_URL debe ser la URL HTTPS regional de IBM, sin rutas adicionales.")
    token = _peticion(
        "https://iam.cloud.ibm.com/identity/token",
        urllib.parse.urlencode({"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": clave}).encode(),
        {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    if not isinstance(token, dict) or not isinstance(token.get("access_token"), str):
        raise ErrorWatsonx("IBM devolvió una autenticación incompleta.")
    respuesta = _peticion(
        base + "/ml/v1/text/chat?version=2023-05-29",
        json.dumps({
            "project_id": proyecto, "model_id": modelo,
            "messages": [{"role": "system", "content": instrucciones}, {"role": "user", "content": datos}],
            "temperature": 0, "max_tokens": max_tokens,
        }, ensure_ascii=False).encode("utf-8"),
        {"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + token["access_token"]},
    )
    try:
        opcion = respuesta["choices"][0]
        if opcion.get("finish_reason") != "stop":
            raise ErrorWatsonx("IBM no completó la respuesta. Vuelve a intentarlo.")
        contenido = opcion["message"]["content"]
        if not isinstance(contenido, str) or not contenido.strip():
            raise ValueError()
        return contenido.strip()
    except (KeyError, IndexError, TypeError, ValueError):
        raise ErrorWatsonx("IBM devolvió una respuesta incompleta.") from None
