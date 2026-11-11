# Trabajo Final · Análisis Numérico (EAFIT)

Aplicación web para ejecutar los métodos numéricos vistos en el curso, organizada por capítulos.

**Integrante:** Santiago Vélez Blandón

- **Backend:** Python, Django, NumPy y SymPy (carpeta `backend/`). Los métodos están en `backend/motor/` y la API en `backend/api/`.
- **Frontend:** React 18 (carpeta `frontend/`). React, Babel, KaTeX y las fuentes se cargan desde internet, así que la app necesita conexión para abrirse.

## Cómo ejecutarla

Requiere Python 3.10 o superior. Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\manage.py runserver 8000
```

Luego abre **http://127.0.0.1:8000** en el navegador.

En Linux o macOS, usa `.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

## Qué incluye

### Capítulo 1 · Ecuaciones no lineales f(x) = 0

- **Métodos:** bisección, regla falsa, punto fijo, Newton-Raphson, secante y raíces múltiples (con multiplicidad m y con segunda derivada).
- **Funciones:** acepta cualquier función algebraica o trascendente (`x^3 - 2x + e^x`, `sin(x)`, `ln(x)`, `sqrt(x)`…).
- **Derivadas:** f'(x) y f''(x) se calculan automáticamente con SymPy. En punto fijo se sugieren funciones g(x) y se indica cuáles cumplen |g'(x₀)| < 1.
- **Resultados:** tabla de iteraciones y gráfica de f(x), con la animación de cada iteración y la gráfica de convergencia de los errores.
- **Comparación:** corre todos los métodos con error absoluto, relativo y de condición (|f(x)|). Muestra una gráfica, una tabla cruzada método × criterio y un informe.

### Capítulo 2 · Sistemas de ecuaciones lineales Ax = b

- **Métodos:** Jacobi, Gauss-Seidel y SOR.
- **Ingreso de datos:** matrices de 2×2 a 8×8, por cuadrícula o por texto (`;` separa filas y `,` separa columnas).
- **Resultados:** tabla de iteraciones, matrices T y C, radio espectral ρ(T) e indicación de si el método converge (ρ(T) < 1). También el número de condición κ(A) y la dominancia diagonal.
- **Comparación:** corre los tres métodos con error absoluto, relativo y de condición (‖b − Ax‖), con gráfica, tabla cruzada e informe.

### Capítulo 3 · Interpolación

- **Métodos:** Vandermonde, Newton (diferencias divididas), Lagrange y splines lineal, cuadrático y cúbico.
- **Ingreso de datos:** hasta 10 puntos, por casillas o como vectores X e Y.
- **Resultados:** el polinomio solución (o los tramos de cada spline) y su gráfica. Según el método, también la tabla de diferencias divididas, la matriz de Vandermonde o las bases de Lagrange.
- **Reserva de datos:** permite reservar el 20 % o el 30 % de los puntos. Esos puntos no se usan para construir el polinomio, sino para medir el error de interpolación en ellos. Los conjuntos de datos se pueden guardar y volver a cargar.
- **Comparación:** los 6 métodos superpuestos en una misma gráfica, con su error en los puntos reservados.

### Ayuda y validaciones

- **Ayuda:** cada capítulo tiene una guía de cómo ingresar los datos, y hay una ayuda general en la barra lateral.
- **Validaciones:**
  - intervalos sin cambio de signo;
  - divisiones por cero en Newton, secante y raíces múltiples;
  - g(x) que no corresponde a f(x);
  - ceros en la diagonal, celdas vacías y ω fuera de (0, 2);
  - valores de x repetidos.

## Pruebas

```powershell
cd backend
..\.venv\Scripts\python.exe verificar_api.py
```

Prueba todos los métodos a través de la API, incluidos los casos de error.
