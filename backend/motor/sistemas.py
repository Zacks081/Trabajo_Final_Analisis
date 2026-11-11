"""Métodos para sistemas de ecuaciones lineales Ax = b (Capítulo 2).

Incluye:
- Métodos iterativos: Jacobi, Gauss-Seidel y SOR (relajación)
- Métodos directos: Eliminación Gaussiana (simple, pivoteo parcial, pivoteo total) y
  Factorizaciones LU (simple, pivoteo parcial PA=LU, Doolittle, Crout, Cholesky)
- Soporte de matrices hasta 8x8
- Tres tipos de error de parada/comparación:
  * 'abs'  : Error absoluto de dispersión ||x(k) - x(k-1)||
  * 'rel'  : Error relativo ||x(k) - x(k-1)|| / ||x(k)||
  * 'cond' : Error de condición / residual ||b - A x(k)||
- Normas vectoriales/matriciales: 'inf', '1', '2'
"""
import math
import re
import time
from dataclasses import dataclass, field

import numpy as np

from .funciones import interpretar_numero

NAN = float('nan')

EXITO = 'exito'
APROXIMACION = 'aproximacion'
FRACASO = 'fracaso'
DIVERGE = 'diverge'
ERROR = 'error'


def _limpio_escalar(v):
    if v is None:
        return None
    if isinstance(v, (complex, np.complexfloating)):
        re_v = 0.0 if abs(v.real) < 1e-14 else float(v.real)
        im_v = 0.0 if abs(v.imag) < 1e-14 else float(v.imag)
        if im_v == 0.0:
            return re_v if math.isfinite(re_v) else None
        return f"{re_v:.6f}{im_v:+.6f}i"
    try:
        vf = float(v)
        if not math.isfinite(vf):
            return None
        return 0.0 if abs(vf) < 1e-14 else vf
    except Exception:
        return str(v)


def _limpio_arreglo(arr):
    arr = np.asarray(arr)
    if arr.ndim == 1:
        return [_limpio_escalar(x) for x in arr]
    return [[_limpio_escalar(x) for x in fila] for fila in arr]


def _orden_norma(tipo_norma):
    if str(tipo_norma) == '1':
        return 1
    if str(tipo_norma) == '2':
        return 2
    return np.inf


def calcular_norma(v, tipo_norma='inf'):
    return float(np.linalg.norm(v, _orden_norma(tipo_norma)))


def _elemento(valor, etiqueta):
    """Lee un número indicando en el error cuál elemento está mal (ej. 'a₂₃' o 'b₁')."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ValueError(f"El elemento {etiqueta} está vacío.")
    try:
        return interpretar_numero(valor)
    except ValueError:
        raise ValueError(f"El elemento {etiqueta} = '{valor}' no es un número válido.")


def parsear_matriz(entrada, max_n=8):
    """Acepta una lista 2D de números/textos o un string estilo MATLAB/CSV ('2,1,-1; 0,1,1; 1,0,1')."""
    if entrada is None or (isinstance(entrada, str) and not entrada.strip()):
        raise ValueError("Falta la matriz A.")
    if isinstance(entrada, (list, tuple, np.ndarray)):
        filas = [[_elemento(celda, f"a{i+1},{j+1}") for j, celda in enumerate(fila)]
                 for i, fila in enumerate(entrada)]
    elif isinstance(entrada, str):
        texto = re.sub(r'^\s*[a-zA-Z]\w*\s*=', '', entrada).strip()
        if texto.startswith('[') and texto.endswith(']'):
            texto = texto[1:-1]
        elif '[' in texto or ']' in texto:
            raise ValueError("Los corchetes de la matriz no están bien cerrados.")
        partes = [f.strip() for f in re.split(r'[;\n]+', texto) if f.strip()]
        if not partes:
            raise ValueError("La matriz A está vacía.")
        filas = [[_elemento(e, f"a{i+1},{j+1}") for j, e in enumerate(x for x in re.split(r'[\s,]+', f) if x)]
                 for i, f in enumerate(partes)]
    else:
        raise ValueError("Formato de matriz no reconocido.")

    n = len(filas)
    if n < 2:
        raise ValueError("La matriz A debe ser de tamaño al menos 2×2.")
    if n > max_n:
        raise ValueError(f"El tamaño máximo permitido para la matriz A es {max_n}×{max_n} (ingresaste {n}×{n}).")
    for idx, fila in enumerate(filas, start=1):
        if len(fila) != n:
            raise ValueError(f"La matriz A debe ser cuadrada: hay {n} filas, pero la fila {idx} tiene {len(fila)} elementos.")
    return np.array(filas, dtype=float)


def parsear_vector(entrada, n=None, nombre="b"):
    """Acepta una lista 1D o un string ('1, 2, 3' o '[1 2 3]' o '1; 2; 3')."""
    if entrada is None:
        raise ValueError(f"Falta el vector {nombre}.")
    if isinstance(entrada, (list, tuple, np.ndarray)):
        plano = list(np.asarray(entrada, dtype=object).flatten())
        valores = [_elemento(v, f"{nombre}{i+1}") for i, v in enumerate(plano)]
    elif isinstance(entrada, str):
        texto = re.sub(r'^\s*[a-zA-Z]\w*\s*=', '', entrada).strip()
        if texto.startswith('[') and texto.endswith(']'):
            texto = texto[1:-1]
        valores = [_elemento(e, f"{nombre}{i+1}") for i, e in enumerate(x for x in re.split(r'[\s,;]+', texto) if x)]
    else:
        raise ValueError(f"Formato del vector {nombre} no reconocido.")

    if not valores:
        raise ValueError(f"El vector {nombre} está vacío.")
    if n is not None and len(valores) != n:
        raise ValueError(f"El vector {nombre} debe tener {n} elementos (tiene {len(valores)}).")
    return np.array(valores, dtype=float)


def diagnosticar_matriz(A, tipo_norma='inf'):
    """Analiza dominancia diagonal fila por fila, simetría, determinante y número de condición."""
    A = np.asarray(A, dtype=float)
    n = A.shape[0]
    filas_edd = []
    es_edd = True
    for i in range(n):
        diag = abs(A[i, i])
        suma_resto = float(np.sum(np.abs(A[i, :])) - diag)
        cumple = diag > suma_resto
        if not cumple:
            es_edd = False
        filas_edd.append({
            'fila': i + 1,
            'diagonal': round(float(diag), 6),
            'suma_resto': round(suma_resto, 6),
            'cumple': bool(cumple),
        })

    try:
        det = float(np.linalg.det(A))
    except Exception:
        det = NAN

    try:
        cond = float(np.linalg.cond(A, _orden_norma(tipo_norma)))
    except Exception:
        cond = NAN

    simetrica = bool(np.allclose(A, A.T))
    try:
        autovalores_sim = np.linalg.eigvalsh(A) if simetrica else []
        def_positiva = bool(simetrica and np.all(autovalores_sim > 0))
    except Exception:
        def_positiva = False

    return {
        'dimension': n,
        'es_edd': es_edd,
        'detalle_edd': filas_edd,
        'determinante': _limpio_escalar(det),
        'condicion': _limpio_escalar(cond),
        'mal_condicionada': bool(math.isfinite(cond) and cond > 1e4),
        'simetrica': simetrica,
        'definida_positiva': def_positiva,
    }


def error_residuo(A, b, x, tipo_norma='inf'):
    r = b - A @ x
    if np.iscomplexobj(r) and np.allclose(np.imag(r), 0):
        r = np.real(r)
    orden = _orden_norma(tipo_norma)
    norma_r = float(np.linalg.norm(r, orden))
    norma_b = float(np.linalg.norm(b, orden))
    relativo = norma_r / norma_b if norma_b != 0 else NAN
    try:
        cond = float(np.linalg.cond(A, orden))
    except Exception:
        cond = NAN
    return {
        'residuo_vector': _limpio_arreglo(r),
        'error_cond': _limpio_escalar(norma_r),
        'error_rel_residuo': _limpio_escalar(relativo),
        'numero_condicion': _limpio_escalar(cond),
    }


# --------------------------------------------------------------- iterativos

def matrices_iteracion(A, b, metodo, w=1.0):
    """Calcula D, L, U, T y C de x(k) = T x(k-1) + C para 'jacobi', 'gauss-seidel' o 'sor'."""
    D = np.diag(np.diag(A))
    L = -np.tril(A, -1)
    U = -np.triu(A, +1)
    if metodo == 'jacobi':
        inv_D = np.linalg.inv(D)
        T = inv_D @ (L + U)
        C = inv_D @ b
    elif metodo == 'gauss-seidel':
        inv_DL = np.linalg.inv(D - L)
        T = inv_DL @ U
        C = inv_DL @ b
    else:
        inv_DWL = np.linalg.inv(D - w * L)
        T = inv_DWL @ ((1.0 - w) * D + w * U)
        C = w * inv_DWL @ b
    return D, L, U, T, C


def _paso_jacobi_seidel(x0, A, b, gauss_seidel):
    n = A.shape[0]
    x1 = x0.copy()
    for i in range(n):
        suma = 0.0
        for j in range(n):
            if j != i and not gauss_seidel:
                suma += A[i, j] * x0[j]
            elif j != i and gauss_seidel:
                suma += A[i, j] * x1[j]
        x1[i] = (b[i] - suma) / A[i, i]
    return x1


def resolver_iterativo(A, b, x0=None, tol=1e-7, niter=100, metodo='jacobi',
                       tipo_error='abs', tipo_norma='inf', w=1.0):
    """Ejecuta Jacobi, Gauss-Seidel o SOR y devuelve toda la información teórica y numérica."""
    t0 = time.perf_counter()
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    n = A.shape[0]
    if x0 is None:
        x0 = np.zeros(n, dtype=float)
    else:
        x0 = np.array(x0, dtype=float).flatten()

    nombres_metodo = {
        'jacobi': 'Jacobi',
        'gauss-seidel': 'Gauss-Seidel',
        'sor': f'SOR (ω = {w:g})',
    }
    nombre_mostrar = nombres_metodo.get(metodo, metodo)
    columnas = ['k'] + [f'x{j+1}' for j in range(n)] + ['E abs', 'E rel', 'E cond']

    ceros = [i + 1 for i in range(n) if A[i, i] == 0]
    diag_info = diagnosticar_matriz(A, tipo_norma)
    if ceros:
        return {
            'metodo': nombre_mostrar,
            'estado': ERROR,
            'exito': False,
            'mensaje': (
                f"La diagonal principal de A tiene ceros en las posiciones {ceros}. "
                f"Reordena las ecuaciones (filas) antes de aplicar {nombre_mostrar}."
            ),
            'columnas': columnas,
            'filas': [],
            'diagnostico_matriz': diag_info,
        }

    if metodo == 'sor' and w == 0:
        return {
            'metodo': nombre_mostrar,
            'estado': ERROR,
            'exito': False,
            'mensaje': "El factor de relajación ω no puede ser 0.",
            'columnas': columnas,
            'filas': [],
            'diagnostico_matriz': diag_info,
        }

    D, L, U, T, C = matrices_iteracion(A, b, metodo, w)
    autovalores = np.linalg.eigvals(T)
    rho = float(max(abs(autovalores)))
    converge_radio = bool(rho < 1.0)
    nombre_T = "Tw" if metodo == 'sor' else "T"
    nombre_C = "Cw" if metodo == 'sor' else "C"

    avisos = []
    if not diag_info['es_edd']:
        avisos.append(
            "La matriz A NO es estrictamente diagonalmente dominante (EDD); "
            "el criterio suficiente de dominancia diagonal no garantiza la convergencia."
        )
    if converge_radio:
        veredicto = (
            f"El radio espectral es ρ({nombre_T}) = {rho:.6f} < 1: "
            f"el método CONVERGE a la solución única para cualquier vector inicial x(0)."
        )
    else:
        veredicto = (
            f"El radio espectral es ρ({nombre_T}) = {rho:.6f} ≥ 1: "
            f"el método NO converge en general."
        )
        avisos.append(veredicto + " Se muestran las iteraciones para analizar su comportamiento.")

    if metodo == 'sor' and not (0 < w < 2):
        avisos.append(f"Con ω = {w:g} fuera del intervalo abierto (0, 2), el teorema de Ostrowski-Reich indica que SOR no converge.")

    orden = _orden_norma(tipo_norma)
    r0 = float(np.linalg.norm(b - A @ x0, orden))
    filas = [[0] + [_limpio_escalar(v) for v in x0] + [None, None, _limpio_escalar(r0)]]
    historial_errores = [{
        'iteracion': 0,
        'e_abs': None,
        'e_rel': None,
        'e_cond': _limpio_escalar(r0),
        'x': _limpio_arreglo(x0),
    }]

    c = 0
    ea, er, ec = NAN, NAN, r0
    error = ec if tipo_error == 'cond' else (tol + 1)
    x_actual = x0.copy()
    estado = FRACASO

    while error > tol and c < niter:
        with np.errstate(all='ignore'):
            if metodo == 'sor':
                x_nuevo = T @ x_actual + C
            else:
                x_nuevo = _paso_jacobi_seidel(x_actual, A, b, metodo == 'gauss-seidel')
            ea = float(np.linalg.norm(x_nuevo - x_actual, orden))
            norma_x = float(np.linalg.norm(x_nuevo, orden))
            er = ea / norma_x if norma_x != 0 else NAN
            ec = float(np.linalg.norm(b - A @ x_nuevo, orden))

        if tipo_error == 'rel':
            error = er if math.isfinite(er) else math.inf
        elif tipo_error == 'cond':
            error = ec if math.isfinite(ec) else math.inf
        else:
            error = ea if math.isfinite(ea) else math.inf

        x_actual = x_nuevo
        c += 1
        filas.append([c] + [_limpio_escalar(v) for v in x_actual] + [_limpio_escalar(ea), _limpio_escalar(er), _limpio_escalar(ec)])
        historial_errores.append({
            'iteracion': c,
            'e_abs': _limpio_escalar(ea),
            'e_rel': _limpio_escalar(er),
            'e_cond': _limpio_escalar(ec),
            'x': _limpio_arreglo(x_actual),
        })

        if not np.all(np.isfinite(x_actual)):
            estado = DIVERGE
            break

    tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    etiqueta_err = {
        'abs': 'error absoluto',
        'rel': 'error relativo',
        'cond': 'error de condición ||b - Ax||',
    }.get(tipo_error, 'error absoluto')

    if estado == DIVERGE:
        mensaje = f"El método diverge: en la iteración {c} las componentes crecieron sin límite."
    elif error <= tol:
        estado = APROXIMACION
        mensaje = f"Convergencia alcanzada en {c} iteraciones con {etiqueta_err} {error:.3e} ≤ Tol ({tol:g})."
    else:
        estado = FRACASO
        mensaje = f"Fracasó en {c} iteraciones (el {etiqueta_err} sigue en {error:.3e} > Tol = {tol:g})."

    residuo_final = error_residuo(A, b, x_actual, tipo_norma) if np.all(np.isfinite(x_actual)) else {}

    return {
        'metodo': nombre_mostrar,
        'codigo_metodo': metodo,
        'estado': estado,
        'exito': estado in (APROXIMACION, EXITO),
        'mensaje': mensaje,
        'avisos': avisos,
        'solucion': _limpio_arreglo(x_actual),
        'iteraciones': c,
        'error_abs': _limpio_escalar(ea),
        'error_rel': _limpio_escalar(er),
        'error_cond': _limpio_escalar(ec),
        'radio_espectral': _limpio_escalar(rho),
        'converge_segun_radio': converge_radio,
        'veredicto_convergencia': veredicto,
        'autovalores_T': [_limpio_escalar(ev) for ev in autovalores],
        'matrices': {
            'D': _limpio_arreglo(D),
            'L': _limpio_arreglo(L),
            'U': _limpio_arreglo(U),
            nombre_T: _limpio_arreglo(T),
            nombre_C: _limpio_arreglo(C),
        },
        'diagnostico_matriz': diag_info,
        'residuo': residuo_final,
        'columnas': columnas,
        'filas': filas,
        'historial_errores': historial_errores,
        'tiempo_ms': tiempo_ms,
    }


# ----------------------------------------------------------------- directos

class _PivoteCero(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


def sustitucion_regresiva(Ab, n):
    x = np.zeros(n, dtype=np.result_type(Ab, float))
    x[n - 1] = Ab[n - 1, n] / Ab[n - 1, n - 1]
    for i in range(n - 2, -1, -1):
        suma = 0
        for p in range(i + 1, n):
            suma += Ab[i, p] * x[p]
        x[i] = (Ab[i, n] - suma) / Ab[i, i]
    return x


def sustitucion_progresiva(Ab, n):
    x = np.zeros(n, dtype=np.result_type(Ab, float))
    x[0] = Ab[0, n] / Ab[0, 0]
    for i in range(1, n):
        suma = 0
        for p in range(0, i):
            suma += Ab[i, p] * x[p]
        x[i] = (Ab[i, n] - suma) / Ab[i, i]
    return x


def _pivoteo_parcial(M, n, k, P=None):
    mayor = abs(M[k, k])
    maxrow = k
    for s in range(k + 1, n):
        if abs(M[s, k]) > mayor:
            mayor = abs(M[s, k])
            maxrow = s
    if mayor == 0:
        raise _PivoteCero(
            f"El sistema no tiene solución única: en la etapa {k+1} toda la columna {k+1} "
            f"(desde la fila {k+1}) es cero."
        )
    detalle = f"Sin intercambio en etapa {k+1}"
    if maxrow != k:
        M[[k, maxrow], :] = M[[maxrow, k], :]
        if P is not None:
            P[[k, maxrow], :] = P[[maxrow, k], :]
        detalle = f"Intercambio de filas: F{k+1} ↔ F{maxrow+1}"
    return detalle


def _pivoteo_total(Ab, mark, n, k):
    mayor = 0.0
    maxrow = k
    maxcol = k
    for r in range(k, n):
        for s in range(k, n):
            if abs(Ab[r, s]) > mayor:
                mayor = abs(Ab[r, s])
                maxrow = r
                maxcol = s
    if mayor == 0:
        raise _PivoteCero(f"El sistema no tiene solución única: en la etapa {k+1} la submatriz restante es cero.")
    cambios = []
    if maxrow != k:
        Ab[[k, maxrow], :] = Ab[[maxrow, k], :]
        cambios.append(f"F{k+1} ↔ F{maxrow+1}")
    if maxcol != k:
        Ab[:, [k, maxcol]] = Ab[:, [maxcol, k]]
        mark[[k, maxcol]] = mark[[maxcol, k]]
        cambios.append(f"C{k+1} ↔ C{maxcol+1}")
    return " | ".join(cambios) if cambios else f"Sin intercambio en etapa {k+1}"


def _revisar_pivote(valor, k, con_pivoteo):
    if abs(valor) == 0:
        if con_pivoteo:
            raise _PivoteCero(f"El sistema no tiene solución única: el pivote de la etapa {k+1} es 0.")
        raise _PivoteCero(
            f"Pivote cero en la etapa {k+1} (a{k+1}{k+1} = 0): no se puede dividir por cero. "
            f"Utiliza Eliminación Gaussiana con pivoteo parcial o total."
        )


def gauss(A, b, pivoteo=0, tipo_norma='inf'):
    t0 = time.perf_counter()
    nombres = {
        0: "Eliminación Gaussiana Simple",
        1: "Eliminación Gaussiana con Pivoteo Parcial",
        2: "Eliminación Gaussiana con Pivoteo Total",
    }
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    n = A.shape[0]
    Ab = np.column_stack((A, b))
    mark = np.arange(n)
    etapas = [{
        'etapa': 0,
        'descripcion': 'Matriz aumentada inicial [A | b]',
        'matriz': _limpio_arreglo(Ab),
        'orden_variables': [int(i + 1) for i in mark],
    }]
    try:
        for k in range(n - 1):
            info_piv = f"Etapa {k+1}"
            if pivoteo == 1:
                info_piv = _pivoteo_parcial(Ab, n, k)
            elif pivoteo == 2:
                info_piv = _pivoteo_total(Ab, mark, n, k)
            _revisar_pivote(Ab[k, k], k, pivoteo != 0)
            for i in range(k + 1, n):
                M = Ab[i, k] / Ab[k, k]
                for j in range(k, n + 1):
                    Ab[i, j] = Ab[i, j] - M * Ab[k, j]
            etapas.append({
                'etapa': k + 1,
                'descripcion': info_piv,
                'matriz': _limpio_arreglo(Ab),
                'orden_variables': [int(i + 1) for i in mark],
            })
        _revisar_pivote(Ab[n - 1, n - 1], n - 1, pivoteo != 0)
    except _PivoteCero as e:
        return {
            'metodo': nombres.get(pivoteo, "Gauss"),
            'estado': ERROR,
            'exito': False,
            'mensaje': e.mensaje,
            'etapas': etapas,
            'diagnostico_matriz': diagnosticar_matriz(A, tipo_norma),
        }

    y = sustitucion_regresiva(Ab, n)
    x = np.zeros(n)
    x[mark] = y
    tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res_info = error_residuo(A, b, x, tipo_norma)

    matrices = {'Matriz aumentada final [U | b\']': _limpio_arreglo(Ab)}
    if pivoteo == 2:
        matrices['Orden final de variables (mark)'] = [int(i + 1) for i in mark]

    return {
        'metodo': nombres.get(pivoteo, "Gauss"),
        'estado': EXITO,
        'exito': True,
        'mensaje': "Sistema resuelto exitosamente mediante eliminación gaussiana y sustitución regresiva.",
        'solucion': _limpio_arreglo(x),
        'matrices': matrices,
        'etapas': etapas,
        'residuo': res_info,
        'error_cond': res_info.get('error_cond'),
        'diagnostico_matriz': diagnosticar_matriz(A, tipo_norma),
        'tiempo_ms': tiempo_ms,
    }


def lu(A, b, pivoteo=0, tipo_norma='inf'):
    t0 = time.perf_counter()
    nombre = "Factorización LU con Pivoteo Parcial (PA = LU)" if pivoteo == 1 else "Factorización LU Simple"
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    A_orig = A.copy()
    n = A.shape[0]
    P = np.eye(n)
    L = np.eye(n)
    etapas = []
    try:
        for k in range(n - 1):
            info_piv = f"Etapa {k+1}"
            if pivoteo == 1:
                info_piv = _pivoteo_parcial(A, n, k, P)
            _revisar_pivote(A[k, k], k, pivoteo != 0)
            for i in range(k + 1, n):
                M = A[i, k] / A[k, k]
                for j in range(k, n):
                    A[i, j] = A[i, j] - M * A[k, j]
                A[i, k] = M
            etapas.append({
                'etapa': k + 1,
                'descripcion': info_piv,
                'L': _limpio_arreglo(np.eye(n) + np.tril(A, -1)),
                'U': _limpio_arreglo(np.triu(A)),
                'P': _limpio_arreglo(P) if pivoteo == 1 else None,
            })
        _revisar_pivote(A[n - 1, n - 1], n - 1, pivoteo != 0)
    except _PivoteCero as e:
        return {
            'metodo': nombre,
            'estado': ERROR,
            'exito': False,
            'mensaje': e.mensaje,
            'etapas': etapas,
            'diagnostico_matriz': diagnosticar_matriz(A_orig, tipo_norma),
        }

    U = np.triu(A)
    L = L + np.tril(A, -1)
    B = P @ b
    z = sustitucion_progresiva(np.column_stack((L, B)), n)
    x = sustitucion_regresiva(np.column_stack((U, z)), n)
    tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res_info = error_residuo(A_orig, b, x, tipo_norma)

    matrices = {}
    if pivoteo == 1:
        matrices['P'] = _limpio_arreglo(P)
    matrices['L'] = _limpio_arreglo(L)
    matrices['U'] = _limpio_arreglo(U)
    if pivoteo == 1:
        matrices['Pb'] = _limpio_arreglo(B)
    matrices['z (Lz = Pb)' if pivoteo == 1 else 'z (Lz = b)'] = _limpio_arreglo(z)

    return {
        'metodo': nombre,
        'estado': EXITO,
        'exito': True,
        'mensaje': "Sistema resuelto exitosamente mediante factorización LU.",
        'solucion': _limpio_arreglo(x),
        'matrices': matrices,
        'etapas': etapas,
        'residuo': res_info,
        'error_cond': res_info.get('error_cond'),
        'diagnostico_matriz': diagnosticar_matriz(A_orig, tipo_norma),
        'tiempo_ms': tiempo_ms,
    }


def factorizacion_directa(A, b, metodo=0, tipo_norma='inf'):
    """metodo: 0 = Doolittle, 1 = Crout, 2 = Cholesky."""
    t0 = time.perf_counter()
    nombres = {0: "Factorización Directa: Doolittle", 1: "Factorización Directa: Crout", 2: "Factorización Directa: Cholesky"}
    nombre = nombres.get(metodo, "Factorización Directa")
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float).flatten()
    n = A.shape[0]
    U = np.eye(n)
    L = np.eye(n)
    avisos = []
    etapas = []

    for k in range(n):
        suma1 = sum(L[k, p] * U[p, k] for p in range(k))
        if metodo == 0:
            U[k, k] = (A[k, k] - suma1) / L[k, k]
        elif metodo == 1:
            L[k, k] = (A[k, k] - suma1) / U[k, k]
        else:
            raiz = np.emath.sqrt(A[k, k] - suma1)
            if np.iscomplexobj(raiz) and not np.iscomplexobj(U):
                L = L.astype(complex)
                U = U.astype(complex)
                avisos.append(
                    f"En la etapa {k+1} apareció la raíz cuadrada de un número negativo: "
                    f"la matriz A no es definida positiva, por lo que L y U contienen números complejos."
                )
            U[k, k] = raiz
            L[k, k] = U[k, k]

        if L[k, k] == 0 or U[k, k] == 0:
            return {
                'metodo': nombre,
                'estado': ERROR,
                'exito': False,
                'mensaje': f"En la etapa {k+1} el elemento diagonal se hizo 0: la factorización no puede completarse.",
                'matrices': {'L': _limpio_arreglo(L), 'U': _limpio_arreglo(U)},
                'etapas': etapas,
                'diagnostico_matriz': diagnosticar_matriz(A, tipo_norma),
            }

        for i in range(k + 1, n):
            suma2 = sum(L[i, p] * U[p, k] for p in range(k))
            L[i, k] = (A[i, k] - suma2) / U[k, k]
        for j in range(k + 1, n):
            suma3 = sum(L[k, p] * U[p, j] for p in range(k))
            U[k, j] = (A[k, j] - suma3) / L[k, k]

        etapas.append({
            'etapa': k + 1,
            'descripcion': f"Cálculo de fila/columna {k+1}",
            'L': _limpio_arreglo(L.copy()),
            'U': _limpio_arreglo(U.copy()),
        })

    z = sustitucion_progresiva(np.column_stack((L, b)), n)
    x = sustitucion_regresiva(np.column_stack((U, z)), n)
    if np.iscomplexobj(x) and np.allclose(np.imag(x), 0):
        x = np.real(x)
    tiempo_ms = round((time.perf_counter() - t0) * 1000, 3)
    res_info = error_residuo(A, b, x, tipo_norma)

    return {
        'metodo': nombre,
        'estado': EXITO,
        'exito': True,
        'mensaje': "Sistema resuelto exitosamente.",
        'avisos': avisos,
        'solucion': _limpio_arreglo(x),
        'matrices': {
            'L': _limpio_arreglo(L),
            'U': _limpio_arreglo(U),
            'z (Lz = b)': _limpio_arreglo(z),
        },
        'etapas': etapas,
        'residuo': res_info,
        'error_cond': res_info.get('error_cond'),
        'diagnostico_matriz': diagnosticar_matriz(A, tipo_norma),
        'tiempo_ms': tiempo_ms,
    }

