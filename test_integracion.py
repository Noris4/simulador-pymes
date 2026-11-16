import copy
import json
import os
import unittest
from unittest.mock import patch
from app import app
from empresa import evaluacion, parametros, registro
from empresa.revision_planes import CRITERIOS, validar_respuesta
from empresa.watsonx import ErrorWatsonx, llamar_chat
from empresa.rubrica import guia_local


def respuesta(valor=2):
    return {nombre: {"criterios": dict.fromkeys(sorted(criterios), valor),
                     "motivo": "Faltan datos concretos.", "mejora": "Agrega metas y supuestos.",
                     "desglose": guia_local(nombre, criterios)}
            for nombre, criterios in CRITERIOS.items()}


class Integracion(unittest.TestCase):
    def setUp(self):
        parametros._parametros.clear()
        evaluacion._historial.clear()
        self.client = app.test_client()
        self.id = self.client.post('/empresa', json={"nombre": "Prueba", "fundador": "Prueba", "giro": "tecnologia"}).get_json()['empresa_id']
        self.datos = dict(capital_inicial=100000, giro_sector='tecnologia', num_empleados=6,
                          registro_legal=True, **{nombre: 'Propuesta inicial para atender clientes locales con servicios tecnológicos.' for nombre in CRITERIOS})
        self.guardar()

    def guardar(self):
        self.assertEqual(self.client.post(f'/empresa/{self.id}/parametros', json=self.datos).status_code, 200)

    def evaluar(self):
        return self.client.post(f'/empresa/{self.id}/evaluar')

    def test_basura_no_aprueba_sin_consulta(self):
        for nombre in CRITERIOS:
            self.datos[nombre] = 's' * 1000
        self.guardar()
        with patch('empresa.revision_planes.llamar_chat') as llamada:
            r = self.evaluar().get_json()
        llamada.assert_not_called()
        self.assertEqual(r['calificacion'], 0)
        self.assertFalse(r['aprobado'])
        self.assertTrue(all(r['detalle_puntajes'][n]['puntaje_obtenido'] == 0 for n in CRITERIOS))

    def test_contenido_usa_puntajes_ibm(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta())) as llamada:
            r = self.evaluar().get_json()
        self.assertEqual(r['calificacion'], 40)
        self.assertFalse(r['aprobado'])
        entrada = json.loads(llamada.call_args.args[1])
        self.assertNotIn('fundador', entrada)
        self.assertNotIn('curp_rfc', entrada)
        self.assertEqual(r['detalle_puntajes']['analisis_mercado']['puntaje_obtenido'], 8)

    def test_basura_parcial_no_recibe_puntos_incluso_si_ibm_los_da(self):
        self.datos['plan_ventas'] = 's' * 500
        self.guardar()
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            r = self.evaluar().get_json()
        self.assertEqual(r['calificacion'], 60)
        self.assertFalse(r['aprobado'])
        self.assertEqual(r['detalle_puntajes']['plan_ventas']['puntaje_obtenido'], 0)

    def test_fallo_ibm_invalida_aprobacion_previa(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            self.assertTrue(self.evaluar().get_json()['aprobado'])
        with patch('empresa.revision_planes.llamar_chat', side_effect=ErrorWatsonx('No disponible')):
            r = self.evaluar()
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()['estado'], 'pendiente')
        self.assertFalse(registro.verificar_elegibilidad_registro(self.id)[0])

    def test_guardar_cambios_invalida_resultado(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            self.evaluar()
        self.guardar()
        self.assertEqual(evaluacion.obtener_historial_evaluaciones(self.id), [])

    def test_respuestas_invalidas_no_puntuan(self):
        for valor in (True, -1, 6, '5', float('nan'), float('inf')):
            with self.subTest(valor=valor), self.assertRaises(ErrorWatsonx):
                validar_respuesta(json.dumps(respuesta(valor)))
        for texto in ('{}', 'No sé', '[]'):
            with self.assertRaises(ErrorWatsonx):
                validar_respuesta(texto)

    def test_sin_clave_no_consulta(self):
        with patch.dict(os.environ, {}, clear=True), patch('empresa.watsonx._peticion') as consulta:
            with self.assertRaises(ErrorWatsonx):
                llamar_chat('Prueba', '{}')
            consulta.assert_not_called()

    def test_cliente_usa_iam_y_chat(self):
        config = dict(WATSONX_API_KEY='clave-ficticia', WATSONX_PROJECT_ID='proyecto-prueba',
                      WATSONX_BASE_URL='https://us-south.ml.cloud.ibm.com', WATSONX_MODEL='ibm/granite-4-h-small')
        with patch.dict(os.environ, config, clear=True), patch('empresa.watsonx._peticion', side_effect=[
            {"access_token": "token-ficticio"}, {"choices": [{"finish_reason": "stop", "message": {"content": "OK"}}]}
        ]) as consulta:
            self.assertEqual(llamar_chat('Instrucción', 'Plan'), 'OK')
            self.assertIn('/ml/v1/text/chat?', consulta.call_args.args[0])
            cuerpo = json.loads(consulta.call_args.args[1])
            self.assertEqual(cuerpo['messages'][0]['role'], 'system')
            self.assertEqual(cuerpo['project_id'], 'proyecto-prueba')

    def test_paginas_cargan(self):
        for ruta in ('/', '/parametros-page', '/evaluacion-page'):
            self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_sin_aprobacion_bloquea_paginas_y_api(self):
        for ruta in ('/tramitologia-page', '/registro-page'):
            r = self.client.get(ruta)
            self.assertEqual(r.status_code, 302)
            self.assertIn('/evaluacion-page?bloqueo=evaluacion', r.location)
        with patch('empresa.tramitologia._generar_con_llm') as llamada:
            for ruta in ('tramitologia', 'registro/documento', 'registro/estado'):
                self.assertEqual(self.client.get(f'/empresa/{self.id}/{ruta}').status_code, 403)
            self.assertEqual(self.client.post(f'/empresa/{self.id}/registro/confirmar').status_code, 403)
            self.assertEqual(self.client.post(f'/empresa/{self.id}/pasos/4/completar').status_code, 403)
        llamada.assert_not_called()

    def test_aprobado_desbloquea_paginas_api_y_navegacion(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(4))):
            r = self.evaluar().get_json()
        self.assertTrue(r['aprobado'])
        self.assertTrue(self.client.get(f'/empresa/{self.id}/acceso').get_json()['permitido'])
        for ruta in ('/tramitologia-page', '/registro-page'):
            self.assertEqual(self.client.get(ruta).status_code, 200)
        with patch('empresa.tramitologia._generar_con_llm', return_value='RESUMEN\nPrueba'):
            self.assertEqual(self.client.get(f'/empresa/{self.id}/tramitologia').status_code, 200)
        self.assertEqual(self.client.get(f'/empresa/{self.id}/registro/documento').status_code, 200)

    def test_plan_debil_no_se_compensa_con_los_demas(self):
        datos = respuesta(5)
        datos['plan_ventas']['criterios'] = dict.fromkeys(CRITERIOS['plan_ventas'], 3)
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(datos)):
            r = self.evaluar().get_json()
        self.assertGreater(r['calificacion'], 80)
        self.assertFalse(r['aprobado'])
        self.assertTrue(any('80%' in m for m in r['motivos_bloqueo']))
        self.assertEqual(self.client.get(f'/empresa/{self.id}/tramitologia').status_code, 403)

    def test_criterio_debil_impide_aprobar_aunque_plan_supere_80(self):
        datos = respuesta(5)
        datos['plan_ventas']['criterios']['clientes'] = 2
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(datos)):
            r = self.evaluar().get_json()
        self.assertGreater(r['calificacion'], 80)
        self.assertFalse(r['aprobado'])

    def test_version_anterior_y_cambios_invalidan_acceso(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            self.evaluar()
        ultima = evaluacion._historial[self.id][-1]
        ultima['version_evaluacion'] = 'anterior'
        self.assertFalse(evaluacion.acceso_aprobado(self.id)[0])
        ultima['version_evaluacion'] = evaluacion.VERSION_EVALUACION
        parametros._parametros[self.id]['plan_ventas'] += ' Cambio de plan.'
        self.assertFalse(evaluacion.acceso_aprobado(self.id)[0])

    def test_otra_sesion_no_aprovecha_aprobacion(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            self.evaluar()
        otra = app.test_client()
        self.assertEqual(otra.get(f'/empresa/{self.id}/tramitologia').status_code, 403)
        self.assertEqual(otra.get('/registro-page').status_code, 302)

    def test_umbral_80_inclusivo(self):
        detalle = {nombre: {"puntaje_obtenido": evaluacion.PESOS[nombre] * 0.8,
                            "criterios": dict.fromkeys(criterios, 4)} for nombre, criterios in CRITERIOS.items()}
        self.assertEqual(evaluacion.comprobar_aprobacion({"calificacion": 80, "detalle_puntajes": detalle}), [])
        self.assertTrue(evaluacion.comprobar_aprobacion({"calificacion": 79.99, "detalle_puntajes": detalle}))

    def test_guia_completa_en_los_doce_criterios(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta())):
            r = self.evaluar().get_json()
        self.assertEqual(set(r['guia_mejora']), set(CRITERIOS))
        for nombre, guia in r['guia_mejora'].items():
            self.assertEqual(set(guia['desglose']), CRITERIOS[nombre])
            for criterio, datos in guia['desglose'].items():
                self.assertGreaterEqual(len(datos['acciones']), 2)
                self.assertTrue(guia['requisitos'][criterio]['requisito'])
                self.assertTrue(datos['entregable'])
                self.assertTrue(datos['verificacion'])

    def test_guia_incompleta_no_se_acepta_como_evaluacion_valida(self):
        datos = respuesta()
        del datos['plan_ventas']['desglose']['clientes']
        with self.assertRaises(ErrorWatsonx):
            validar_respuesta(json.dumps(datos))
        datos = respuesta()
        datos['plan_ventas']['desglose']['clientes']['acciones'] = ['Mejora todo.']
        with self.assertRaises(ErrorWatsonx):
            validar_respuesta(json.dumps(datos))

    def test_basura_tambien_recibe_guia_para_empezar(self):
        for nombre in CRITERIOS:
            self.datos[nombre] = 's' * 300
        self.guardar()
        with patch('empresa.revision_planes.llamar_chat') as llamada:
            r = self.evaluar().get_json()
        llamada.assert_not_called()
        self.assertEqual(len(r['guia_mejora']['plan_ventas']['desglose']), 4)
        self.assertEqual(r['guia_mejora']['plan_ventas']['fuente'], 'validacion_local')

    def test_contexto_no_agrega_puntos_y_se_envia_a_ibm(self):
        notas = []
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(4))) as llamada:
            for capital, empleados, giro, legal in ((1000000, 50, 'tecnologia', True), (0, 0, 'otro', False)):
                self.datos.update(capital_inicial=capital, num_empleados=empleados, giro_sector=giro, registro_legal=legal)
                self.guardar()
                r = self.evaluar().get_json()
                notas.append(r['calificacion'])
                self.assertEqual(set(r['detalle_puntajes']), set(CRITERIOS))
                self.assertTrue(r['aprobado'])
                contexto = json.loads(llamada.call_args.args[1])['contexto_empresa']
                self.assertEqual(contexto['capital_inicial'], capital)
                self.assertEqual(contexto['registro_legal'], legal)
        self.assertEqual(notas, [80, 80])

    def test_maximos_de_los_planes_suman_cien(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(5))):
            r = self.evaluar().get_json()
        self.assertEqual(r['calificacion'], 100)
        self.assertEqual(sum(d['puntaje_maximo'] for d in r['detalle_puntajes'].values()), 100)


if __name__ == '__main__':
    unittest.main()
