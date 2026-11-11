"""Pruebas integrales End-to-End de todos los endpoints REST de Django y motores matemáticos."""
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client


def probar_todo():
    c = Client()

    # 1. Index SPA
    r_idx = c.get('/')
    assert r_idx.status_code == 200, f"Fallo en GET /: {r_idx.status_code}"
    assert b'NumLab' in r_idx.content

    # 2. Analizar función
    r_fn = c.post(
        '/api/analizar-funcion/',
        data=json.dumps({'fx': 'ln(sin(x)^2 + 1) - 1/2', 'x0': 0.5}),
        content_type='application/json',
    ).json()
    assert r_fn['ok'] is True, f"Fallo en analizar-funcion: {r_fn}"
    assert len(r_fn['candidatas_g']) > 0

    # 3. Capítulo 1: Todos los métodos y comparador
    for met in ['biseccion', 'regla_falsa', 'punto_fijo', 'newton', 'secante', 'raices_multiples', 'busqueda_incremental']:
        r_c1 = c.post(
            '/api/capitulo-1/ejecutar/',
            data=json.dumps({
                'metodo': met,
                'fx': 'exp(-x) - x',
                'gx': 'exp(-x)',
                'a': 0,
                'b': 1,
                'x0': 0.5,
                'x1': 0.6,
                'delta': 0.2,
                'variante': 2,
                'm': 1,
                'tol': 1e-7,
                'max_iter': 100,
                'tipo_error': 'rel',
            }),
            content_type='application/json',
        ).json()
        assert r_c1['ok'] is True, f"Fallo en Cap 1 ({met}): {r_c1}"

    r_cmp1 = c.post(
        '/api/capitulo-1/comparar/',
        data=json.dumps({
            'fx': 'exp(-x) - x',
            'gx': 'exp(-x)',
            'a': 0,
            'b': 1,
            'x0': 0.5,
            'x1': 0.6,
            'm': 1,
            'tol': 1e-7,
            'max_iter': 100,
            'tipo_error': 'rel',
        }),
        content_type='application/json',
    ).json()
    assert r_cmp1['ok'] is True and len(r_cmp1['metodos']) == 7, f"Fallo en comparar Cap 1: {r_cmp1}"

    # 4. Capítulo 2: Matriz 8x8 en Jacobi, Gauss-Seidel, SOR y Comparador
    A8 = [[15.0 if i == j else -1.0 for j in range(8)] for i in range(8)]
    b8 = [8.0] * 8
    x0_8 = [0.0] * 8

    for met2 in ['jacobi', 'gauss_seidel', 'sor', 'gauss_parcial', 'doolittle', 'crout', 'cholesky']:
        r_c2 = c.post(
            '/api/capitulo-2/ejecutar/',
            data=json.dumps({
                'metodo': met2,
                'A': A8,
                'b': b8,
                'x0': x0_8,
                'omega': 1.12,
                'tol': 1e-7,
                'max_iter': 100,
                'norma': 'inf',
                'tipo_error': 'rel',
            }),
            content_type='application/json',
        ).json()
        assert r_c2['ok'] is True, f"Fallo en Cap 2 ({met2}): {r_c2}"
        assert len(r_c2['solucion']) == 8

    r_cmp2 = c.post(
        '/api/capitulo-2/comparar/',
        data=json.dumps({
            'A': A8,
            'b': b8,
            'x0': x0_8,
            'omega': 1.12,
            'tol': 1e-7,
            'max_iter': 100,
            'norma': 'inf',
            'tipo_error': 'rel',
        }),
        content_type='application/json',
    ).json()
    assert r_cmp2['ok'] is True and len(r_cmp2['metodos']) == 3, f"Fallo en comparar Cap 2: {r_cmp2}"

    # 5. Capítulo 3: Hasta 10 datos + Reserva del 20% y 30% + Comparador + Bóveda
    x10 = [float(i) for i in range(10)]
    y10 = [float(np_val) for np_val in [0.0, 0.8415, 0.9093, 0.1411, -0.7568, -0.9589, -0.2794, 0.6570, 0.9894, 0.4121]]

    for met3 in ['vandermonde', 'newton', 'lagrange', 'spline_lineal', 'spline_cuadratico', 'spline_cubico']:
        for pct in (20, 30):
            r_c3 = c.post(
                '/api/capitulo-3/ejecutar/',
                data=json.dumps({
                    'metodo': met3,
                    'x': x10,
                    'y': y10,
                    'porcentaje_reserva': pct,
                    'x_eval': 4.5,
                    'fx_real': 'sin(x)',
                }),
                content_type='application/json',
            ).json()
            assert r_c3['ok'] is True, f"Fallo en Cap 3 ({met3}, {pct}%): {r_c3}"
            assert r_c3['validacion_reserva'] is not None

    r_cmp3 = c.post(
        '/api/capitulo-3/comparar/',
        data=json.dumps({
            'x': x10,
            'y': y10,
            'porcentaje_reserva': 30,
            'x_eval': 4.5,
            'fx_real': 'sin(x)',
        }),
        content_type='application/json',
    ).json()
    assert r_cmp3['ok'] is True and len(r_cmp3['metodos']) == 6, f"Fallo en comparar Cap 3: {r_cmp3}"

    r_alm = c.get('/api/capitulo-3/almacenamiento/').json()
    assert r_alm['ok'] is True and len(r_alm['datasets']) >= 2

    # 6. Prevención de errores y casos límite
    def post(url, datos):
        return c.post(url, data=json.dumps(datos), content_type='application/json').json()

    # Intervalo sin cambio de signo: se informa el motivo (Bolzano), no un "límite alcanzado"
    r = post('/api/capitulo-1/ejecutar/', {'metodo': 'biseccion', 'fx': 'x^2 + 1', 'a': '0', 'b': '1', 'tol': '1e-7', 'max_iter': '100'})
    assert r['ok'] and r['estado'] == 'inadecuado' and 'Bolzano' in r['mensaje'], r

    # Campos vacíos y expresiones numéricas
    r = post('/api/capitulo-1/ejecutar/', {'metodo': 'biseccion', 'fx': 'x^3 - x - 2', 'a': '', 'b': '2', 'tol': '1e-7', 'max_iter': '100'})
    assert not r['ok'] and r['error'] == 'Falta el valor de a (extremo izquierdo).', r
    r = post('/api/capitulo-1/ejecutar/', {'metodo': 'newton', 'fx': 'x^3 - x - 2', 'x0': 'pi/2', 'tol': '1e-7', 'max_iter': '100'})
    assert r['ok'] and abs(r['raiz'] - 1.5213797068) < 1e-8, r
    r = post('/api/capitulo-1/ejecutar/', {'metodo': 'newton', 'fx': 'x^3 - x - 2', 'x0': '1', 'tol': '1e-7', 'max_iter': '5000'})
    assert not r['ok'] and '2000' in r['error'], r

    # Punto fijo con una g(x) que no corresponde a f(x)
    r = post('/api/capitulo-1/ejecutar/', {'metodo': 'punto_fijo', 'fx': 'exp(-x) - x', 'gx': 'ln(sin(x)^2 + 1) - 1/2 + x', 'x0': '0.5', 'tol': '1e-7', 'max_iter': '100', 'tipo_error': 'rel'})
    assert r['ok'] and r['estado'] == 'inconsistente' and not r['convergio'], r

    # Comparación: cada método corrido con los 3 criterios
    r = post('/api/capitulo-1/comparar/', {'fx': 'exp(-x) - x', 'gx': 'exp(-x)', 'a': '0', 'b': '1', 'x0': '0.5', 'x1': '0.6', 'm': '1', 'tol': '1e-7', 'max_iter': '100', 'tipo_error': 'abs'})
    assert r['ok'] and set(r['metodos_por_criterio']) == {'abs', 'rel', 'cond'}, r
    assert all(len(v) == 7 for v in r['metodos_por_criterio'].values())
    assert r['informe']['ganador_cond'] == 'Newton-Raphson', r['informe']
    r = post('/api/capitulo-2/comparar/', {'A': [[4, 1], [1, 3]], 'b': [1, 2], 'x0': [0, 0], 'omega': '1.1', 'tol': '1e-7', 'max_iter': '100', 'tipo_error': 'rel'})
    assert r['ok'] and all(len(v) == 3 for v in r['metodos_por_criterio'].values()), r

    # Matriz con una celda vacía y diagonal con cero
    r = post('/api/capitulo-2/ejecutar/', {'metodo': 'jacobi', 'A': [['4', '1'], ['', '3']], 'b': ['1', '2'], 'tol': '1e-7', 'max_iter': '100'})
    assert not r['ok'] and r['error'] == 'El elemento a2,1 está vacío.', r
    r = post('/api/capitulo-2/ejecutar/', {'metodo': 'jacobi', 'A': [[0, 5, 6], [-2, 7, 1], [-1, -1, 4]], 'b': [15, 15, 20], 'x0': [1, 1, 1], 'tol': '0.05', 'max_iter': '100'})
    assert not r['ok'] and 'diagonal' in r['error'], r
    # Jacobi con rho >= 1: se informa el fracaso y los avisos
    r = post('/api/capitulo-2/ejecutar/', {'metodo': 'jacobi', 'A': [[1, 5], [7, 1]], 'b': [1, 1], 'x0': [0, 0], 'tol': '1e-7', 'max_iter': '30', 'tipo_error': 'rel'})
    assert r['ok'] and r['estado'] in ('fracaso', 'diverge') and r['avisos'] and not r['puede_converger'], r

    # Capítulo 3 sin reserva: el polinomio usa todos los puntos (ejemplo de clase, grado 3)
    r = post('/api/capitulo-3/ejecutar/', {'metodo': 'newton', 'x': ['19', '25', '29', '33'], 'y': ['5.8', '2.1', '-1.3', '9.2'], 'porcentaje_reserva': 0, 'x_eval': '20'})
    assert r['ok'] and r['grado'] == 3 and abs(r['evaluacion_punto']['y_interp'] - 6.771205357) < 1e-8, r
    assert r['tabla_diferencias']['columnas'][:3] == ['i', 'xi', 'f[xi]'] and r['tabla_diferencias']['filas'][0][3] is None
    # Con 3 puntos y reserva se avisa que hacen falta 4
    r = post('/api/capitulo-3/ejecutar/', {'metodo': 'spline_cuadratico', 'x': [7, 8, 9], 'y': [-33, 0, 35], 'porcentaje_reserva': 20})
    assert not r['ok'] and 'al menos 4' in r['error'], r
    # Función real para graficar
    r = post('/api/capitulo-3/ejecutar/', {'metodo': 'lagrange', 'x': [1, 2, 3], 'y': [1, 4, 9], 'porcentaje_reserva': 0, 'fx_real': 'x^2'})
    assert r['ok'] and r['curva']['y_real'] is not None

    print("TODAS LAS PRUEBAS END-TO-END DE DJANGO + REACT API PASARON EXITOSAMENTE (OK)")


if __name__ == '__main__':
    probar_todo()

