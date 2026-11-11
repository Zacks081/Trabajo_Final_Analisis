"""Vistas REST de Django para los 3 capítulos, comparadores, derivadas y almacenamiento de datos."""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from motor import comparador as cmp
from motor import funciones as fn
from motor import interpolacion as it
from motor import no_lineales as nl
from motor import sistemas as si

STORAGE_FILE = Path(__file__).resolve().parent.parent / 'datos_interpolacion.json'


def _leer_json(request):
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        raise ValueError("El cuerpo de la petición no es un JSON válido.")


def _error_json(mensaje, status=400):
    return JsonResponse({'ok': False, 'error': str(mensaje)}, status=status)


def _num(d, nombre, *claves):
    """Lee un número del JSON (acepta '1e-7', 'pi/2', '1/3'...). El error dice qué campo falta."""
    for clave in claves:
        if clave in d and d[clave] is not None and str(d[clave]).strip() != '':
            try:
                return fn.interpretar_numero(d[clave])
            except ValueError:
                raise ValueError(f"El valor de {nombre} ('{d[clave]}') no es un número válido.")
    raise ValueError(f"Falta el valor de {nombre}.")


def _iteraciones(d):
    valor = _num(d, "Máx. iteraciones", 'max_iter', 'niter')
    if valor != int(valor) or not 1 <= valor <= 2000:
        raise ValueError("El número máximo de iteraciones debe ser un entero entre 1 y 2000.")
    return int(valor)


def _tolerancia(d):
    tol = _num(d, "la tolerancia", 'tol')
    if tol <= 0:
        raise ValueError("La tolerancia debe ser mayor que 0.")
    return tol


def spa_index(request):
    """Sirve la aplicación React principal."""
    return render(request, 'index.html')


# =============================================== ASISTENTE DE FUNCIONES Y DERIVADAS

@csrf_exempt
def analizar_funcion_view(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        datos = _leer_json(request)
        f_str = datos.get('fx') or datos.get('funcion', '')
        x0 = datos.get('x0', None)
        if x0 == '':
            x0 = None
        resultado = fn.analizar_funcion(f_str, x0=x0)
        candidatas_g = [
            {
                'expr': s['texto'],
                'latex': s['latex'],
                'descripcion': s['descripcion'],
                'dg_x0': s.get('dg_x0'),
                'converge': s.get('converge_local', False),
            }
            for s in resultado.get('sugerencias_g', [])
        ]
        return JsonResponse({
            'ok': True,
            'datos': resultado,
            'fx': resultado['f']['texto'],
            'fx_latex': resultado['f']['latex'],
            'dfx': resultado['df']['texto'],
            'dfx_latex': resultado['df']['latex'],
            'ddfx': resultado['d2f']['texto'],
            'ddfx_latex': resultado['d2f']['latex'],
            'candidatas_g': candidatas_g,
        })
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error al analizar la función: {e}")


# =============================================== CAPÍTULO 1: NO LINEALES

def _estimar_orden(historial):
    """Estima el orden de convergencia p a partir de los últimos errores absolutos."""
    errores = [h.get('e_abs') for h in historial if h.get('e_abs') is not None and h.get('e_abs') > 1e-15]
    if len(errores) < 3:
        return None
    try:
        e_k1, e_k, e_km1 = errores[-1], errores[-2], errores[-3]
        if e_k <= 0 or e_km1 <= 0 or abs(np.log(e_k / e_km1)) < 1e-12:
            return None
        p = np.log(e_k1 / e_k) / np.log(e_k / e_km1)
        if np.isfinite(p) and 0.3 <= p <= 3.5:
            return round(float(p), 2)
    except Exception:
        pass
    return None


@csrf_exempt
def capitulo_1_ejecutar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        metodo = d.get('metodo', 'biseccion')
        if metodo == 'busqueda_incremental':
            metodo_interno = 'busquedas'
        else:
            metodo_interno = metodo

        f_str = d.get('fx') or d.get('funcion', '')
        f = fn.Funcion.desde_texto(f_str)

        df_str = d.get('dfx') if 'dfx' in d else d.get('derivada_1', '')
        d2f_str = d.get('ddfx') if 'ddfx' in d else d.get('derivada_2', '')
        df = fn.Funcion.desde_texto(df_str) if (df_str and str(df_str).strip()) else f.derivada()
        d2f = fn.Funcion.desde_texto(d2f_str) if (d2f_str and str(d2f_str).strip()) else df.derivada()

        tol = _tolerancia(d)
        niter = _iteraciones(d)
        tipo_error = d.get('tipo_error', 'abs')
        if tipo_error not in ('abs', 'rel', 'cond'):
            tipo_error = 'abs'

        g = None
        intervalo = None
        advertencia = None

        if metodo_interno == 'busquedas':
            x0 = _num(d, "x₀", 'x0')
            dx = _num(d, "Δx", 'delta', 'dx')
            if dx == 0:
                raise ValueError("El tamaño de paso Δx no puede ser 0.")
            res = nl.busquedas_incrementales(f, x0, dx, niter)
            if res.puntos:
                intervalo = (min(res.puntos), max(res.puntos))

        elif metodo_interno in ('biseccion', 'regla_falsa'):
            a = _num(d, "a (extremo izquierdo)", 'a')
            b = _num(d, "b (extremo derecho)", 'b')
            if b <= a:
                raise ValueError("El extremo derecho b debe ser mayor que el extremo izquierdo a.")
            intervalo = (a, b)
            res = nl.biseccion(f, a, b, tol, niter, tipo_error) if metodo_interno == 'biseccion' else nl.regla_falsa(f, a, b, tol, niter, tipo_error)

        elif metodo_interno == 'punto_fijo':
            g_str = d.get('gx') or d.get('funcion_g', '')
            if not g_str or not str(g_str).strip():
                raise ValueError("Debes ingresar la función de iteración g(x) (o seleccionar una de las sugerencias automáticas).")
            g = fn.Funcion.desde_texto(g_str)
            x0 = _num(d, "x₀", 'x0')
            try:
                dg_val = abs(g.derivada()(x0))
                if np.isfinite(dg_val) and dg_val >= 1.0:
                    advertencia = f"En x₀ = {x0}, |g'(x₀)| = {dg_val:.4f} ≥ 1. La condición suficiente de convergencia local no se cumple."
            except Exception:
                pass
            res = nl.punto_fijo(f, g, x0, tol, niter, tipo_error)

        elif metodo_interno == 'newton':
            x0 = _num(d, "x₀", 'x0')
            res = nl.newton(f, df, x0, tol, niter, tipo_error)

        elif metodo_interno == 'secante':
            x0 = _num(d, "x₀", 'x0')
            x1 = _num(d, "x₁", 'x1')
            if x1 == x0:
                raise ValueError("Los valores iniciales x0 y x1 deben ser distintos en el método de la Secante.")
            res = nl.secante(f, x0, x1, tol, niter, tipo_error)

        elif metodo_interno in ('raices_multiples_m', 'raices_multiples_d2', 'raices_multiples'):
            x0 = _num(d, "x₀", 'x0')
            variante = int(d.get('variante', 1 if metodo_interno == 'raices_multiples_m' else 2))
            m = 2
            if variante == 1:
                m = _num(d, "la multiplicidad m", 'm')
                if m != int(m) or m < 1:
                    raise ValueError("La multiplicidad m debe ser un entero mayor o igual a 1.")
                m = int(m)
            res = nl.raices_multiples(f, df, d2f, x0, tol, niter, tipo_error, variante=variante, m=m)

        else:
            raise ValueError(f"Método '{metodo}' no reconocido.")

        payload = nl.serializar_resultado_no_lineal(res, f, df=df, d2f=d2f, g=g, intervalo=intervalo)
        payload['funciones'] = {
            'f': {'texto': f.texto, 'latex': f.latex},
            'df': {'texto': df.texto, 'latex': df.latex},
            'd2f': {'texto': d2f.texto, 'latex': d2f.latex},
            'g': {'texto': g.texto, 'latex': g.latex} if g is not None else None,
        }

        # Construir columnas y filas estructuradas para la tabla de React
        col_defs = []
        for idx_c, nombre_col in enumerate(payload['columnas']):
            key_map = {
                'E abs': 'error_abs',
                'E rel': 'error_rel',
                'E cond': 'error_cond',
            }
            col_defs.append({
                'key': key_map.get(nombre_col, f'c{idx_c}'),
                'label': nombre_col,
                'idx': idx_c,
            })

        iteraciones_estructuradas = []
        for fila in payload['filas']:
            row_dict = {}
            for cd in col_defs:
                row_dict[cd['key']] = fila[cd['idx']] if cd['idx'] < len(fila) else None
            iteraciones_estructuradas.append(row_dict)

        err_map = {'abs': payload['error_abs'], 'rel': payload['error_rel'], 'cond': payload['error_cond']}

        respuesta = {
            'ok': True,
            'resultado': payload,
            **payload,
            'raiz': payload['valor'],
            'f_raiz': payload['fx_final'],
            'iteraciones_usadas': payload['iteraciones'],
            'error_final': err_map.get(tipo_error, payload['error_abs']),
            'convergio': payload['exito'],
            'orden_estimado': _estimar_orden(payload['historial_errores']),
            'advertencia': advertencia,
            'columnas': [{'key': c['key'], 'label': c['label']} for c in col_defs],
            'iteraciones': iteraciones_estructuradas,
            'intervalos': payload.get('extras', {}).get('intervalos', []),
            'pasos_animacion': payload.get('pasos_grafica', []),
            'curva': payload['grafica'],
        }
        return JsonResponse(respuesta)
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error inesperado en el cálculo: {e}")


@csrf_exempt
def capitulo_1_comparar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        tol = _tolerancia(d)
        niter = _iteraciones(d)
        tipo_error = d.get('tipo_error', 'rel')
        if tipo_error not in cmp.CRITERIOS:
            tipo_error = 'rel'

        x0 = _num(d, "x₀", 'x0')
        x1 = _num(d, "x₁", 'x1')
        m = _num(d, "la multiplicidad m", 'm')
        if m != int(m) or m < 1:
            raise ValueError("La multiplicidad m debe ser un entero mayor o igual a 1.")

        reporte = cmp.comparar_capitulo_1(
            f_texto=d.get('fx') or d.get('funcion', ''),
            a=_num(d, "a (extremo izquierdo)", 'a'),
            b=_num(d, "b (extremo derecho)", 'b'),
            x0=x0,
            x1=x1,
            g_texto=d.get('gx') or d.get('funcion_g', ''),
            df_texto=d.get('dfx') if 'dfx' in d else d.get('derivada_1', ''),
            d2f_texto=d.get('ddfx') if 'ddfx' in d else d.get('derivada_2', ''),
            m=int(m),
            tol=tol,
            niter=niter,
            tipo_error=tipo_error,
        )

        # Cada método corrido con cada criterio de parada (absoluto, relativo y condición)
        por_criterio = reporte['por_criterio']
        for lista in por_criterio.values():
            for item in lista:
                item['orden_estimado'] = _estimar_orden([{'e_abs': h['error_abs']} for h in item['historia']])

        ganadores = reporte['ganadores_por_criterio']
        informe_ext = {
            **reporte.get('informe', {}),
            'ganador_iteraciones': ganadores.get(tipo_error) or 'N/A',
            'ganador_abs': ganadores.get('abs') or 'Ninguno',
            'ganador_rel': ganadores.get('rel') or 'Ninguno',
            'ganador_cond': ganadores.get('cond') or 'Ninguno',
            'conclusion_general': " ".join(reporte.get('informe', {}).get('conclusiones', [])),
        }

        return JsonResponse({
            'ok': True,
            **reporte,
            'tipo_error': tipo_error,
            'metodos': por_criterio[tipo_error],
            'metodos_por_criterio': por_criterio,
            'informe': informe_ext,
        })
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error al comparar los métodos: {e}")


# =============================================== CAPÍTULO 2: SISTEMAS LINEALES

@csrf_exempt
def capitulo_2_ejecutar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        metodo = d.get('metodo', 'jacobi')
        if metodo == 'gauss_seidel':
            metodo_interno = 'gauss-seidel'
        else:
            metodo_interno = metodo

        A = si.parsear_matriz(d.get('A'), max_n=8)
        n = A.shape[0]
        b = si.parsear_vector(d.get('b'), n=n, nombre="b")
        tipo_norma = d.get('norma') or d.get('tipo_norma', 'inf')
        tipo_error = d.get('tipo_error', 'rel')

        if metodo_interno in ('jacobi', 'gauss-seidel', 'sor'):
            x0_in = d.get('x0')
            x0 = si.parsear_vector(x0_in, n=n, nombre="x0") if (x0_in is not None and str(x0_in).strip() != '' and x0_in != []) else None
            tol = _tolerancia(d)
            niter = _iteraciones(d)
            w = _num(d, "ω (factor de relajación)", 'omega', 'w') if metodo_interno == 'sor' else 1.0
            res = si.resolver_iterativo(A, b, x0, tol, niter, metodo_interno, tipo_error, tipo_norma, w)
        elif metodo_interno == 'gauss_simple':
            res = si.gauss(A, b, pivoteo=0, tipo_norma=tipo_norma)
        elif metodo_interno == 'gauss_parcial':
            res = si.gauss(A, b, pivoteo=1, tipo_norma=tipo_norma)
        elif metodo_interno == 'gauss_total':
            res = si.gauss(A, b, pivoteo=2, tipo_norma=tipo_norma)
        elif metodo_interno == 'lu_simple':
            res = si.lu(A, b, pivoteo=0, tipo_norma=tipo_norma)
        elif metodo_interno == 'lu_parcial':
            res = si.lu(A, b, pivoteo=1, tipo_norma=tipo_norma)
        elif metodo_interno == 'doolittle':
            res = si.factorizacion_directa(A, b, metodo=0, tipo_norma=tipo_norma)
        elif metodo_interno == 'crout':
            res = si.factorizacion_directa(A, b, metodo=1, tipo_norma=tipo_norma)
        elif metodo_interno == 'cholesky':
            res = si.factorizacion_directa(A, b, metodo=2, tipo_norma=tipo_norma)
        else:
            raise ValueError(f"Método '{metodo}' no reconocido.")

        if not res.get('exito', True) and res.get('estado') == 'error':
            return _error_json(res.get('mensaje', 'Error al resolver el sistema lineal.'))

        # Normalizar claves para la interfaz React
        matrices = res.get('matrices') or {}
        if 'Tw' in matrices and 'T' not in matrices:
            matrices['T'] = matrices['Tw']
        if 'Cw' in matrices and 'C' not in matrices:
            matrices['C'] = matrices['Cw']

        diag = res.get('diagnostico_matriz') or si.diagnosticar_matriz(A, tipo_norma)
        hist = res.get('historial_errores') or []
        iteraciones_estructuradas = [
            {
                'iteracion': h['iteracion'],
                'x': h['x'],
                'error_abs': h['e_abs'],
                'error_rel': h['e_rel'],
                'error_cond': h['e_cond'],
            }
            for h in hist
        ]

        err_map = {'abs': res.get('error_abs'), 'rel': res.get('error_rel'), 'cond': res.get('error_cond')}

        respuesta = {
            'ok': True,
            'resultado': res,
            **res,
            'matrices': matrices if matrices else None,
            'L': res.get('matrices_factorizacion', {}).get('L'),
            'U': res.get('matrices_factorizacion', {}).get('U'),
            'puede_converger': res.get('converge_segun_radio'),
            'condicion_matriz': diag.get('condicion'),
            'residuo_norma': res.get('error_cond'),
            'iteraciones_usadas': res.get('iteraciones'),
            'error_final': err_map.get(tipo_error, res.get('error_rel')),
            'dominancia': diag,
            'iteraciones': iteraciones_estructuradas,
        }
        return JsonResponse(respuesta)
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error en el cálculo del sistema: {e}")


@csrf_exempt
def capitulo_2_comparar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        tol = _tolerancia(d)
        niter = _iteraciones(d)
        w = _num(d, "ω (factor de relajación)", 'omega', 'w')
        tipo_norma = d.get('norma') or d.get('tipo_norma', 'inf')
        tipo_error = d.get('tipo_error', 'rel')
        if tipo_error not in cmp.CRITERIOS:
            tipo_error = 'rel'
        x0_in = d.get('x0')
        if x0_in == '' or x0_in == []:
            x0_in = None

        reporte = cmp.comparar_capitulo_2(
            A_in=d.get('A'),
            b_in=d.get('b'),
            x0_in=x0_in,
            tol=tol,
            niter=niter,
            w=w,
            tipo_error=tipo_error,
            tipo_norma=tipo_norma,
        )

        # Cada método corrido con cada criterio de parada (absoluto, relativo y condición)
        por_criterio = reporte['por_criterio']
        metodos_lista = por_criterio[tipo_error]
        radios = [m for m in metodos_lista if m['radio_espectral'] is not None]
        menor_radio = min(radios, key=lambda x: x['radio_espectral'])['metodo'] if radios else 'N/A'
        ganadores = reporte['ganadores_por_criterio']

        diag = reporte.get('diagnostico_matriz', {})
        informe_ext = {
            **reporte.get('informe', {}),
            'metodo_menor_radio': menor_radio,
            'ganador_iteraciones': ganadores.get(tipo_error) or 'N/A',
            'ganador_abs': ganadores.get('abs') or 'Ninguno',
            'ganador_rel': ganadores.get('rel') or 'Ninguno',
            'ganador_cond': ganadores.get('cond') or 'Ninguno',
            'conclusion_general': " ".join(reporte.get('informe', {}).get('conclusiones', [])),
        }

        return JsonResponse({
            'ok': True,
            **reporte,
            'tipo_error': tipo_error,
            'metodos': metodos_lista,
            'metodos_por_criterio': por_criterio,
            'propiedades_matriz': {
                'condicion_matriz': diag.get('condicion'),
                'determinante': diag.get('determinante'),
                'es_edd': diag.get('es_edd'),
            },
            'informe': informe_ext,
        })
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error al comparar métodos del Capítulo 2: {e}")


# =============================================== CAPÍTULO 3: INTERPOLACIÓN

def _adaptar_resultado_cap3(res, porcentaje_reserva):
    """Normaliza la estructura de interpolación para que coincida con todos los componentes de React."""
    n_ent = len(res.get('nodos_usados', []))
    n_res = len(res.get('datos_almacenados', []))
    val = res.get('validacion_reserva')
    if val:
        val_adaptada = {
            **val,
            'error_abs_medio': val.get('error_abs_promedio'),
            'error_rel_medio': val.get('error_rel_promedio'),
            'error_abs_max': val.get('error_abs_maximo'),
            'detalle': val.get('puntos', []),
        }
    else:
        val_adaptada = None

    ev = res.get('evaluacion')
    if ev:
        ev_adaptada = {
            **ev,
            'x_eval': ev.get('x'),
            'y_interp': ev.get('y'),
        }
    else:
        ev_adaptada = None

    curva_pts = res.get('grafica', {}).get('curva', [])
    curva_xy = {
        'x': [p['x'] for p in curva_pts],
        'y': [p['y'] for p in curva_pts],
        'y_real': [p.get('y_real') for p in curva_pts] if any('y_real' in p for p in curva_pts) else None,
        'puntos': curva_pts,
    }

    tramos_adaptados = None
    if res.get('tramos'):
        tramos_adaptados = [
            {
                **t,
                'indice': t.get('tramo'),
                'intervalo': [t.get('x_inicio'), t.get('x_fin')],
                'latex': t.get('polinomio_latex'),
            }
            for t in res['tramos']
        ]

    # Tabla de diferencias divididas tal cual: {columnas, filas}, con None en el triángulo vacío
    tabla_dif = res.get('tabla_diferencias') if isinstance(res.get('tabla_diferencias'), dict) else None

    bases_adaptadas = None
    if res.get('bases_lagrange'):
        bases_adaptadas = [
            {
                **b,
                'indice': b.get('k'),
                'latex': b.get('polinomio_latex'),
            }
            for b in res['bases_lagrange']
        ]

    grado = (n_ent - 1) if res.get('coeficientes') is not None else res.get('grado_spline')

    return {
        **res,
        'grado': grado,
        'n_entrenamiento': n_ent,
        'n_reservados': n_res,
        'n_total': n_ent + n_res,
        'porcentaje_reserva': val.get('porcentaje', porcentaje_reserva) if val else 0,
        'puntos_entrenamiento': res.get('nodos_usados', []),
        'puntos_reservados': res.get('datos_almacenados', []),
        'validacion_reserva': val_adaptada,
        'evaluacion_punto': ev_adaptada,
        'curva': curva_xy,
        'tramos': tramos_adaptados,
        'tabla_diferencias': tabla_dif,
        'matriz_vandermonde': res.get('detalles', {}).get('matriz_vandermonde'),
        'polinomios_base': bases_adaptadas,
    }


@csrf_exempt
def capitulo_3_ejecutar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        pct = float(d.get('porcentaje_reserva', 0))
        x_eval = d.get('x_eval') if 'x_eval' in d else d.get('x_evaluar')
        fx_real = d.get('fx_real') if 'fx_real' in d else d.get('funcion_real')

        res = it.ejecutar_interpolacion(
            metodo_clave=d.get('metodo', 'vandermonde'),
            x_in=d.get('x'),
            y_in=d.get('y'),
            porcentaje_reserva=pct,
            indices_reserva=d.get('indices_reserva'),
            x_evaluar=x_eval,
            funcion_real_texto=fx_real,
        )
        if not res.get('exito', True):
            return _error_json(res.get('mensaje', 'Error en la interpolación.'))

        adaptado = _adaptar_resultado_cap3(res, pct)
        return JsonResponse({'ok': True, 'resultado': adaptado, **adaptado})
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error en la interpolación: {e}")


@csrf_exempt
def capitulo_3_comparar(request):
    if request.method != 'POST':
        return _error_json("Usa método POST.", 405)
    try:
        d = _leer_json(request)
        pct = float(d.get('porcentaje_reserva', 20))
        x_eval = d.get('x_eval') if 'x_eval' in d else d.get('x_evaluar')
        fx_real = d.get('fx_real') if 'fx_real' in d else d.get('funcion_real')

        reporte = cmp.comparar_capitulo_3(
            x_in=d.get('x'),
            y_in=d.get('y'),
            porcentaje_reserva=pct,
            indices_reserva=d.get('indices_reserva'),
            x_evaluar=x_eval,
            funcion_real_texto=fx_real,
        )

        claves = ['vandermonde', 'newton', 'lagrange', 'spline_lineal', 'spline_cuadratico', 'spline_cubico']
        x_todos, y_todos = it.parsear_puntos(d.get('x'), d.get('y'), max_puntos=10)
        metodos_lista = []
        cond_vander = None
        for clave in claves:
            r = it.ejecutar_interpolacion(
                clave, x_todos, y_todos,
                porcentaje_reserva=pct,
                indices_reserva=d.get('indices_reserva'),
                x_evaluar=x_eval,
                funcion_real_texto=fx_real,
            )
            adap = _adaptar_resultado_cap3(r, pct)
            adap['id'] = clave
            if clave == 'vandermonde':
                cond_vander = r.get('detalles', {}).get('condicion_inf')
            metodos_lista.append(adap)

        con_val = [m for m in metodos_lista if m.get('validacion_reserva') and m['validacion_reserva'].get('error_abs_medio') is not None]
        ganador_abs = min(con_val, key=lambda m: m['validacion_reserva']['error_abs_medio'])['metodo'] if con_val else 'Empate Algebraico'
        ganador_rel = min(
            [m for m in con_val if m['validacion_reserva'].get('error_rel_medio') is not None],
            key=lambda m: m['validacion_reserva']['error_rel_medio'],
            default={},
        ).get('metodo', 'Empate Algebraico')

        informe_ext = {
            **reporte.get('informe', {}),
            'ganador_validacion_abs': ganador_abs,
            'ganador_validacion_rel': ganador_rel,
            'condicion_vandermonde': cond_vander,
            'conclusion_general': " ".join(reporte.get('informe', {}).get('conclusiones', [])),
        }

        primero = metodos_lista[0] if metodos_lista else {}
        return JsonResponse({
            'ok': True,
            'comparacion': reporte,
            **reporte,
            'porcentaje_reserva': primero.get('porcentaje_reserva', pct),
            'puntos_entrenamiento': primero.get('puntos_entrenamiento', []),
            'puntos_reservados': primero.get('puntos_reservados', []),
            'metodos': metodos_lista,
            'informe': informe_ext,
        })
    except ValueError as e:
        return _error_json(e)
    except Exception as e:
        return _error_json(f"Error al comparar interpolaciones: {e}")


def _cargar_registros():
    if not STORAGE_FILE.exists():
        inicial = [
            {
                'id': 'ej-ejemnewt',
                'nombre': 'Ejemplo Clase (5 pts — 20% almacenado)',
                'fecha': '2026-11-08',
                'x': [19.0, 25.0, 29.0, 33.0, 37.0],
                'y': [5.8, 2.1, -1.3, 9.2, 8.8],
                'x_todos': [19.0, 25.0, 29.0, 33.0, 37.0],
                'y_todos': [5.8, 2.1, -1.3, 9.2, 8.8],
                'porcentaje_almacenado': 20.0,
                'x_almacenados': [29.0],
                'y_almacenados': [-1.3],
                'x_entrenamiento': [19.0, 25.0, 33.0, 37.0],
                'y_entrenamiento': [5.8, 2.1, 9.2, 8.8],
            },
            {
                'id': 'ej-vander2',
                'nombre': 'Curva Exponencial (6 pts — 30% almacenado)',
                'fecha': '2026-11-08',
                'x': [1.8, 2.0, 2.5, 3.0, 4.0, 5.0],
                'y': [4.53454611, 1.32919299, 0.55675809, 0.35554227, 0.1852911, 0.10763107],
                'x_todos': [1.8, 2.0, 2.5, 3.0, 4.0, 5.0],
                'y_todos': [4.53454611, 1.32919299, 0.55675809, 0.35554227, 0.1852911, 0.10763107],
                'porcentaje_almacenado': 30.0,
                'x_almacenados': [2.0, 4.0],
                'y_almacenados': [1.32919299, 0.1852911],
                'x_entrenamiento': [1.8, 2.5, 3.0, 5.0],
                'y_entrenamiento': [4.53454611, 0.55675809, 0.35554227, 0.10763107],
            },
        ]
        STORAGE_FILE.write_text(json.dumps(inicial, indent=2, ensure_ascii=False), encoding='utf-8')
        return inicial
    try:
        datos = json.loads(STORAGE_FILE.read_text(encoding='utf-8'))
        for item in datos:
            if 'x' not in item and 'x_todos' in item:
                item['x'] = item['x_todos']
            if 'y' not in item and 'y_todos' in item:
                item['y'] = item['y_todos']
        return datos
    except Exception:
        return []


@csrf_exempt
def capitulo_3_almacenamiento(request):
    """Permite listar, guardar o eliminar conjuntos de datos (con su 20% o 30% almacenado)."""
    registros = _cargar_registros()
    if request.method == 'GET':
        return JsonResponse({'ok': True, 'registros': registros, 'datasets': registros})

    if request.method == 'POST':
        try:
            d = _leer_json(request)
            nombre = str(d.get('nombre', '')).strip() or f"Dataset ({datetime.now().strftime('%H:%M:%S')})"
            porcentaje = float(d.get('porcentaje_almacenado') or d.get('porcentaje_reserva', 20))
            if porcentaje not in (20.0, 30.0, 0.0):
                porcentaje = 20.0
            x_todos, y_todos = it.parsear_puntos(d.get('x'), d.get('y'), max_puntos=10)
            part = it.separar_reserva_datos(
                x_todos, y_todos,
                porcentaje=porcentaje if porcentaje > 0 else 20,
                indices_manuales=d.get('indices_reserva'),
            )
            nuevo = {
                'id': f"ds-{int(datetime.now().timestamp() * 1000)}",
                'nombre': nombre,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'x': [float(v) for v in x_todos],
                'y': [float(v) for v in y_todos],
                'x_todos': [float(v) for v in x_todos],
                'y_todos': [float(v) for v in y_todos],
                'porcentaje_almacenado': part['porcentaje_aplicado'],
                'x_almacenados': [float(v) for v in part['x_almacenados']],
                'y_almacenados': [float(v) for v in part['y_almacenados']],
                'x_entrenamiento': [float(v) for v in part['x_entrenamiento']],
                'y_entrenamiento': [float(v) for v in part['y_entrenamiento']],
            }
            registros.insert(0, nuevo)
            STORAGE_FILE.write_text(json.dumps(registros[:25], indent=2, ensure_ascii=False), encoding='utf-8')
            return JsonResponse({'ok': True, 'registro': nuevo, 'registros': registros[:25], 'datasets': registros[:25]})
        except ValueError as e:
            return _error_json(e)
        except Exception as e:
            return _error_json(f"No se pudo almacenar el conjunto de datos: {e}")

    if request.method == 'DELETE':
        try:
            d = _leer_json(request)
            id_borrar = d.get('id')
            registros = [r for r in registros if r.get('id') != id_borrar]
            STORAGE_FILE.write_text(json.dumps(registros, indent=2, ensure_ascii=False), encoding='utf-8')
            return JsonResponse({'ok': True, 'registros': registros, 'datasets': registros})
        except Exception as e:
            return _error_json(f"Error al eliminar registro: {e}")

    return _error_json("Método no permitido.", 405)
