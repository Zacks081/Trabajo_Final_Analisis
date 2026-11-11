"""Módulo de comparación multimétodo y generación automática de informes para los 3 capítulos."""
import math
import numpy as np

from . import interpolacion as it
from . import no_lineales as nl
from . import sistemas as si
from .funciones import Funcion, analizar_funcion, interpretar_numero


def _limpio(v):
    if v is None:
        return None
    try:
        vf = float(v)
        return vf if math.isfinite(vf) else None
    except Exception:
        return None


CRITERIOS = ('abs', 'rel', 'cond')
NOMBRES_CRITERIO = {'abs': 'error absoluto', 'rel': 'error relativo', 'cond': 'error de condición'}


def _ganador(resumenes):
    """Método que convergió con menos iteraciones (None si ninguno convergió)."""
    conv = [r for r in resumenes if r['convergio'] and r['iteraciones_usadas'] is not None]
    return min(conv, key=lambda r: r['iteraciones_usadas']) if conv else None


def _frase_ganadores(ganadores):
    partes = []
    for crit in CRITERIOS:
        g = ganadores.get(crit)
        if g:
            partes.append(f"con {NOMBRES_CRITERIO[crit]} ganó {g['metodo']} ({g['iteraciones_usadas']} iteraciones)")
        else:
            partes.append(f"con {NOMBRES_CRITERIO[crit]} ningún método convergió")
    return "Comparando los tres criterios de parada: " + "; ".join(partes) + "."


# ============================================================ CAPÍTULO 1

def _resumen_nl(r, criterio):
    cols = r.columnas
    ia, ir, ic = cols.index('E abs'), cols.index('E rel'), cols.index('E cond')
    finales = {'abs': r.error_abs, 'rel': r.error_rel, 'cond': r.error_cond}
    return {
        'metodo': r.metodo,
        'estado': r.estado,
        'convergio': r.estado in (nl.RAIZ, nl.APROXIMACION),
        'mensaje': r.mensaje,
        'iteraciones_usadas': r.iteracion,
        'raiz': _limpio(r.valor),
        'error_abs': _limpio(r.error_abs),
        'error_rel': _limpio(r.error_rel),
        'error_cond': _limpio(r.error_cond),
        'error_final': _limpio(finales[criterio]),
        'historia': [
            {'iteracion': int(f[0]), 'error_abs': _limpio(f[ia]), 'error_rel': _limpio(f[ir]), 'error_cond': _limpio(f[ic])}
            for f in r.filas
        ],
    }


def comparar_capitulo_1(f_texto, a, b, x0, x1=None, g_texto=None, df_texto=None, d2f_texto=None,
                        m=2, tol=1e-7, niter=100, tipo_error='abs'):
    """Ejecuta todos los métodos del Capítulo 1 ante los 3 tipos de error y genera gráfica + informe."""
    f = Funcion.desde_texto(f_texto)
    df = Funcion.desde_texto(df_texto) if (df_texto and str(df_texto).strip()) else f.derivada()
    d2f = Funcion.desde_texto(d2f_texto) if (d2f_texto and str(d2f_texto).strip()) else df.derivada()

    a_val = interpretar_numero(a)
    b_val = interpretar_numero(b)
    if b_val <= a_val:
        raise ValueError("El extremo derecho b debe ser estrictamente mayor que el extremo izquierdo a.")
    x0_val = interpretar_numero(x0)
    x1_val = interpretar_numero(x1) if (x1 is not None and str(x1).strip() != '') else (x0_val + 0.5)
    if x1_val == x0_val:
        x1_val = x0_val + 0.5

    # Si el usuario no especificó g(x), elegir la mejor sugerencia automática
    if g_texto and str(g_texto).strip():
        g = Funcion.desde_texto(g_texto)
    else:
        info_f = analizar_funcion(f_texto, x0=x0_val)
        elegida = None
        for sug in info_f['sugerencias_g']:
            if sug.get('converge_local'):
                elegida = sug['texto']
                break
        if not elegida and info_f['sugerencias_g']:
            elegida = info_f['sugerencias_g'][0]['texto']
        g = Funcion.desde_texto(elegida if elegida else f"x - ({f.texto})")

    def _correr_todos(criterio):
        return [
            nl.biseccion(f, a_val, b_val, tol, niter, criterio),
            nl.regla_falsa(f, a_val, b_val, tol, niter, criterio),
            nl.punto_fijo(f, g, x0_val, tol, niter, criterio),
            nl.newton(f, df, x0_val, tol, niter, criterio),
            nl.secante(f, x0_val, x1_val, tol, niter, criterio),
            nl.raices_multiples(f, df, d2f, x0_val, tol, niter, criterio, variante=1, m=int(m)),
            nl.raices_multiples(f, df, d2f, x0_val, tol, niter, criterio, variante=2, m=int(m)),
        ]

    if tipo_error not in CRITERIOS:
        tipo_error = 'abs'
    por_criterio = {crit: _correr_todos(crit) for crit in CRITERIOS}
    resultados_actual = por_criterio[tipo_error]
    resumen_criterios = {crit: [_resumen_nl(r, crit) for r in por_criterio[crit]] for crit in CRITERIOS}
    ganadores = {crit: _ganador(resumen_criterios[crit]) for crit in CRITERIOS}

    # Tabla resumen del criterio seleccionado
    tabla_comparativa = []
    max_iter_obs = 0
    for r in resultados_actual:
        exito = r.estado in (nl.RAIZ, nl.APROXIMACION)
        if r.iteracion is not None:
            max_iter_obs = max(max_iter_obs, r.iteracion)
        tabla_comparativa.append({
            'metodo': r.metodo,
            'estado': r.estado,
            'exito': exito,
            'raiz': _limpio(r.valor),
            'iteraciones': r.iteracion,
            'error_abs': _limpio(r.error_abs),
            'error_rel': _limpio(r.error_rel),
            'error_cond': _limpio(r.error_cond),
            'tiempo_ms': r.tiempo_ms,
            'mensaje': r.mensaje,
        })

    # Matriz cruzada ante los 3 tipos de error (Absoluto, Relativo, Condición)
    matriz_errores = []
    for idx_m, r_base in enumerate(resultados_actual):
        r_abs = por_criterio['abs'][idx_m]
        r_rel = por_criterio['rel'][idx_m]
        r_cond = por_criterio['cond'][idx_m]
        matriz_errores.append({
            'metodo': r_base.metodo,
            'abs': {
                'iteraciones': r_abs.iteracion,
                'raiz': _limpio(r_abs.valor),
                'error_final': _limpio(r_abs.error_abs),
                'exito': r_abs.estado in (nl.RAIZ, nl.APROXIMACION),
                'estado': r_abs.estado,
            },
            'rel': {
                'iteraciones': r_rel.iteracion,
                'raiz': _limpio(r_rel.valor),
                'error_final': _limpio(r_rel.error_rel),
                'exito': r_rel.estado in (nl.RAIZ, nl.APROXIMACION),
                'estado': r_rel.estado,
            },
            'cond': {
                'iteraciones': r_cond.iteracion,
                'raiz': _limpio(r_cond.valor),
                'error_final': _limpio(r_cond.error_cond),
                'exito': r_cond.estado in (nl.RAIZ, nl.APROXIMACION),
                'estado': r_cond.estado,
            },
        })

    # Series de convergencia (iteración vs error) para la gráfica comparativa
    clave_col_err = {'abs': 'E abs', 'rel': 'E rel', 'cond': 'E cond'}.get(tipo_error, 'E abs')
    series_convergencia = []
    for k in range(max_iter_obs + 1):
        punto_k = {'iteracion': k}
        for r in resultados_actual:
            if k < len(r.filas) and clave_col_err in r.columnas:
                idx_c = r.columnas.index(clave_col_err)
                val_e = _limpio(r.filas[k][idx_c])
                punto_k[r.metodo] = val_e
        series_convergencia.append(punto_k)

    # Redacción del informe automático
    exitosos = [item for item in tabla_comparativa if item['exito'] and item['iteraciones'] is not None]
    fallidos = [item for item in tabla_comparativa if not item['exito']]

    clave_err_item = {'abs': 'error_abs', 'rel': 'error_rel', 'cond': 'error_cond'}.get(tipo_error, 'error_abs')
    ranking = sorted(
        exitosos,
        key=lambda it_: (
            it_['iteraciones'],
            it_[clave_err_item] if it_[clave_err_item] is not None else 1e99,
            it_['tiempo_ms'],
        ),
    )

    conclusiones = []
    if ranking:
        mejor = ranking[0]
        peor = ranking[-1]
        conclusiones.append(
            f"El método más eficiente bajo el criterio seleccionado fue {mejor['metodo']}, "
            f"alcanzando la raíz x ≈ {mejor['raiz']:.10f} en solo {mejor['iteraciones']} iteraciones "
            f"(|f(x)| = {(mejor['error_cond'] or 0):.3e})."
        )
        if len(ranking) > 1 and peor['metodo'] != mejor['metodo']:
            conclusiones.append(
                f"Entre los métodos que convergieron, {peor['metodo']} requirió el mayor esfuerzo con "
                f"{peor['iteraciones']} iteraciones."
            )
    else:
        conclusiones.append(
            "Ninguno de los métodos logró converger con los parámetros ingresados. "
            "Verifica que exista cambio de signo en [a, b] y que x0 esté suficientemente cerca de la raíz."
        )

    if fallidos:
        nombres_fall = ", ".join(f"{it_['metodo']} ({it_['estado']})" for it_ in fallidos)
        conclusiones.append(f"Métodos que no convergieron con esta configuración: {nombres_fall}.")

    conclusiones.append(_frase_ganadores(ganadores))
    conclusiones.append(
        "Comparación por tipo de error: el Error Absoluto |xi - xi-1| mide decimales exactos, "
        "el Error Relativo |xi - xi-1|/|xi| garantiza cifras significativas independientemente de la escala de x, "
        "y el Error de Condición |f(xi)| mide directamente qué tan cerca está la evaluación de anular la función."
    )

    return {
        'funcion_f': {'texto': f.texto, 'latex': f.latex},
        'derivada_1': {'texto': df.texto, 'latex': df.latex},
        'derivada_2': {'texto': d2f.texto, 'latex': d2f.latex},
        'funcion_g_usada': {'texto': g.texto, 'latex': g.latex},
        'tipo_error_activo': tipo_error,
        'tolerancia': tol,
        'tabla_comparativa': tabla_comparativa,
        'matriz_errores': matriz_errores,
        'series_convergencia': series_convergencia,
        'ranking': ranking,
        'por_criterio': resumen_criterios,
        'ganadores_por_criterio': {crit: (g['metodo'] if g else None) for crit, g in ganadores.items()},
        'informe': {
            'mejor_metodo': ranking[0]['metodo'] if ranking else None,
            'raiz_consenso': ranking[0]['raiz'] if ranking else None,
            'conclusiones': conclusiones,
        },
    }


# ============================================================ CAPÍTULO 2

def _resumen_si(r, criterio):
    clave = {'abs': 'error_abs', 'rel': 'error_rel', 'cond': 'error_cond'}[criterio]
    return {
        'metodo': r['metodo'],
        'estado': r['estado'],
        'convergio': r['exito'],
        'mensaje': r.get('mensaje'),
        'radio_espectral': r.get('radio_espectral'),
        'puede_converger': r.get('converge_segun_radio'),
        'iteraciones_usadas': r.get('iteraciones'),
        'error_abs': r.get('error_abs'),
        'error_rel': r.get('error_rel'),
        'error_cond': r.get('error_cond'),
        'error_final': r.get(clave),
        'historia': [
            {'iteracion': h['iteracion'], 'error_abs': h['e_abs'], 'error_rel': h['e_rel'], 'error_cond': h['e_cond']}
            for h in r.get('historial_errores', [])
        ],
    }


def comparar_capitulo_2(A_in, b_in, x0_in=None, tol=1e-7, niter=100, w=1.2,
                        tipo_error='abs', tipo_norma='inf'):
    """Compara Jacobi, Gauss-Seidel y SOR ante los 3 tipos de error (abs, rel, cond)."""
    A = si.parsear_matriz(A_in, max_n=8)
    n = A.shape[0]
    b = si.parsear_vector(b_in, n=n, nombre="b")
    x0 = si.parsear_vector(x0_in, n=n, nombre="x0") if x0_in is not None else np.zeros(n)

    metodos = ['jacobi', 'gauss-seidel', 'sor']

    def _correr_tres(criterio):
        return [
            si.resolver_iterativo(A, b, x0, tol, niter, met, criterio, tipo_norma, w)
            for met in metodos
        ]

    if tipo_error not in CRITERIOS:
        tipo_error = 'abs'
    por_criterio = {crit: _correr_tres(crit) for crit in CRITERIOS}
    actuales = por_criterio[tipo_error]
    resumen_criterios = {crit: [_resumen_si(r, crit) for r in por_criterio[crit]] for crit in CRITERIOS}
    ganadores = {crit: _ganador(resumen_criterios[crit]) for crit in CRITERIOS}
    diag_A = si.diagnosticar_matriz(A, tipo_norma)

    tabla_comparativa = []
    max_iter_obs = 0
    for r in actuales:
        if r.get('iteraciones') is not None:
            max_iter_obs = max(max_iter_obs, r['iteraciones'])
        tabla_comparativa.append({
            'metodo': r['metodo'],
            'codigo': r.get('codigo_metodo'),
            'estado': r['estado'],
            'exito': r['exito'],
            'iteraciones': r.get('iteraciones'),
            'radio_espectral': r.get('radio_espectral'),
            'converge_segun_radio': r.get('converge_segun_radio'),
            'error_abs': r.get('error_abs'),
            'error_rel': r.get('error_rel'),
            'error_cond': r.get('error_cond'),
            'solucion': r.get('solucion'),
            'tiempo_ms': r.get('tiempo_ms'),
            'mensaje': r.get('mensaje'),
        })

    matriz_errores = []
    for idx_m, r_base in enumerate(actuales):
        r_abs = por_criterio['abs'][idx_m]
        r_rel = por_criterio['rel'][idx_m]
        r_cond = por_criterio['cond'][idx_m]
        matriz_errores.append({
            'metodo': r_base['metodo'],
            'radio_espectral': r_base.get('radio_espectral'),
            'converge_segun_radio': r_base.get('converge_segun_radio'),
            'abs': {
                'iteraciones': r_abs.get('iteraciones'),
                'error_final': r_abs.get('error_abs'),
                'exito': r_abs['exito'],
                'estado': r_abs['estado'],
            },
            'rel': {
                'iteraciones': r_rel.get('iteraciones'),
                'error_final': r_rel.get('error_rel'),
                'exito': r_rel['exito'],
                'estado': r_rel['estado'],
            },
            'cond': {
                'iteraciones': r_cond.get('iteraciones'),
                'error_final': r_cond.get('error_cond'),
                'exito': r_cond['exito'],
                'estado': r_cond['estado'],
            },
        })

    clave_hist = {'abs': 'e_abs', 'rel': 'e_rel', 'cond': 'e_cond'}.get(tipo_error, 'e_abs')
    series_convergencia = []
    for k in range(max_iter_obs + 1):
        punto_k = {'iteracion': k}
        for r in actuales:
            hist = r.get('historial_errores', [])
            if k < len(hist):
                punto_k[r['metodo']] = hist[k].get(clave_hist)
        series_convergencia.append(punto_k)

    exitosos = [it_ for it_ in tabla_comparativa if it_['exito'] and it_['iteraciones'] is not None]
    ranking = sorted(
        exitosos,
        key=lambda it_: (
            it_['iteraciones'],
            it_['radio_espectral'] if it_['radio_espectral'] is not None else 999.0,
        ),
    )

    conclusiones = []
    if diag_A['es_edd']:
        conclusiones.append(
            "La matriz A es Estrictamente Diagonalmente Dominante (EDD), lo que garantiza teóricamente "
            "que tanto Jacobi como Gauss-Seidel convergen para cualquier vector inicial x(0)."
        )
    else:
        conclusiones.append(
            "La matriz A NO es estrictamente diagonalmente dominante; la convergencia depende exclusivamente "
            "de que el radio espectral ρ(T) de cada método sea estrictamente menor que 1."
        )

    radios = [it_ for it_ in tabla_comparativa if it_['radio_espectral'] is not None]
    if radios:
        menor_rho = min(radios, key=lambda r_: r_['radio_espectral'])
        conclusiones.append(
            f"El menor radio espectral lo obtuvo {menor_rho['metodo']} con ρ(T) = {menor_rho['radio_espectral']:.6f}. "
            f"Como la tasa asintótica de convergencia depende de ρ(T), un menor radio espectral implica converger en menos iteraciones."
        )

    if ranking:
        mejor = ranking[0]
        conclusiones.append(
            f"El método ganador fue {mejor['metodo']}, convergiendo en {mejor['iteraciones']} iteraciones "
            f"con error absoluto {(mejor['error_abs'] or 0):.3e}, relativo {(mejor['error_rel'] or 0):.3e} "
            f"y residual ||b - Ax|| = {(mejor['error_cond'] or 0):.3e}."
        )

    conclusiones.append(_frase_ganadores(ganadores))

    if diag_A.get('condicion') is not None:
        conclusiones.append(
            f"El número de condición de la matriz es κ(A) = {diag_A['condicion']:.4e} "
            f"({'sistema bien condicionado' if not diag_A['mal_condicionada'] else 'sistema mal condicionado, sensible a perturbaciones'})."
        )

    return {
        'diagnostico_matriz': diag_A,
        'tipo_error_activo': tipo_error,
        'tipo_norma': tipo_norma,
        'tolerancia': tol,
        'tabla_comparativa': tabla_comparativa,
        'matriz_errores': matriz_errores,
        'series_convergencia': series_convergencia,
        'ranking': ranking,
        'por_criterio': resumen_criterios,
        'ganadores_por_criterio': {crit: (g['metodo'] if g else None) for crit, g in ganadores.items()},
        'informe': {
            'mejor_metodo': ranking[0]['metodo'] if ranking else None,
            'solucion_consenso': ranking[0]['solucion'] if ranking else None,
            'conclusiones': conclusiones,
        },
    }


# ============================================================ CAPÍTULO 3

def comparar_capitulo_3(x_in, y_in, porcentaje_reserva=20, indices_reserva=None,
                        x_evaluar=None, funcion_real_texto=None):
    """Compara los 6 métodos de interpolación y evalúa precisión sobre los datos reservados (20% o 30%)."""
    claves = [
        'vandermonde',
        'newton',
        'lagrange',
        'spline_lineal',
        'spline_cuadratico',
        'spline_cubico',
    ]
    x_todos, y_todos = it.parsear_puntos(x_in, y_in, max_puntos=10)
    # Si el usuario dejó 0% en la vista comparativa pero hay >= 4 puntos, también calculamos una reserva
    # de referencia del 20% para que el informe comparativo pueda medir el error predictivo.
    porcentaje_efectivo = porcentaje_reserva
    resultados = [
        it.ejecutar_interpolacion(
            clave, x_todos, y_todos,
            porcentaje_reserva=porcentaje_efectivo,
            indices_reserva=indices_reserva,
            x_evaluar=x_evaluar,
            funcion_real_texto=funcion_real_texto,
        )
        for clave in claves
    ]

    # Construir curva unificada con todos los métodos para superponerlos en una sola gráfica
    lo = float(np.min(x_todos))
    hi = float(np.max(x_todos))
    if x_evaluar is not None and str(x_evaluar).strip() != '':
        t_eval = interpretar_numero(x_evaluar)
        lo = min(lo, t_eval)
        hi = max(hi, t_eval)
    margen = 0.06 * (hi - lo if hi > lo else 2.0)
    xs_grid = np.linspace(lo - margen, hi + margen, 250)

    f_real = Funcion.desde_texto(funcion_real_texto) if (funcion_real_texto and str(funcion_real_texto).strip()) else None
    ys_real = f_real.evaluar_arreglo(xs_grid) if f_real is not None else None

    tabla_comparativa = []
    for clave, r in zip(claves, resultados):
        val_res = r.get('validacion_reserva') or {}
        eval_pto = r.get('evaluacion') or {}
        tabla_comparativa.append({
            'clave': clave,
            'metodo': r['metodo'],
            'exito': r['exito'],
            'polinomio_texto': r.get('polinomio_texto'),
            'polinomio_latex': r.get('polinomio_latex'),
            'tramos': r.get('tramos'),
            'valor_en_x_evaluar': eval_pto.get('y'),
            'error_real_en_x_evaluar': eval_pto.get('error_abs'),
            'error_abs_reserva_promedio': val_res.get('error_abs_promedio'),
            'error_abs_reserva_maximo': val_res.get('error_abs_maximo'),
            'error_rel_reserva_promedio': val_res.get('error_rel_promedio'),
            'tiempo_ms': r.get('tiempo_ms'),
        })

    # Unificar curvas tomadas de cada resultado (todas usan el mismo rango y 300 puntos)
    curva_comparativa = []
    if resultados and resultados[0].get('grafica'):
        base_curva = resultados[0]['grafica']['curva']
        for idx_p, p_base in enumerate(base_curva):
            fila_c = {'x': p_base['x']}
            if 'y_real' in p_base:
                fila_c['f(x) real'] = p_base['y_real']
            for r in resultados:
                if r.get('grafica') and idx_p < len(r['grafica']['curva']):
                    fila_c[r['metodo']] = r['grafica']['curva'][idx_p]['y']
            curva_comparativa.append(fila_c)

    conclusiones = [
        "Por el Teorema de Existencia y Unicidad del polinomio interpolante, Vandermonde, Newton y Lagrange "
        "generan exactamente el mismo polinomio algebraico de grado ≤ n-1 (salvo pequeñas diferencias de redondeo).",
        "Los Trazadores (Splines) evitan las oscilaciones de grados altos (fenómeno de Runge) ajustando polinomios "
        "por tramos con continuidad en los nodos interiores; el Spline Cúbico Natural asegura además continuidad en primera y segunda derivada."
    ]

    con_error_reserva = [t for t in tabla_comparativa if t['error_abs_reserva_promedio'] is not None]
    mejor_metodo = None
    if con_error_reserva:
        mejor = min(con_error_reserva, key=lambda t_: t_['error_abs_reserva_promedio'])
        mejor_metodo = mejor['metodo']
        conclusiones.append(
            f"Al evaluar sobre el conjunto de datos almacenados ({resultados[0]['validacion_reserva']['porcentaje']}% reservado), "
            f"el menor error promedio de predicción lo obtuvo {mejor['metodo']} "
            f"(Error abs promedio = {mejor['error_abs_reserva_promedio']:.4e})."
        )

    return {
        'tabla_comparativa': tabla_comparativa,
        'nodos_usados': resultados[0].get('nodos_usados', []) if resultados else [],
        'datos_almacenados': resultados[0].get('datos_almacenados', []) if resultados else [],
        'validacion_detalle': [
            {'metodo': r['metodo'], 'validacion': r.get('validacion_reserva')}
            for r in resultados if r.get('validacion_reserva')
        ],
        'curva_comparativa': curva_comparativa,
        'informe': {
            'mejor_metodo': mejor_metodo,
            'conclusiones': conclusiones,
        },
    }
