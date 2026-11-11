"""Métodos para ecuaciones no lineales f(x) = 0 (Capítulo 1).

Soporta parada y análisis bajo los tres tipos de error exigidos:
- 'abs'  : Error absoluto  |xi - xi-1| <= Tol
- 'rel'  : Error relativo  |xi - xi-1| / |xi| <= Tol
- 'cond' : Error de condición (residual) |f(xi)| <= Tol
"""
import math
import time
from dataclasses import dataclass, field

import numpy as np

NAN = float('nan')

# Estados posibles
RAIZ = 'raiz'
APROXIMACION = 'aproximacion'
FRACASO = 'fracaso'
DIVERGE = 'diverge'
DETENIDO = 'detenido'
INTERVALO = 'intervalo'
INADECUADO = 'inadecuado'
INCONSISTENTE = 'inconsistente'   # punto fijo: g(x) converge, pero su punto fijo no es raíz de f(x)


@dataclass
class ResultadoNoLineal:
    metodo: str
    estado: str
    mensaje: str
    columnas: list
    filas: list = field(default_factory=list)
    valor: float = None
    fx_final: float = None
    iteracion: int = None
    error_abs: float = None
    error_rel: float = None
    error_cond: float = None
    puntos: list = field(default_factory=list)
    pasos_grafica: list = field(default_factory=list)
    tiempo_ms: float = 0.0
    extras: dict = field(default_factory=dict)


def _finito(*valores):
    return all(v is not None and isinstance(v, (int, float, np.number)) and math.isfinite(v) for v in valores)


def _limpio(v):
    """Convierte nan/inf a None para serialización JSON limpia."""
    if v is None:
        return None
    try:
        vf = float(v)
        return vf if math.isfinite(vf) else None
    except Exception:
        return None


def _errores(nuevo, anterior, fx):
    """Devuelve (error_absoluto, error_relativo, error_condicion)."""
    ea = abs(nuevo - anterior) if _finito(nuevo, anterior) else NAN
    er = ea / abs(nuevo) if (_finito(ea, nuevo) and nuevo != 0) else NAN
    ec = abs(fx) if _finito(fx) else NAN
    return ea, er, ec


def _control(ea, er, ec, tipo_error):
    """Error que decide la parada según el criterio elegido."""
    if tipo_error == 'rel':
        return er if _finito(er) else math.inf
    if tipo_error == 'cond':
        return ec if _finito(ec) else math.inf
    return ea if _finito(ea) else math.inf


def _nombre_error(tipo_error):
    if tipo_error == 'rel':
        return "error relativo"
    if tipo_error == 'cond':
        return "error de condición |f(x)|"
    return "error absoluto"


def _fin_iterativo(res, x, c, ea, er, ec, tol, tipo_error, fx, t0):
    res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res.valor = x
    res.fx_final = fx
    res.iteracion = c
    res.error_abs = ea
    res.error_rel = er
    res.error_cond = ec
    error = _control(ea, er, ec, tipo_error)
    if fx == 0:
        res.estado = RAIZ
        res.mensaje = f"{x:.10g} es raíz exacta de f(x) (f(x) = 0) en la iteración {c}."
    elif error <= tol:
        res.estado = APROXIMACION
        res.mensaje = (
            f"{x:.10g} es una aproximación a la raíz con {_nombre_error(tipo_error)} "
            f"{error:.3e} ≤ Tol ({tol:g}) en {c} iteraciones."
        )
    else:
        res.estado = FRACASO
        res.mensaje = (
            f"Se alcanzó el máximo de {c} iteraciones sin cumplir la tolerancia "
            f"({_nombre_error(tipo_error)} = {error:.3e} > {tol:g})."
        )
    return res


def _diverge(res, x, c, que, t0):
    res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res.estado = DIVERGE
    res.valor, res.iteracion = x, c
    res.mensaje = (
        f"El método diverge: en la iteración {c} no se pudo evaluar {que} "
        f"(valor desbordado o fuera del dominio real)."
    )
    return res


# ------------------------------------------------------------------ métodos

def busquedas_incrementales(f, x0, dx, niter):
    t0 = time.perf_counter()
    res = ResultadoNoLineal("Búsquedas Incrementales", '', '', ['i', 'xi', 'f(xi)'])
    f0 = f(x0)
    res.filas.append([0, x0, f0])
    res.puntos.append(x0)
    if not _finito(f0):
        return _diverge(res, x0, 0, "f(x0)", t0)
    if f0 == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = RAIZ, x0, 0.0, 0
        res.mensaje = f"{x0:.10g} es raíz exacta de f(x)."
        return res

    x1 = x0 + dx
    f1 = f(x1)
    c = 1
    res.filas.append([c, x1, f1])
    res.puntos.append(x1)
    intervalos = []
    if _finito(f0, f1) and f0 * f1 < 0:
        intervalos.append((min(x0, x1), max(x0, x1)))

    while _finito(f1) and f0 * f1 > 0 and c < niter:
        x0, f0 = x1, f1
        x1 = x0 + dx
        f1 = f(x1)
        c += 1
        res.filas.append([c, x1, f1])
        res.puntos.append(x1)
        if _finito(f0, f1) and f0 * f1 < 0:
            intervalos.append((min(x0, x1), max(x0, x1)))

    res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res.iteracion = c
    if not _finito(f1):
        res.estado, res.valor = DIVERGE, x1
        res.mensaje = f"f(x) no está definida en x = {x1:.6g} (iteración {c})."
    elif f1 == 0:
        res.estado, res.valor, res.fx_final = RAIZ, x1, 0.0
        res.mensaje = f"{x1:.10g} es raíz exacta de f(x) (iteración {c})."
    elif f0 * f1 < 0:
        res.estado, res.valor = INTERVALO, (x0 + x1) / 2.0
        res.extras['intervalo'] = (min(x0, x1), max(x0, x1))
        res.extras['intervalos'] = intervalos
        res.mensaje = f"Se detectó cambio de signo: existe al menos una raíz en [{min(x0, x1):.6g}, {max(x0, x1):.6g}] (iteración {c})."
    else:
        res.estado = FRACASO
        res.mensaje = f"Fracasó en {niter} iteraciones: no se encontró cambio de signo desde x0 = {res.puntos[0]:g} con Δx = {dx:g}."
    return res


def _por_intervalos(nombre, f, a, b, tol, niter, tipo_error, siguiente):
    t0 = time.perf_counter()
    res = ResultadoNoLineal(nombre, '', '', ['i', 'a', 'xm', 'b', 'f(xm)', 'E abs', 'E rel', 'E cond'])
    fi, fs = f(a), f(b)
    if not _finito(fi, fs):
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado = INADECUADO
        res.mensaje = "f(x) no está definida o no es finita en alguno de los extremos [a, b]."
        return res
    if fi == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = RAIZ, a, 0.0, 0
        res.error_abs, res.error_rel, res.error_cond = 0.0, 0.0, 0.0
        res.mensaje = f"El extremo izquierdo a = {a:.10g} es raíz exacta de f(x)."
        return res
    if fs == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = RAIZ, b, 0.0, 0
        res.error_abs, res.error_rel, res.error_cond = 0.0, 0.0, 0.0
        res.mensaje = f"El extremo derecho b = {b:.10g} es raíz exacta de f(x)."
        return res
    if fi * fs > 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado = INADECUADO
        res.mensaje = (
            f"Intervalo [{a:g}, {b:g}] inadecuado: f(a) = {fi:.6g} y f(b) = {fs:.6g} tienen el mismo signo "
            f"(no cumple el Teorema de Bolzano f(a)·f(b) < 0)."
        )
        return res

    c = 0
    xm = siguiente(a, b, fi, fs)
    fm = f(xm)
    ec = abs(fm) if _finito(fm) else NAN
    ea, er = NAN, NAN
    error = ec if tipo_error == 'cond' else (tol + 1)
    res.filas.append([c, a, xm, b, fm, ea, er, ec])
    res.puntos.append(xm)
    res.pasos_grafica.append({'i': c, 'a': _limpio(a), 'b': _limpio(b), 'xm': _limpio(xm), 'fxm': _limpio(fm), 'fa': _limpio(fi), 'fb': _limpio(fs)})

    while error > tol and fm != 0 and c < niter:
        if not _finito(fm):
            return _diverge(res, xm, c, "f(xm)", t0)
        if fi * fm < 0:
            b, fs = xm, fm
        else:
            a, fi = xm, fm
        xa = xm
        xm = siguiente(a, b, fi, fs)
        fm = f(xm)
        ea, er, ec = _errores(xm, xa, fm)
        error = _control(ea, er, ec, tipo_error)
        c += 1
        res.filas.append([c, a, xm, b, fm, ea, er, ec])
        res.puntos.append(xm)
        res.pasos_grafica.append({'i': c, 'a': _limpio(a), 'b': _limpio(b), 'xm': _limpio(xm), 'fxm': _limpio(fm), 'fa': _limpio(fi), 'fb': _limpio(fs)})

    if not _finito(fm):
        return _diverge(res, xm, c, "f(xm)", t0)
    return _fin_iterativo(res, xm, c, ea, er, ec, tol, tipo_error, fm, t0)


def biseccion(f, a, b, tol, niter, tipo_error='abs'):
    return _por_intervalos("Bisección", f, a, b, tol, niter, tipo_error, lambda a, b, fa, fb: (a + b) / 2.0)


def regla_falsa(f, a, b, tol, niter, tipo_error='abs'):
    return _por_intervalos("Regla Falsa", f, a, b, tol, niter, tipo_error, lambda a, b, fa, fb: b - fb * (b - a) / (fb - fa))


def punto_fijo(f, g, x0, tol, niter, tipo_error='abs'):
    t0 = time.perf_counter()
    res = ResultadoNoLineal("Punto Fijo", '', '', ['i', 'xi', 'g(xi)', 'f(xi)', 'E abs', 'E rel', 'E cond'])
    x = x0
    fx = f(x)
    c = 0
    if not _finito(fx):
        return _diverge(res, x, c, "f(x0)", t0)
    ec = abs(fx)
    ea, er = NAN, NAN
    error = ec if tipo_error == 'cond' else (tol + 1)
    filas_pendientes = [[c, x, None, fx, ea, er, ec]]
    res.puntos.append(x)

    # Verificar derivada de g en x0 para diagnóstico teórico
    try:
        dg_x0 = abs(g.derivada()(x0))
        res.extras['dg_x0'] = _limpio(dg_x0)
        res.extras['converge_teorico'] = bool(_finito(dg_x0) and dg_x0 < 1.0)
    except Exception:
        pass

    while error > tol and fx != 0 and c < niter:
        xn = g(x)
        if not _finito(xn):
            filas_pendientes[-1][2] = xn
            res.filas = filas_pendientes
            return _diverge(res, x, c + 1, "g(x)", t0)
        fx = f(xn)
        if not _finito(fx):
            filas_pendientes[-1][2] = xn
            res.filas = filas_pendientes
            return _diverge(res, xn, c + 1, "f(x)", t0)
        filas_pendientes[-1][2] = xn
        res.pasos_grafica.append({'i': c, 'x': _limpio(x), 'gx': _limpio(xn), 'fx': _limpio(fx)})
        ea, er, ec = _errores(xn, x, fx)
        error = _control(ea, er, ec, tipo_error)
        c += 1
        x = xn
        filas_pendientes.append([c, x, None, fx, ea, er, ec])
        res.puntos.append(x)

    filas_pendientes[-1][2] = g(x)
    res.filas = filas_pendientes
    _fin_iterativo(res, x, c, ea, er, ec, tol, tipo_error, fx, t0)
    # Si g(x) se despejó de f(x), su punto fijo es raíz de f. Si f(x*) está lejos de 0,
    # g(x) no corresponde a f(x) y el "punto fijo" encontrado no sirve como raíz.
    if res.estado == APROXIMACION:
        dfx = abs(f.derivada()(x)) if hasattr(f, 'derivada') else 1.0
        limite = max(1e-2, 100 * tol) * max(1.0, dfx if _finito(dfx) else 1.0)
        if abs(fx) > limite:
            res.estado = INCONSISTENTE
            res.mensaje = (
                f"g(x) converge a x* = {x:.10g}, pero f(x*) = {fx:.6g} ≠ 0: la función g(x) no "
                f"corresponde a f(x), así que x* no es raíz de f. Elige una g(x) obtenida despejando x de f(x) = 0."
            )
    return res


def newton(f, df, x0, tol, niter, tipo_error='abs'):
    t0 = time.perf_counter()
    res = ResultadoNoLineal("Newton-Raphson", '', '', ['i', 'xi', 'f(xi)', "f'(xi)", 'E abs', 'E rel', 'E cond'])
    x = x0
    fx, dfx = f(x), df(x)
    c = 0
    if not _finito(fx, dfx):
        res.filas.append([c, x, fx, dfx, NAN, NAN, NAN])
        return _diverge(res, x, c, "f(x0) o f'(x0)", t0)
    ec = abs(fx)
    ea, er = NAN, NAN
    error = ec if tipo_error == 'cond' else (tol + 1)
    res.filas.append([c, x, fx, dfx, ea, er, ec])
    res.puntos.append(x)

    while error > tol and fx != 0 and dfx != 0 and c < niter:
        xn = x - fx / dfx
        res.pasos_grafica.append({'i': c, 'x': _limpio(x), 'fx': _limpio(fx), 'dfx': _limpio(dfx), 'xn': _limpio(xn)})
        fx, dfx = f(xn), df(xn)
        ea, er, ec = _errores(xn, x, fx)
        error = _control(ea, er, ec, tipo_error)
        c += 1
        x = xn
        res.filas.append([c, x, fx, dfx, ea, er, ec])
        res.puntos.append(x)
        if not _finito(x, fx, dfx):
            return _diverge(res, x, c, "f(x) o f'(x)", t0)

    if fx != 0 and error > tol and dfx == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = DETENIDO, x, fx, c
        res.error_abs, res.error_rel, res.error_cond = ea, er, ec
        res.mensaje = (
            f"La derivada f'(x) se hizo 0 en x = {x:.6g} con f(x) = {fx:.6g}. "
            f"El método no puede dividir por cero (si f(x) ≈ 0 podría ser una raíz múltiple)."
        )
        return res
    return _fin_iterativo(res, x, c, ea, er, ec, tol, tipo_error, fx, t0)


def secante(f, x0, x1, tol, niter, tipo_error='abs'):
    t0 = time.perf_counter()
    res = ResultadoNoLineal("Secante", '', '', ['i', 'xi', 'f(xi)', 'E abs', 'E rel', 'E cond'])
    f0 = f(x0)
    if not _finito(f0):
        res.filas.append([0, x0, f0, NAN, NAN, NAN])
        return _diverge(res, x0, 0, "f(x0)", t0)
    res.filas.append([0, x0, f0, NAN, NAN, abs(f0)])
    res.puntos.append(x0)
    if f0 == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = RAIZ, x0, 0.0, 0
        res.error_abs, res.error_rel, res.error_cond = 0.0, 0.0, 0.0
        res.mensaje = f"{x0:.10g} es raíz exacta de f(x)."
        return res

    f1 = f(x1)
    if not _finito(f1):
        res.filas.append([1, x1, f1, abs(x1 - x0), NAN, NAN])
        return _diverge(res, x1, 1, "f(x1)", t0)
    ea, er, ec = _errores(x1, x0, f1)
    error = _control(ea, er, ec, tipo_error)
    c = 1
    res.filas.append([c, x1, f1, ea, er, ec])
    res.puntos.append(x1)

    while error > tol and f1 != 0 and (f1 - f0) != 0 and c < niter:
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        res.pasos_grafica.append({'i': c, 'x0': _limpio(x0), 'f0': _limpio(f0), 'x1': _limpio(x1), 'f1': _limpio(f1), 'x2': _limpio(x2)})
        f2 = f(x2)
        x0, f0 = x1, f1
        x1, f1 = x2, f2
        ea, er, ec = _errores(x1, x0, f1)
        error = _control(ea, er, ec, tipo_error)
        c += 1
        res.filas.append([c, x1, f1, ea, er, ec])
        res.puntos.append(x1)
        if not _finito(x1, f1):
            return _diverge(res, x1, c, "f(x)", t0)

    if f1 != 0 and error > tol and (f1 - f0) == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = DETENIDO, x1, f1, c
        res.error_abs, res.error_rel, res.error_cond = ea, er, ec
        res.mensaje = f"f(xi) - f(xi-1) = 0 en la iteración {c}: división por cero en la secante."
        return res
    return _fin_iterativo(res, x1, c, ea, er, ec, tol, tipo_error, f1, t0)


def raices_multiples(f, df, d2f, x0, tol, niter, tipo_error='abs', variante=2, m=2):
    """variante 1: x - m*f/f'  |  variante 2: x - f*f' / (f'^2 - f*f'')"""
    t0 = time.perf_counter()
    nombre = f"Raíces Múltiples (m={m})" if variante == 1 else "Raíces Múltiples (con f'')"
    if variante == 1:
        columnas = ['i', 'xi', 'f(xi)', "f'(xi)", 'E abs', 'E rel', 'E cond']
    else:
        columnas = ['i', 'xi', 'f(xi)', "f'(xi)", "f''(xi)", 'E abs', 'E rel', 'E cond']
    res = ResultadoNoLineal(nombre, '', '', columnas)

    def evaluar(v):
        fv, dv = f(v), df(v)
        if variante == 1:
            return fv, dv, None, dv
        d2v = d2f(v)
        den = (dv ** 2 - fv * d2v) if _finito(fv, dv, d2v) else NAN
        return fv, dv, d2v, den

    def armar_fila(i, v, fv, dv, d2v, ea_, er_, ec_):
        if variante == 1:
            return [i, v, fv, dv, ea_, er_, ec_]
        return [i, v, fv, dv, d2v, ea_, er_, ec_]

    x = x0
    fx, dfx, d2fx, den = evaluar(x)
    c = 0
    if not _finito(fx, den):
        res.filas.append(armar_fila(c, x, fx, dfx, d2fx, NAN, NAN, NAN))
        return _diverge(res, x, c, "f(x0) o sus derivadas", t0)
    ec = abs(fx)
    ea, er = NAN, NAN
    error = ec if tipo_error == 'cond' else (tol + 1)
    res.filas.append(armar_fila(c, x, fx, dfx, d2fx, ea, er, ec))
    res.puntos.append(x)

    while error > tol and fx != 0 and den != 0 and c < niter:
        if variante == 1:
            xn = x - m * fx / den
        else:
            xn = x - fx * dfx / den
        res.pasos_grafica.append({'i': c, 'x': _limpio(x), 'fx': _limpio(fx), 'xn': _limpio(xn)})
        fx, dfx, d2fx, den = evaluar(xn)
        ea, er, ec = _errores(xn, x, fx)
        error = _control(ea, er, ec, tipo_error)
        c += 1
        x = xn
        res.filas.append(armar_fila(c, x, fx, dfx, d2fx, ea, er, ec))
        res.puntos.append(x)
        if not _finito(x, fx, den):
            return _diverge(res, x, c, "f(x) o sus derivadas", t0)

    if fx != 0 and error > tol and den == 0:
        res.tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        res.estado, res.valor, res.fx_final, res.iteracion = DETENIDO, x, fx, c
        res.error_abs, res.error_rel, res.error_cond = ea, er, ec
        res.mensaje = f"El denominador se hizo 0 en x = {x:.6g} (iteración {c}): no se puede continuar."
        return res
    return _fin_iterativo(res, x, c, ea, er, ec, tol, tipo_error, fx, t0)


# ---------------------------------------------------- muestreo para gráficas

def _rango_x(intervalo, puntos, raiz):
    if intervalo is not None:
        a, b = sorted(intervalo)
        ancho = (b - a) if b > a else 2.0
        return a - 0.15 * ancho, b + 0.15 * ancho
    finitos = [p for p in puntos if _finito(p)]
    if _finito(raiz):
        finitos.append(raiz)
    if not finitos:
        return -5.0, 5.0
    inicio = finitos[0]
    limite = 80 * (1 + abs(inicio))
    razonables = [p for p in finitos if abs(p - inicio) <= limite] or [inicio]
    lo, hi = min(razonables), max(razonables)
    if hi - lo < 1.5:
        centro = (lo + hi) / 2.0
        lo, hi = centro - 1.5, centro + 1.5
    ancho = hi - lo
    return lo - 0.18 * ancho, hi + 0.18 * ancho


def _cortar_asintotas(ys):
    finitos = ys[np.isfinite(ys)]
    if finitos.size < 4:
        return ys
    p_lo, p_hi = np.percentile(finitos, [2, 98])
    rango = max(p_hi - p_lo, 1.0)
    ys_out = ys.copy()
    with np.errstate(invalid='ignore'):
        fuera = np.abs(ys_out) > (max(abs(p_lo), abs(p_hi)) + 8 * rango)
        ys_out[fuera] = np.nan
        saltos = np.abs(np.diff(ys_out)) > (3.5 * rango)
        ys_out[1:][saltos] = np.nan
    return ys_out


def generar_datos_grafica(f, df=None, d2f=None, g=None, puntos=(), raiz=None, intervalo=None, n_puntos=350):
    """Genera series numéricas limpias (JSON-serializables) para graficar en el frontend."""
    lo, hi = _rango_x(intervalo, puntos, raiz)
    xs = np.linspace(lo, hi, n_puntos)
    ys = _cortar_asintotas(f.evaluar_arreglo(xs))
    dys = _cortar_asintotas(df.evaluar_arreglo(xs)) if df is not None else None
    d2ys = _cortar_asintotas(d2f.evaluar_arreglo(xs)) if d2f is not None else None
    gys = _cortar_asintotas(g.evaluar_arreglo(xs)) if g is not None else None

    serie_curva = []
    for idx in range(len(xs)):
        punto = {
            'x': round(float(xs[idx]), 6),
            'fx': _limpio(ys[idx]),
        }
        if dys is not None:
            punto['dfx'] = _limpio(dys[idx])
        if d2ys is not None:
            punto['d2fx'] = _limpio(d2ys[idx])
        if gys is not None:
            punto['gx'] = _limpio(gys[idx])
            punto['yx'] = round(float(xs[idx]), 6)
        serie_curva.append(punto)

    iteraciones_visibles = []
    for idx, p in enumerate(puntos):
        if _finito(p) and lo <= p <= hi:
            fp = f(p)
            item = {'i': idx, 'x': float(p), 'fx': _limpio(fp)}
            if g is not None:
                item['gx'] = _limpio(g(p))
            iteraciones_visibles.append(item)

    return {
        'rango_x': [round(float(lo), 6), round(float(hi), 6)],
        'curva': serie_curva,
        'iteraciones': iteraciones_visibles,
        'raiz': {'x': _limpio(raiz), 'fx': _limpio(f(raiz))} if _finito(raiz) else None,
    }


def serializar_resultado_no_lineal(res, f, df=None, d2f=None, g=None, intervalo=None):
    """Convierte ResultadoNoLineal a un diccionario JSON completo con tabla, métricas y gráfica."""
    filas_limpias = [
        [celda if isinstance(celda, (int, str)) else _limpio(celda) for celda in fila]
        for fila in res.filas
    ]
    # Serie de convergencia de errores por iteración
    idx_ea = res.columnas.index('E abs') if 'E abs' in res.columnas else None
    idx_er = res.columnas.index('E rel') if 'E rel' in res.columnas else None
    idx_ec = res.columnas.index('E cond') if 'E cond' in res.columnas else None
    idx_x = 2 if 'xm' in res.columnas else 1

    historial_errores = []
    for fila in res.filas:
        it_num = int(fila[0])
        historial_errores.append({
            'iteracion': it_num,
            'x': _limpio(fila[idx_x]),
            'e_abs': _limpio(fila[idx_ea]) if idx_ea is not None else None,
            'e_rel': _limpio(fila[idx_er]) if idx_er is not None else None,
            'e_cond': _limpio(fila[idx_ec]) if idx_ec is not None else None,
        })

    raiz_graf = res.valor if res.estado in (RAIZ, APROXIMACION) else None
    grafica = generar_datos_grafica(
        f, df=df, d2f=d2f, g=g,
        puntos=res.puntos, raiz=raiz_graf, intervalo=intervalo
    )

    return {
        'metodo': res.metodo,
        'estado': res.estado,
        'exito': res.estado in (RAIZ, APROXIMACION, INTERVALO),
        'mensaje': res.mensaje,
        'valor': _limpio(res.valor),
        'fx_final': _limpio(res.fx_final),
        'iteraciones': res.iteracion,
        'error_abs': _limpio(res.error_abs),
        'error_rel': _limpio(res.error_rel),
        'error_cond': _limpio(res.error_cond),
        'tiempo_ms': res.tiempo_ms,
        'columnas': res.columnas,
        'filas': filas_limpias,
        'historial_errores': historial_errores,
        'pasos_grafica': res.pasos_grafica,
        'grafica': grafica,
        'extras': res.extras,
    }

