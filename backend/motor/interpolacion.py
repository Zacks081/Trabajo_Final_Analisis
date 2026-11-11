"""Métodos de interpolación (Capítulo 3):
- Vandermonde
- Newton con diferencias divididas
- Lagrange
- Trazador (Spline) Lineal (grado 1)
- Trazador (Spline) Cuadrático (grado 2)
- Trazador (Spline) Cúbico Natural (grado 3)

Incluye soporte para:
- Hasta 10 puntos (x, y)
- Reserva / almacenamiento del 20% o 30% de los datos (para validación y persistencia)
- Evaluación en un punto x* y comparación contra función real f(x)
"""
import math
import re
import time

import numpy as np

from . import sistemas as si
from .funciones import Funcion, interpretar_numero

EXITO = 'exito'
ERROR = 'error'

NODO = 'nodo'
INTERPOLACION = 'interpolacion'
EXTRAPOLACION = 'extrapolacion'

_COND_GRANDE = 1e6

_ORDINALES = {
    1: '1ra', 2: '2da', 3: '3ra', 4: '4ta', 5: '5ta',
    6: '6ta', 7: '7ma', 8: '8va', 9: '9na', 10: '10ma'
}


def _limpio(v):
    if v is None:
        return None
    try:
        vf = float(v)
        if not math.isfinite(vf):
            return None
        return 0.0 if abs(vf) < 1e-14 else vf
    except Exception:
        return None


def parsear_puntos(x_in, y_in, max_puntos=10):
    """Lee vectores x e y desde listas o cadenas separadas por espacios/comas/corchetes."""
    def _valor(v, etiqueta):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"El valor {etiqueta} está vacío.")
        try:
            return interpretar_numero(v)
        except ValueError:
            raise ValueError(f"El valor {etiqueta} = '{v}' no es un número válido.")

    def _a_lista(entrada, nombre):
        if entrada is None:
            raise ValueError(f"Faltan los valores de {nombre}.")
        if isinstance(entrada, (list, tuple, np.ndarray)):
            return [_valor(v, f"{nombre}{i}") for i, v in enumerate(np.asarray(entrada, dtype=object).flatten())]
        if isinstance(entrada, str):
            texto = re.sub(r'^\s*[a-zA-Z]\w*\s*=', '', entrada).strip()
            if texto.startswith('[') and texto.endswith(']'):
                texto = texto[1:-1]
            partes = [e for e in re.split(r'[\s,;]+', texto) if e]
            if not partes:
                raise ValueError(f"La lista de valores de {nombre} está vacía.")
            return [_valor(e, f"{nombre}{i}") for i, e in enumerate(partes)]
        raise ValueError(f"Formato no válido para {nombre}.")

    x = np.array(_a_lista(x_in, "x"), dtype=float)
    y = np.array(_a_lista(y_in, "y"), dtype=float)

    if len(x) != len(y):
        raise ValueError(f"x tiene {len(x)} valores e y tiene {len(y)}: ambos deben tener la misma cantidad de datos.")
    if len(x) < 2:
        raise ValueError("Se necesitan al menos 2 puntos para interpolar.")
    if len(x) > max_puntos:
        raise ValueError(f"Se permiten hasta {max_puntos} puntos como máximo (ingresaste {len(x)}).")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("Todos los puntos (x, y) deben ser números reales finitos.")
    valores, veces = np.unique(x, return_counts=True)
    repetidos = valores[veces > 1]
    if repetidos.size:
        rep_str = ", ".join(f"{v:g}" for v in repetidos)
        raise ValueError(f"Hay valores de x repetidos ({rep_str}): una función no puede tener dos valores de y para el mismo x.")
    return x, y


def separar_reserva_datos(x, y, porcentaje=0, indices_manuales=None):
    """Separa el 20% o 30% de los datos para almacenarlos y evaluar la calidad del polinomio.

    Mantiene los extremos (mínimo y máximo de x) en el conjunto de construcción para
    que los puntos reservados queden dentro del intervalo de interpolación.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)

    if indices_manuales:
        idx_res = sorted({int(i) for i in indices_manuales if 0 <= int(i) < n})
        if n - len(idx_res) < 2:
            raise ValueError("Deben quedar al menos 2 puntos activos para construir el polinomio.")
    elif porcentaje and porcentaje > 0:
        if n < 4:
            raise ValueError("Para almacenar el 20% o 30% de los datos y dejar suficientes nodos de interpolación, ingresa al menos 4 puntos.")
        k = max(1, int(round(n * (float(porcentaje) / 100.0))))
        k = min(k, n - 2)
        orden_x = np.argsort(x)
        interiores = orden_x[1:-1]
        posiciones = np.linspace(0, len(interiores) - 1, k, dtype=int)
        idx_res = sorted(int(interiores[p]) for p in np.unique(posiciones))
    else:
        idx_res = []

    mascara_res = np.zeros(n, dtype=bool)
    if idx_res:
        mascara_res[idx_res] = True

    return {
        'x_entrenamiento': x[~mascara_res],
        'y_entrenamiento': y[~mascara_res],
        'x_almacenados': x[mascara_res],
        'y_almacenados': y[mascara_res],
        'indices_almacenados': idx_res,
        'porcentaje_aplicado': round(100.0 * len(idx_res) / n, 1) if n else 0.0,
    }


def tipo_punto(x, t):
    if np.any(np.isclose(x, t, atol=1e-12)):
        return NODO
    if np.min(x) < t < np.max(x):
        return INTERPOLACION
    return EXTRAPOLACION


def evaluar_polinomio_o_tramos(x_nodos, coefs, tramos, t):
    t_arr = np.asarray(t, dtype=float)
    if tramos is None:
        r = np.polyval(coefs, t_arr)
    else:
        j = np.clip(np.searchsorted(x_nodos, t_arr, side='right') - 1, 0, len(x_nodos) - 2)
        coef = tramos[j]
        r = np.zeros_like(t_arr, dtype=float)
        for k in range(tramos.shape[1]):
            r = r * t_arr + coef[..., k]
    return float(r) if np.ndim(r) == 0 else r


def formatear_polinomio(coefs, decimales=8):
    """Convierte [a_n, ..., a_0] a texto legible y a LaTeX."""
    coefs = np.asarray(coefs, dtype=float)
    grado = len(coefs) - 1
    escala = float(np.max(np.abs(coefs))) if coefs.size else 0.0
    terminos_txt = []
    terminos_ltx = []

    for k, c in enumerate(coefs):
        if c == 0 or (escala > 0 and abs(c) <= 1e-12 * escala):
            continue
        p = grado - k
        abs_c = abs(c)
        if abs_c != 0 and (abs_c < 1e-4 or abs_c >= 1e7):
            num_txt = f"{abs_c:.4e}"
            base, exp = f"{abs_c:.4e}".split('e')
            num_ltx = f"{base} \\times 10^{{{int(exp)}}}"
        else:
            num_txt = f"{abs_c:.{decimales}f}".rstrip('0').rstrip('.') or '0'
            num_ltx = num_txt

        if p == 0:
            var_txt, var_ltx = "", ""
        elif p == 1:
            var_txt, var_ltx = "x", "x"
        else:
            var_txt, var_ltx = f"x^{p}", f"x^{{{p}}}"

        coef_mostrar_txt = "" if (p > 0 and abs(abs_c - 1.0) < 1e-12) else num_txt
        coef_mostrar_ltx = "" if (p > 0 and abs(abs_c - 1.0) < 1e-12) else num_ltx

        terminos_txt.append((c < 0, f"{coef_mostrar_txt}{var_txt}"))
        terminos_ltx.append((c < 0, f"{coef_mostrar_ltx}{var_ltx}"))

    def _unir(lista):
        if not lista:
            return "0"
        s = ("-" if lista[0][0] else "") + lista[0][1]
        for neg, t in lista[1:]:
            s += (" - " if neg else " + ") + t
        return s

    return _unir(terminos_txt), _unir(terminos_ltx)


def _factor_txt(v):
    if abs(v) < 1e-14:
        return "x"
    return f"(x - {v:.8g})" if v > 0 else f"(x + {-v:.8g})"


def _factor_ltx(v):
    if abs(v) < 1e-14:
        return "x"
    return f"(x - {v:.8g})" if v > 0 else f"(x + {-v:.8g})"


def formatear_newton(b, x):
    terminos_txt = []
    terminos_ltx = []
    for k, bk in enumerate(b):
        if abs(bk) < 1e-14:
            continue
        abs_b = abs(bk)
        num = f"{abs_b:.8g}"
        factores_t = "".join(_factor_txt(v) for v in x[:k])
        factores_l = "".join(_factor_ltx(v) for v in x[:k])
        terminos_txt.append((bk < 0, f"{num}{factores_t}"))
        terminos_ltx.append((bk < 0, f"{num}{factores_l}"))

    def _unir(lista):
        if not lista:
            return "0"
        s = ("-" if lista[0][0] else "") + lista[0][1]
        for neg, t in lista[1:]:
            s += (" - " if neg else " + ") + t
        return s

    return _unir(terminos_txt), _unir(terminos_ltx)


def _resolver_sistema_interno(A, b):
    r = si.gauss(A, b, pivoteo=1)
    if not r['exito']:
        return None, r['mensaje']
    return np.array(r['solucion'], dtype=float), None


# --------------------------------------------------------------- métodos

def vandermonde(x, y):
    n = len(x)
    A = np.vander(x)
    a, problema = _resolver_sistema_interno(A, y)
    if problema:
        return {'metodo': 'Vandermonde', 'estado': ERROR, 'exito': False, 'mensaje': problema}
    cond = float(np.linalg.cond(A, np.inf))
    avisos = []
    if cond > _COND_GRANDE:
        avisos.append(
            f"La matriz de Vandermonde presenta alto número de condición (κ∞ = {cond:.3e}): "
            f"pueden presentarse errores de redondeo en los coeficientes."
        )
    poly_txt, poly_ltx = formatear_polinomio(a)
    return {
        'metodo': 'Vandermonde',
        'estado': EXITO,
        'exito': True,
        'mensaje': f"Polinomio interpolante de grado ≤ {n-1} construido con {n} puntos.",
        'x': [_limpio(v) for v in x],
        'y': [_limpio(v) for v in y],
        'coeficientes': [_limpio(v) for v in a],
        'polinomio_texto': poly_txt,
        'polinomio_latex': poly_ltx,
        'tramos': None,
        'avisos': avisos,
        'detalles': {
            'matriz_vandermonde': [[_limpio(v) for v in fila] for fila in A],
            'vector_y': [_limpio(v) for v in y],
            'condicion_inf': _limpio(cond),
        },
    }


def tabla_diferencias(x, y):
    n = len(x)
    T = np.zeros((n, n + 1))
    T[:, 0] = x
    T[:, 1] = y
    for j in range(2, n + 1):
        for i in range(j - 1, n):
            T[i, j] = (T[i, j - 1] - T[i - 1, j - 1]) / (T[i, 0] - T[i - j + 1, 0])
    return T


def newton_a_coeficientes(x, b):
    pol = np.array([b[0]], dtype=float)
    acum = np.array([1.0])
    for i in range(len(x) - 1):
        pol = np.concatenate(([0.0], pol))
        acum = np.convolve(acum, [1.0, -x[i]])
        pol = pol + b[i + 1] * acum
    return pol


def newton(x, y):
    n = len(x)
    T = tabla_diferencias(x, y)
    b = np.diag(T, 1).copy()
    coefs = newton_a_coeficientes(x, b)
    columnas = ['i', 'xi', 'f[xi]'] + [_ORDINALES.get(k, f'{k}ª') for k in range(1, n)]
    filas = [
        [i, _limpio(x[i]), _limpio(T[i, 1])] + [_limpio(T[i, k + 1]) if k <= i else None for k in range(1, n)]
        for i in range(n)
    ]
    poly_txt, poly_ltx = formatear_polinomio(coefs)
    newt_txt, newt_ltx = formatear_newton(b, x)
    return {
        'metodo': 'Newton (Diferencias Divididas)',
        'estado': EXITO,
        'exito': True,
        'mensaje': f"Polinomio interpolante de Newton de grado ≤ {n-1} ({n} puntos).",
        'x': [_limpio(v) for v in x],
        'y': [_limpio(v) for v in y],
        'coeficientes': [_limpio(v) for v in coefs],
        'polinomio_texto': poly_txt,
        'polinomio_latex': poly_ltx,
        'forma_newton_texto': newt_txt,
        'forma_newton_latex': newt_ltx,
        'coeficientes_newton': [_limpio(v) for v in b],
        'tabla_diferencias': {'columnas': columnas, 'filas': filas},
        'tramos': None,
        'avisos': [],
        'detalles': {},
    }


def lagrange(x, y):
    n = len(x)
    pol = np.zeros(n)
    bases = []
    for i in range(n):
        Li = np.array([1.0])
        den = 1.0
        for j in range(n):
            if j != i:
                Li = np.convolve(Li, [1.0, -x[j]])
                den = den * (x[i] - x[j])
        coefs_base = Li / den
        pol = pol + y[i] * coefs_base
        num_str = "".join(_factor_txt(v) for j, v in enumerate(x) if j != i)
        b_txt, b_ltx = formatear_polinomio(coefs_base)
        bases.append({
            'k': i,
            'yi': _limpio(y[i]),
            'numerador': num_str,
            'denominador': _limpio(den),
            'polinomio_texto': b_txt,
            'polinomio_latex': b_ltx,
        })

    poly_txt, poly_ltx = formatear_polinomio(pol)
    return {
        'metodo': 'Lagrange',
        'estado': EXITO,
        'exito': True,
        'mensaje': f"Polinomio interpolante de Lagrange de grado ≤ {n-1} ({n} puntos).",
        'x': [_limpio(v) for v in x],
        'y': [_limpio(v) for v in y],
        'coeficientes': [_limpio(v) for v in pol],
        'polinomio_texto': poly_txt,
        'polinomio_latex': poly_ltx,
        'bases_lagrange': bases,
        'tramos': None,
        'avisos': [],
        'detalles': {},
    }


def _fila_trazador(v, d, orden):
    return np.array([
        math.perm(p, orden) * (v ** (p - orden)) if p >= orden else 0.0
        for p in range(d, -1, -1)
    ])


def sistema_trazador(x, y, d):
    n = len(x)
    m = (d + 1) * (n - 1)
    A = np.zeros((m, m))
    b = np.zeros(m)
    h = 0
    for i in range(n - 1):
        A[h, (d + 1) * i:(d + 1) * (i + 1)] = _fila_trazador(x[i], d, 0)
        b[h] = y[i]
        h += 1
    for i in range(1, n):
        A[h, (d + 1) * (i - 1):(d + 1) * i] = _fila_trazador(x[i], d, 0)
        b[h] = y[i]
        h += 1
    for orden in range(1, d):
        for i in range(1, n - 1):
            fila = _fila_trazador(x[i], d, orden)
            A[h, (d + 1) * (i - 1):(d + 1) * i] = fila
            A[h, (d + 1) * i:(d + 1) * (i + 1)] = -fila
            h += 1
    if d >= 2:
        A[h, 0:d + 1] = _fila_trazador(x[0], d, 2)
        h += 1
    if d == 3:
        A[h, m - 4:m] = _fila_trazador(x[-1], d, 2)
    return A, b


def trazador(x, y, d=3):
    nombres_d = {1: "Spline Lineal (Grado 1)", 2: "Spline Cuadrático (Grado 2)", 3: "Spline Cúbico Natural (Grado 3)"}
    avisos = []
    orden = np.argsort(x, kind='stable')
    if np.any(orden != np.arange(len(x))):
        x, y = x[orden], y[orden]
        avisos.append("Los nodos se ordenaron automáticamente de menor a mayor en x para construir los tramos del spline.")

    A, b = sistema_trazador(x, y, d)
    c, problema = _resolver_sistema_interno(A, b)
    if problema:
        return {
            'metodo': nombres_d.get(d, f"Spline grado {d}"),
            'estado': ERROR,
            'exito': False,
            'mensaje': problema,
        }

    matriz_tramos = c.reshape(len(x) - 1, d + 1)
    tramos_info = []
    for j in range(len(x) - 1):
        t_txt, t_ltx = formatear_polinomio(matriz_tramos[j])
        tramos_info.append({
            'tramo': j + 1,
            'x_inicio': _limpio(x[j]),
            'x_fin': _limpio(x[j + 1]),
            'intervalo': f"{x[j]:.6g} ≤ x ≤ {x[j+1]:.6g}",
            'coeficientes': [_limpio(v) for v in matriz_tramos[j]],
            'polinomio_texto': t_txt,
            'polinomio_latex': t_ltx,
        })

    letras = "abcd"[:d + 1]
    incognitas = [f"{letra}{j}" for j in range(1, len(x)) for letra in letras]

    return {
        'metodo': nombres_d.get(d, f"Spline grado {d}"),
        'grado_spline': d,
        'estado': EXITO,
        'exito': True,
        'mensaje': f"{nombres_d.get(d)} construido con {len(x) - 1} tramos.",
        'x': [_limpio(v) for v in x],
        'y': [_limpio(v) for v in y],
        'coeficientes': None,
        'polinomio_texto': " | ".join(f"p{t['tramo']}(x) = {t['polinomio_texto']} [{t['intervalo']}]" for t in tramos_info),
        'tramos': tramos_info,
        '_tramos_np': matriz_tramos,
        'avisos': avisos,
        'detalles': {
            'incognitas': incognitas,
            'matriz_sistema': [[_limpio(v) for v in fila] for fila in A],
            'vector_b': [_limpio(v) for v in b],
            'condicion_inf': _limpio(np.linalg.cond(A, np.inf)),
        },
    }


def ejecutar_interpolacion(metodo_clave, x_in, y_in, porcentaje_reserva=0, indices_reserva=None,
                           x_evaluar=None, funcion_real_texto=None):
    """Ejecuta un método de interpolación con soporte de reserva del 20%/30%, evaluación y gráfica."""
    t0 = time.perf_counter()
    x_todos, y_todos = parsear_puntos(x_in, y_in, max_puntos=10)
    particion = separar_reserva_datos(x_todos, y_todos, porcentaje=porcentaje_reserva, indices_manuales=indices_reserva)
    x_ent = particion['x_entrenamiento']
    y_ent = particion['y_entrenamiento']
    x_alm = particion['x_almacenados']
    y_alm = particion['y_almacenados']

    constructores = {
        'vandermonde': lambda: vandermonde(x_ent, y_ent),
        'newton': lambda: newton(x_ent, y_ent),
        'lagrange': lambda: lagrange(x_ent, y_ent),
        'spline_lineal': lambda: trazador(x_ent, y_ent, 1),
        'spline_cuadratico': lambda: trazador(x_ent, y_ent, 2),
        'spline_cubico': lambda: trazador(x_ent, y_ent, 3),
    }
    if metodo_clave not in constructores:
        raise ValueError(f"Método de interpolación '{metodo_clave}' no reconocido.")

    res = constructores[metodo_clave]()
    if not res['exito']:
        return res

    x_nodos = np.array(res['x'], dtype=float)
    coefs_np = np.array(res['coeficientes'], dtype=float) if res['coeficientes'] is not None else None
    tramos_np = res.pop('_tramos_np', None)

    def _eval(val_x):
        return evaluar_polinomio_o_tramos(x_nodos, coefs_np, tramos_np, val_x)

    # Evaluación sobre el 20% o 30% de datos almacenados (si se activó la reserva)
    validacion_reserva = None
    if len(x_alm) > 0:
        filas_val = []
        errores_abs = []
        errores_rel = []
        for xv, yv in zip(x_alm, y_alm):
            yp = float(_eval(xv))
            ea = abs(yv - yp)
            er = ea / abs(yv) if yv != 0 else float('nan')
            errores_abs.append(ea)
            if math.isfinite(er):
                errores_rel.append(er)
            filas_val.append({
                'x': _limpio(xv),
                'y_real': _limpio(yv),
                'y_interpolado': _limpio(yp),
                'error_abs': _limpio(ea),
                'error_rel': _limpio(er),
            })
        validacion_reserva = {
            'porcentaje': particion['porcentaje_aplicado'],
            'cantidad_almacenados': len(x_alm),
            'cantidad_usados': len(x_ent),
            'puntos': filas_val,
            'error_abs_promedio': _limpio(np.mean(errores_abs)) if errores_abs else None,
            'error_abs_maximo': _limpio(np.max(errores_abs)) if errores_abs else None,
            'error_rel_promedio': _limpio(np.mean(errores_rel)) if errores_rel else None,
        }

    # Función real opcional para comparar
    f_real = None
    if funcion_real_texto and str(funcion_real_texto).strip():
        f_real = Funcion.desde_texto(funcion_real_texto)

    # Evaluación en un punto x* opcional
    evaluacion_punto = None
    if x_evaluar is not None and str(x_evaluar).strip() != '':
        t_val = interpretar_numero(x_evaluar)
        y_est = float(_eval(t_val))
        t_tipo = tipo_punto(x_nodos, t_val)
        evaluacion_punto = {
            'x': _limpio(t_val),
            'y': _limpio(y_est),
            'tipo': t_tipo,
        }
        if f_real is not None:
            y_exacto = f_real(t_val)
            ea_p = abs(y_exacto - y_est) if math.isfinite(y_exacto) else float('nan')
            er_p = ea_p / abs(y_exacto) if (math.isfinite(ea_p) and y_exacto != 0) else float('nan')
            evaluacion_punto['y_real'] = _limpio(y_exacto)
            evaluacion_punto['error_abs'] = _limpio(ea_p)
            evaluacion_punto['error_rel'] = _limpio(er_p)

    # Datos para la gráfica interactiva
    lo = float(np.min(x_todos))
    hi = float(np.max(x_todos))
    if evaluacion_punto is not None and evaluacion_punto['x'] is not None:
        lo = min(lo, evaluacion_punto['x'])
        hi = max(hi, evaluacion_punto['x'])
    margen = 0.08 * (hi - lo if hi > lo else 2.0)
    xs_plot = np.linspace(lo - margen, hi + margen, 300)
    ys_plot = _eval(xs_plot)
    ys_real = f_real.evaluar_arreglo(xs_plot) if f_real is not None else None

    serie_curva = []
    for idx in range(len(xs_plot)):
        item = {
            'x': round(float(xs_plot[idx]), 6),
            'y': _limpio(ys_plot[idx]),
        }
        if ys_real is not None:
            item['y_real'] = _limpio(ys_real[idx])
        serie_curva.append(item)

    res['tiempo_ms'] = round((time.perf_counter() - t0) * 1000, 3)
    res['nodos_usados'] = [{'x': _limpio(xv), 'y': _limpio(yv)} for xv, yv in zip(x_ent, y_ent)]
    res['datos_almacenados'] = [{'x': _limpio(xv), 'y': _limpio(yv)} for xv, yv in zip(x_alm, y_alm)]
    res['validacion_reserva'] = validacion_reserva
    res['evaluacion'] = evaluacion_punto
    res['grafica'] = {
        'curva': serie_curva,
        'nodos': res['nodos_usados'],
        'almacenados': res['datos_almacenados'],
        'punto_evaluado': evaluacion_punto,
    }
    return res
