import json
import unittest
from unittest.mock import patch
from app import app
from empresa import directorio, evaluacion, parametros, perfil
from test_integracion import respuesta


class Directorio(unittest.TestCase):
    def setUp(self):
        perfil._empresas.clear()
        evaluacion._historial.clear()
        parametros._parametros.clear()
        self.client = app.test_client()
        self.id = self.client.post('/empresa', json={'nombre': 'Mi empresa aprobada', 'fundador': 'Privado', 'curp_rfc': 'PRIVADO'}).get_json()['empresa_id']
        self.datos = dict(capital_inicial=100000, giro_sector='tecnologia', num_empleados=6, registro_legal=True,
                          **{nombre: 'Propuesta de negocio para clientes locales con atención mensual.' for nombre in ('plan_ventas', 'plan_financiero', 'analisis_mercado')})
        self.client.post(f'/empresa/{self.id}/parametros', json=self.datos)

    def aprobar(self):
        with patch('empresa.revision_planes.llamar_chat', return_value=json.dumps(respuesta(4))):
            self.assertTrue(self.client.post(f'/empresa/{self.id}/evaluar').get_json()['aprobado'])

    def test_directorio_abierto_y_edicion_protegida(self):
        self.assertEqual(self.client.get('/directorio-page').status_code, 200)
        self.assertEqual(self.client.put('/empresa/activa/oportunidades', json={}).status_code, 403)
        visitante = app.test_client()
        respuesta = visitante.get('/directorio-page?giro=tecnologia')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        self.assertIn('Norte Digital', html)
        self.assertNotIn('id="form-oportunidades"', html)
        self.assertEqual(visitante.put('/empresa/activa/oportunidades', json={}).status_code, 403)
        for ruta in ('/tramitologia-page', '/registro-page'):
            self.assertEqual(visitante.get(ruta).status_code, 302)

    def test_ejemplos_identificados_y_reales_solo_si_aprueban(self):
        empresas = directorio.listar_empresas()
        self.assertEqual(len(empresas), 12)
        self.assertTrue(all(e['es_ejemplo'] for e in empresas))
        self.aprobar()
        empresas = directorio.listar_empresas()
        propia = next(e for e in empresas if e['empresa_id'] == self.id)
        self.assertFalse(propia['es_ejemplo'])
        self.assertNotIn('fundador', propia)
        self.assertNotIn('curp_rfc', propia)
        html = self.client.get('/directorio-page').get_data(as_text=True)
        self.assertIn('Mi empresa aprobada', html)
        self.assertIn('Ejemplo ficticio', html)
        self.assertIn('⑥ Empresas', html)
        self.assertNotIn('PRIVADO', html)

    def test_filtros_combinados(self):
        empresas = directorio.listar_empresas()
        resultado = directorio.filtrar_empresas(empresas, 'Norte', 'tecnologia', 'inversion', 'ejemplos')
        self.assertEqual([e['nombre'] for e in resultado], ['Norte Digital'])
        self.assertEqual(directorio.filtrar_empresas(empresas, giro='tecnologia', necesidad='financiamiento'), [])
        self.aprobar()
        html = self.client.get('/directorio-page?q=NORTE&giro=tecnologia&necesidad=inversion&origen=ejemplos').get_data(as_text=True)
        self.assertIn('Norte Digital', html)
        self.assertNotIn('Café Bruma', html)
        vacio = self.client.get('/directorio-page?q=empresa-inexistente').get_data(as_text=True)
        self.assertIn('No hay empresas con estos filtros', vacio)

    def test_editar_oportunidades_y_escapar_html(self):
        self.aprobar()
        datos = dict(descripcion='<script>alert(1)</script> Servicio de prueba.', financiamiento=True, inversion=False, empleados=True)
        self.assertEqual(self.client.put('/empresa/activa/oportunidades', json=datos).status_code, 200)
        propia = next(e for e in directorio.listar_empresas() if e['empresa_id'] == self.id)
        self.assertTrue(propia['financiamiento'])
        self.assertFalse(propia['inversion'])
        html = self.client.get('/directorio-page?origen=evaluadas').get_data(as_text=True)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        datos['empleados'] = 'sí'
        self.assertEqual(self.client.put('/empresa/activa/oportunidades', json=datos).status_code, 400)

    def test_cambios_retiraran_empresa_del_directorio(self):
        self.aprobar()
        self.assertTrue(any(e['empresa_id'] == self.id for e in directorio.listar_empresas()))
        self.client.post(f'/empresa/{self.id}/parametros', json=self.datos)
        self.assertFalse(any(e['empresa_id'] == self.id for e in directorio.listar_empresas()))
        self.assertEqual(self.client.get('/directorio-page').status_code, 200)

    def test_miniaturas_locales_disponibles(self):
        for giro in directorio.GIROS:
            r = self.client.get(f'/static/empresas/{giro}.svg')
            self.assertEqual(r.status_code, 200)
            self.assertIn('image/svg+xml', r.content_type)
            r.close()


if __name__ == '__main__':
    unittest.main()
