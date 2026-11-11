"""Interpretación de funciones algebraicas y trascendentes con SymPy.

Incluye:
- Conversión desde notación matemática natural (ej: "5x", "x^2", "e^x", "sen(x)", "ln(x)")
- Generación de representación LaTeX para renderizado en el frontend
- Cálculo automático de primera y segunda derivada (y sugerencias de g(x) para Punto Fijo)
- Evaluación numérica segura sobre escalares y arreglos de NumPy
"""
import re

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

x = sp.Symbol('x', real=True)

_TRANSFORMACIONES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

_NOMBRES = {
    'x': x, 'X': x,
    'e': sp.E, 'E': sp.E, 'pi': sp.pi,
    'ln': sp.log, 'log': sp.log, 'exp': sp.exp,
    'sin': sp.sin, 'sen': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'tg': sp.tan,
    'sec': sp.sec, 'csc': sp.csc, 'cot': sp.cot,
    'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'arcsin': sp.asin, 'arccos': sp.acos, 'arctan': sp.atan,
    'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
    'sqrt': sp.sqrt, 'raiz': sp.sqrt, 'abs': sp.Abs,
}

AYUDA = "ej: x^3 - 2x + e^x, sin(x), ln(x), sqrt(x), abs(x+2)"


def _limpiar(texto):
    if texto is None:
        return ""
    texto = str(texto).strip()
    texto = re.sub(r'^\s*[a-zA-Z]\w*\s*\(\s*x\s*\)\s*=', '', texto)
    texto = re.sub(r'\b(math|np|numpy)\.', '', texto)
    return texto.strip()


def interpretar(texto):
    """Convierte el texto en una expresión SymPy de x. Lanza ValueError con explicación clara."""
    limpio = _limpiar(texto)
    if not limpio:
        raise ValueError("No escribiste ninguna función. Ingresa una expresión en términos de x.")
    try:
        expr = parse_expr(limpio, local_dict=dict(_NOMBRES), transformations=_TRANSFORMACIONES)
    except Exception:
        raise ValueError(
            f"No se pudo interpretar la función '{texto}'. Revisa que los paréntesis estén cerrados "
            f"y los operadores bien escritos ({AYUDA})."
        )
    if not isinstance(expr, sp.Expr):
        raise ValueError(f"'{texto}' no es una expresión matemática válida.")
    otras = expr.free_symbols - {x}
    if otras:
        nombres = ', '.join(sorted(str(s) for s in otras))
        raise ValueError(f"La función solo puede depender de la variable 'x' (se encontró: {nombres}).")
    return expr


def interpretar_numero(texto):
    """Lee un número real o constante matemática: 2, -1.5, 1e-7, 1/3, pi/2, e, sqrt(2)."""
    if isinstance(texto, (int, float, np.number)):
        val = float(texto)
        if not np.isfinite(val):
            raise ValueError("El número debe ser finito.")
        return val
    limpio = str(texto).strip()
    if not limpio:
        raise ValueError("El campo numérico está vacío.")
    try:
        val = float(limpio)
        if not np.isfinite(val):
            raise ValueError
        return val
    except ValueError:
        pass
    try:
        expr = parse_expr(_limpiar(limpio), local_dict=dict(_NOMBRES), transformations=_TRANSFORMACIONES)
        if not isinstance(expr, sp.Expr) or expr.free_symbols:
            raise ValueError
        valor = complex(sp.N(expr))
    except Exception:
        raise ValueError(f"'{texto}' no es un número real válido (puedes usar decimales, 1e-7, pi/2, sqrt(2)...).")
    if abs(valor.imag) > 1e-12 or not np.isfinite(valor.real):
        raise ValueError(f"'{texto}' no da un número real finito.")
    return float(valor.real)


def mostrar(expr):
    """Texto legible de una expresión: x**2 -> x^2, log -> ln, Abs -> abs."""
    texto = sp.sstr(expr).replace('**', '^')
    texto = re.sub(r'\blog\(', 'ln(', texto)
    texto = re.sub(r'\bAbs\(', 'abs(', texto)
    return texto


def a_latex(expr):
    """Convierte una expresión SymPy a código LaTeX limpio."""
    try:
        return sp.latex(expr, ln_notation=True)
    except Exception:
        return mostrar(expr)


class Funcion:
    """Función de una variable que se puede evaluar, derivar y exportar a LaTeX."""

    def __init__(self, expr, original=None):
        self.expr = expr
        self.texto = mostrar(expr)
        self.latex = a_latex(expr)
        self.original = original
        self._numerica = sp.lambdify(x, expr, modules='numpy')

    @classmethod
    def desde_texto(cls, texto):
        return cls(interpretar(texto), _limpiar(texto))

    def derivada(self):
        d = sp.diff(self.expr, x)
        d = d.replace(sp.DiracDelta, lambda *args: sp.S.Zero)
        return Funcion(d)

    def __call__(self, valor):
        try:
            with np.errstate(all='ignore'):
                r = self._numerica(np.float64(valor))
            r = complex(r)
            if abs(r.imag) > 1e-12:
                return float('nan')
            return float(r.real)
        except Exception:
            return float('nan')

    def evaluar_arreglo(self, xs):
        xs = np.asarray(xs, dtype=float)
        try:
            with np.errstate(all='ignore'):
                ys = self._numerica(xs)
            ys = np.broadcast_to(np.asarray(ys), xs.shape)
            if np.iscomplexobj(ys):
                ys = np.where(np.abs(np.imag(ys)) <= 1e-12, np.real(ys), np.nan)
            ys = np.array(ys, dtype=float)
        except Exception:
            ys = np.array([self(v) for v in xs], dtype=float)
        ys[~np.isfinite(ys)] = np.nan
        return ys

    def __str__(self):
        return self.original if self.original else self.texto


def analizar_funcion(texto_f, x0=None):
    """Analiza f(x), calcula f'(x) y f''(x), y sugiere funciones g(x) para Punto Fijo."""
    f = Funcion.desde_texto(texto_f)
    df = f.derivada()
    d2f = df.derivada()

    sugerencias_g = []
    vistas = set()

    # 1. Intentar despejar el término lineal a*x de f(x) = 0
    try:
        expandida = sp.expand(f.expr)
        coef_x = expandida.coeff(x, 1)
        if coef_x != 0 and not coef_x.has(x):
            resto = expandida - coef_x * x
            g_despeje = sp.simplify(-resto / coef_x)
            txt = mostrar(g_despeje)
            if txt not in vistas:
                vistas.add(txt)
                sugerencias_g.append({
                    'texto': txt,
                    'latex': a_latex(g_despeje),
                    'descripcion': 'Despeje algebraico del término lineal de x',
                })
    except Exception:
        pass

    # 2. Forma canónica g(x) = x - f(x) y amortiguada g(x) = x - f(x)/f'(x0)
    for expr_cand, desc in [
        (sp.simplify(x - f.expr), 'Transformación directa: g(x) = x - f(x)'),
        (sp.simplify(x + f.expr), 'Transformación directa: g(x) = x + f(x)'),
    ]:
        txt = mostrar(expr_cand)
        if txt not in vistas:
            vistas.add(txt)
            sugerencias_g.append({
                'texto': txt,
                'latex': a_latex(expr_cand),
                'descripcion': desc,
            })

    # Si se dio x0, evaluar |g'(x0)| en cada sugerencia para indicar si converge localmente
    if x0 is not None:
        try:
            val_x0 = interpretar_numero(x0)
            for sug in sugerencias_g:
                g_fun = Funcion.desde_texto(sug['texto'])
                dg_val = abs(g_fun.derivada()(val_x0))
                sug['dg_x0'] = float(dg_val) if np.isfinite(dg_val) else None
                sug['converge_local'] = bool(np.isfinite(dg_val) and dg_val < 1.0)
        except Exception:
            pass

    return {
        'f': {'texto': f.texto, 'original': str(f), 'latex': f.latex},
        'df': {'texto': df.texto, 'latex': df.latex},
        'd2f': {'texto': d2f.texto, 'latex': d2f.latex},
        'sugerencias_g': sugerencias_g,
    }

