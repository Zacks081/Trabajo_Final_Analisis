// ============================================================================
// CAPÍTULO 2: SISTEMAS DE ECUACIONES LINEALES Ax = b (HASTA 8×8)
// Métodos: Jacobi, Gauss-Seidel, SOR y comparación de los tres
// ============================================================================

const { useState, useEffect } = React;

const METODOS_CAP2 = [
  { id: 'jacobi', nombre: 'Jacobi', desc: 'x⁽ᵏ⁺¹⁾ = D⁻¹(L + U)x⁽ᵏ⁾ + D⁻¹b' },
  { id: 'gauss_seidel', nombre: 'Gauss-Seidel', desc: 'x⁽ᵏ⁺¹⁾ = (D − L)⁻¹Ux⁽ᵏ⁾ + (D − L)⁻¹b' },
  { id: 'sor', nombre: 'SOR (relajación)', desc: 'Gauss-Seidel con factor de relajación ω ∈ (0, 2)' },
  { id: 'comparar', nombre: 'Comparar todos', desc: 'Compara Jacobi, Gauss-Seidel y SOR con error absoluto, relativo y de condición' }
];

const EJEMPLOS_CAP2 = [
  { nombre: 'Sistema 3×3 (EDD)', n: 3, A: [[10, -1, 2], [-1, 11, -1], [2, -1, 10]], b: [6, 25, -11], x0: [0, 0, 0], omega: '1.15' },
  {
    nombre: 'Sistema 4×4 de clase',
    n: 4,
    A: [[45, 13, -4, 8], [-5, -28, 4, -14], [9, 15, 63, -7], [2, 3, -8, -42]],
    b: [-25, 82, 75, -43],
    x0: [2, 2, 2, 2],
    omega: '1.08'
  },
  {
    nombre: 'Sistema 6×6 tridiagonal',
    n: 6,
    A: [
      [4, -1, 0, 0, 0, 0],
      [-1, 4, -1, 0, 0, 0],
      [0, -1, 4, -1, 0, 0],
      [0, 0, -1, 4, -1, 0],
      [0, 0, 0, -1, 4, -1],
      [0, 0, 0, 0, -1, 4]
    ],
    b: [100, 0, 0, 0, 0, 100],
    x0: [0, 0, 0, 0, 0, 0],
    omega: '1.22'
  },
  {
    nombre: 'Sistema 8×8',
    n: 8,
    A: [
      [12, -2, 1, 0, 0, 0, 0, 1],
      [-2, 14, -3, 1, 0, 0, 0, 0],
      [1, -3, 15, -2, 1, 0, 0, 0],
      [0, 1, -2, 13, -2, 1, 0, 0],
      [0, 0, 1, -2, 16, -3, 1, 0],
      [0, 0, 0, 1, -3, 14, -2, 1],
      [0, 0, 0, 0, 1, -2, 15, -2],
      [1, 0, 0, 0, 0, 1, -2, 12]
    ],
    b: [12, 10, 12, 11, 13, 11, 12, 12],
    x0: [0, 0, 0, 0, 0, 0, 0, 0],
    omega: '1.12'
  }
];

const CLAVE_ERROR_C2 = { abs: 'error_abs', rel: 'error_rel', cond: 'error_cond' };

function matrizATexto(M) {
  return M.map((fila) => fila.join(', ')).join(';\n');
}

function vectorATexto(v) {
  return v.join(', ');
}

// '1, 2; 3, 4' -> [['1','2'],['3','4']] (o null si no es una matriz cuadrada de 2×2 a 8×8)
function textoAMatriz(texto) {
  const filas = texto.replace(/[[\]]/g, '').split(/[;\n]+/).map((f) => f.trim()).filter(Boolean);
  const celdas = filas.map((f) => f.split(/[\s,]+/).filter(Boolean));
  const n = celdas.length;
  if (n < 2 || n > 8 || celdas.some((f) => f.length !== n)) return null;
  return celdas;
}

function textoAVector(texto) {
  return texto.replace(/[[\]]/g, '').split(/[\s,;]+/).filter(Boolean);
}

const vacio = (v) => v === null || v === undefined || String(v).trim() === '';

function Chapter2({ apiUrl, notify }) {
  const [metodo, setMetodo] = useState('jacobi');
  const [n, setN] = useState(4);
  const [modoEntrada, setModoEntrada] = useState('grid');
  const [matrizA, setMatrizA] = useState(EJEMPLOS_CAP2[1].A);
  const [vectorB, setVectorB] = useState(EJEMPLOS_CAP2[1].b);
  const [vectorX0, setVectorX0] = useState(EJEMPLOS_CAP2[1].x0);

  const [textoA, setTextoA] = useState(matrizATexto(EJEMPLOS_CAP2[1].A));
  const [textoB, setTextoB] = useState(vectorATexto(EJEMPLOS_CAP2[1].b));
  const [textoX0, setTextoX0] = useState(vectorATexto(EJEMPLOS_CAP2[1].x0));

  const [omega, setOmega] = useState('1.08');
  const [norma, setNorma] = useState('inf');
  const [tipoError, setTipoError] = useState('rel');
  const [tol, setTol] = useState('1e-7');
  const [maxIter, setMaxIter] = useState('100');

  const [resultado, setResultado] = useState(null);
  const [comparacion, setComparacion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [mostrarGuiaDatos, setMostrarGuiaDatos] = useState(false);
  const [verMatricesDescomp, setVerMatricesDescomp] = useState(false);
  const [marcarVacias, setMarcarVacias] = useState(false);

  const cambiarTamano = (nuevoN) => {
    const dim = Math.max(2, Math.min(8, parseInt(nuevoN, 10) || 3));
    const nuevaA = Array.from({ length: dim }, (_, i) =>
      Array.from({ length: dim }, (__, j) => {
        if (i < matrizA.length && j < (matrizA[0]?.length || 0)) {
          return matrizA[i][j];
        }
        return i === j ? 10 : 1;
      })
    );
    const nuevoB = Array.from({ length: dim }, (_, i) => (i < vectorB.length ? vectorB[i] : 1));
    const nuevoX0 = Array.from({ length: dim }, (_, i) => (i < vectorX0.length ? vectorX0[i] : 0));
    setN(dim);
    setMatrizA(nuevaA);
    setVectorB(nuevoB);
    setVectorX0(nuevoX0);
    setTextoA(matrizATexto(nuevaA));
    setTextoB(vectorATexto(nuevoB));
    setTextoX0(vectorATexto(nuevoX0));
  };

  const generarMatrizEDD = () => {
    const nuevaA = Array.from({ length: n }, (_, i) => {
      let sumaFila = 0;
      const fila = Array.from({ length: n }, (__, j) => {
        if (i === j) return 0;
        const val = Math.round((Math.random() * 6 - 3) * 10) / 10;
        sumaFila += Math.abs(val);
        return val;
      });
      fila[i] = Math.round((sumaFila + 4 + Math.random() * 5) * 10) / 10;
      return fila;
    });
    const nuevoB = Array.from({ length: n }, () => Math.round((Math.random() * 20 - 5) * 10) / 10);
    const nuevoX0 = Array.from({ length: n }, () => 0);

    setMatrizA(nuevaA);
    setVectorB(nuevoB);
    setVectorX0(nuevoX0);
    setTextoA(matrizATexto(nuevaA));
    setTextoB(vectorATexto(nuevoB));
    setTextoX0(vectorATexto(nuevoX0));
  };

  const actualizarCeldaA = (i, j, valor) => {
    const copia = matrizA.map((f) => [...f]);
    copia[i][j] = valor;
    setMatrizA(copia);
    setTextoA(matrizATexto(copia));
  };

  const actualizarCeldaB = (i, valor) => {
    const copia = [...vectorB];
    copia[i] = valor;
    setVectorB(copia);
    setTextoB(vectorATexto(copia));
  };

  const actualizarCeldaX0 = (i, valor) => {
    const copia = [...vectorX0];
    copia[i] = valor;
    setVectorX0(copia);
    setTextoX0(vectorATexto(copia));
  };

  // En modo texto, si la matriz escrita es cuadrada se sincroniza el tamaño y la cuadrícula
  const cambiarTextoA = (texto) => {
    setTextoA(texto);
    const celdas = textoAMatriz(texto);
    if (celdas) {
      setN(celdas.length);
      setMatrizA(celdas);
    }
  };

  const cambiarTextoVector = (texto, setTexto, setVector) => {
    setTexto(texto);
    const valores = textoAVector(texto);
    if (valores.length === n) setVector(valores);
  };

  const cargarEjemplo = (ej) => {
    setN(ej.n);
    setMatrizA(ej.A);
    setVectorB(ej.b);
    setVectorX0(ej.x0);
    setTextoA(matrizATexto(ej.A));
    setTextoB(vectorATexto(ej.b));
    setTextoX0(vectorATexto(ej.x0));
    setOmega(ej.omega);
    setErrorMsg(null);
    setMarcarVacias(false);
  };

  const cambiarMetodo = (id) => {
    setMetodo(id);
    setErrorMsg(null);
    setResultado(null);
  };

  const ejecutar = async (e) => {
    if (e) e.preventDefault();
    setErrorMsg(null);

    if (modoEntrada === 'grid') {
      const faltaA = matrizA.some((f) => f.some(vacio));
      const faltaB = vectorB.some(vacio);
      const faltaX0 = vectorX0.some(vacio);
      if (faltaA || faltaB || faltaX0) {
        setMarcarVacias(true);
        const partes = [faltaA && 'la matriz A', faltaB && 'el vector b', faltaX0 && 'el vector inicial x⁽⁰⁾'].filter(Boolean);
        setErrorMsg(`Hay casillas vacías en ${partes.join(', ')} (marcadas en rojo). Escribe un número en cada una.`);
        return;
      }
      setMarcarVacias(false);
    }

    setCargando(true);
    try {
      const url = metodo === 'comparar' ? `${apiUrl}/capitulo-2/comparar/` : `${apiUrl}/capitulo-2/ejecutar/`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metodo,
          A: modoEntrada === 'texto' ? textoA : matrizA.map((f) => f.map(String)),
          b: modoEntrada === 'texto' ? textoB : vectorB.map(String),
          x0: modoEntrada === 'texto' ? textoX0 : vectorX0.map(String),
          omega,
          tol,
          max_iter: maxIter,
          norma,
          tipo_error: tipoError
        })
      });
      const data = await resp.json();
      if (!data.ok) {
        setErrorMsg(data.error || 'Error al resolver el sistema lineal.');
      } else if (metodo === 'comparar') {
        setComparacion(data);
      } else {
        setResultado(data);
      }
    } catch (err) {
      setErrorMsg('No se pudo conectar con el servidor de Django.');
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    ejecutar();
  }, []);

  const exportarCSV = () => {
    if (!resultado || !resultado.iteraciones || !resultado.iteraciones.length) return;
    const dim = resultado.solucion?.length || n;
    const xHeaders = Array.from({ length: dim }, (_, i) => `x${i + 1}`);
    const header = ['k', ...xHeaders, 'error_abs', 'error_rel', 'error_cond'].join(',');
    const rows = resultado.iteraciones.map((r) =>
      [r.iteracion, ...(r.x || []), r.error_abs, r.error_rel, r.error_cond].join(',')
    );
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `cap2_${metodo}_iteraciones.csv`;
    link.click();
  };

  const infoMetodoActual = METODOS_CAP2.find((m) => m.id === metodo) || METODOS_CAP2[0];
  const claseCelda = (valor) => (marcarVacias && vacio(valor) ? ' cell-error' : '');

  return (
    <div className="chapter-view">
      <div className="chapter-header">
        <div>
          <h1 className="chapter-title">
            Capítulo 2 · Sistemas lineales <MathTex tex="A\mathbf{x} = \mathbf{b}" />
          </h1>
          <p className="chapter-subtitle">{infoMetodoActual.desc}</p>
        </div>
        <button type="button" className="btn-secondary" onClick={() => setMostrarGuiaDatos((v) => !v)}>
          {mostrarGuiaDatos ? 'Ocultar ayuda' : '? Cómo ingresar matrices'}
        </button>
      </div>

      {mostrarGuiaDatos && (
        <div className="glass-card help-banner">
          <div className="help-banner-header">
            <strong>Cómo ingresar los datos · Capítulo 2 (matrices hasta 8×8)</strong>
            <button type="button" className="btn-ghost" onClick={() => setMostrarGuiaDatos(false)} aria-label="Cerrar ayuda">✕</button>
          </div>
          <div className="help-banner-grid">
            <div>
              <h4>Cuadrícula o texto</h4>
              <p>
                Elige el tamaño de <MathTex tex="2\times 2" /> a <MathTex tex="8\times 8" />. En modo texto separa las columnas con comas <code>,</code> y las filas con punto y coma <code>;</code>; el tamaño se ajusta solo.
              </p>
            </div>
            <div>
              <h4>Radio espectral <MathTex tex="\rho(T)" /></h4>
              <p>
                El método converge para cualquier <MathTex tex="\mathbf{x}^{(0)}" /> si y solo si <MathTex tex="\rho(T) < 1" />. Ningún elemento de la diagonal <MathTex tex="a_{ii}" /> puede ser cero.
              </p>
            </div>
            <div>
              <h4>Tipos de error</h4>
              <p>
                Relativo <MathTex tex="\|x^{(k)}-x^{(k-1)}\|/\|x^{(k)}\|" />, absoluto <MathTex tex="\|x^{(k)}-x^{(k-1)}\|" /> o de condición <MathTex tex="\|b-Ax^{(k)}\|" />.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="method-tabs" role="tablist">
        {METODOS_CAP2.map((m) => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={metodo === m.id}
            className={`method-tab ${metodo === m.id ? 'active ch2' : ''} ${m.id === 'comparar' ? 'compare-tab' : ''}`}
            onClick={() => cambiarMetodo(m.id)}
          >
            {m.nombre}
          </button>
        ))}
      </div>

      <div className="preset-bar">
        <span className="preset-label">Ejemplos:</span>
        {EJEMPLOS_CAP2.map((ej, idx) => (
          <button key={idx} type="button" className="preset-chip" onClick={() => cargarEjemplo(ej)}>
            {ej.nombre}
          </button>
        ))}
        <button type="button" className="preset-chip highlight" onClick={generarMatrizEDD}>
          Generar {n}×{n} EDD aleatoria
        </button>
      </div>

      <div className="workspace-stack">
        <form className="glass-card input-panel" onSubmit={ejecutar}>
          <div className="panel-title-row">
            <h3>Configuración del sistema ({n}×{n})</h3>
            <span className="badge badge-ch2">{infoMetodoActual.nombre}</span>
          </div>

          <div className="input-grid-layout">
            {/* Columna izquierda: controles */}
            <div className="input-column">
              <div className="form-row-2">
                <div className="form-group">
                  <span className="form-label">Tamaño de la matriz (hasta 8×8)</span>
                  <div className="size-selector">
                    {[2, 3, 4, 5, 6, 7, 8].map((dim) => (
                      <button
                        key={dim}
                        type="button"
                        className={`size-btn ${n === dim ? 'active' : ''}`}
                        onClick={() => cambiarTamano(dim)}
                      >
                        {dim}×{dim}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <span className="form-label">Modo de ingreso</span>
                  <div className="segmented-control two-cols">
                    <button type="button" className={`segment-btn ${modoEntrada === 'grid' ? 'active' : ''}`} onClick={() => setModoEntrada('grid')}>
                      Cuadrícula
                    </button>
                    <button type="button" className={`segment-btn ${modoEntrada === 'texto' ? 'active' : ''}`} onClick={() => setModoEntrada('texto')}>
                      Texto (; y ,)
                    </button>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <span className="form-label">Tipo de error (criterio de parada)</span>
                <div className="segmented-control" role="radiogroup" aria-label="Tipo de error">
                  {['rel', 'abs', 'cond'].map((id) => (
                    <button
                      key={id}
                      type="button"
                      role="radio"
                      aria-checked={tipoError === id}
                      className={`segment-btn ${tipoError === id ? 'active' : ''}`}
                      onClick={() => setTipoError(id)}
                    >
                      {NOMBRE_ERROR[id]}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-row-3">
                <div className="form-group">
                  <label className="form-label" htmlFor="c2-norma">Norma</label>
                  <select id="c2-norma" className="form-select" value={norma} onChange={(e) => setNorma(e.target.value)}>
                    <option value="inf">Norma ∞ (máximo)</option>
                    <option value="2">Norma 2 (euclidiana)</option>
                    <option value="1">Norma 1</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="c2-tol">Tolerancia</label>
                  <input id="c2-tol" type="text" inputMode="decimal" className="form-input mono" value={tol} onChange={(e) => setTol(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="c2-niter">Máx. iteraciones</label>
                  <input id="c2-niter" type="number" min="1" max="2000" className="form-input mono" value={maxIter} onChange={(e) => setMaxIter(e.target.value)} />
                </div>
              </div>

              {(metodo === 'sor' || metodo === 'comparar') && (
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="c2-omega">Factor ω (SOR)</label>
                    <input id="c2-omega" type="text" inputMode="decimal" className="form-input mono" value={omega} onChange={(e) => setOmega(e.target.value)} />
                  </div>
                </div>
              )}
            </div>

            {/* Columna derecha: A, b y x0 */}
            <div className="input-column">
              {modoEntrada === 'grid' ? (
                <>
                  <div className="form-group">
                    <span className="form-label">
                      <span>Matriz aumentada <MathTex tex="[A \mid \mathbf{b}]" /> ({n}×{n})</span>
                      <span className="label-hint">diagonal en violeta · b en cian</span>
                    </span>
                    <div className="matrix-scroll-wrapper">
                      <div className="matrix-input-grid" style={{ gridTemplateColumns: `repeat(${n}, 64px) 16px 68px` }}>
                        {matrizA.map((fila, i) => (
                          <React.Fragment key={i}>
                            {fila.map((val, j) => (
                              <input
                                key={`${i}-${j}`}
                                type="text"
                                inputMode="decimal"
                                className={`matrix-cell-input ${i === j ? 'diag-cell' : ''}${claseCelda(val)}`}
                                value={val}
                                onChange={(e) => actualizarCeldaA(i, j, e.target.value)}
                                aria-label={`a ${i + 1},${j + 1}`}
                              />
                            ))}
                            <span className="aug-sep">|</span>
                            <input
                              type="text"
                              inputMode="decimal"
                              className={`matrix-cell-input b-cell${claseCelda(vectorB[i])}`}
                              value={vectorB[i] ?? ''}
                              onChange={(e) => actualizarCeldaB(i, e.target.value)}
                              aria-label={`b ${i + 1}`}
                            />
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="form-group">
                    <span className="form-label">Vector inicial <MathTex tex="\mathbf{x}^{(0)}" /></span>
                    <div className="matrix-scroll-wrapper" style={{ padding: '8px 12px' }}>
                      <div className="x0-input-grid" style={{ gridTemplateColumns: `repeat(${n}, 64px)` }}>
                        {vectorX0.map((val, i) => (
                          <input
                            key={i}
                            type="text"
                            inputMode="decimal"
                            className={`matrix-cell-input${claseCelda(val)}`}
                            value={val}
                            onChange={(e) => actualizarCeldaX0(i, e.target.value)}
                            aria-label={`x0 ${i + 1}`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="form-group">
                    <label className="form-label" htmlFor="c2-textoA">Matriz A (filas con ; y columnas con ,)</label>
                    <textarea id="c2-textoA" rows={4} className="form-textarea mono" value={textoA} onChange={(e) => cambiarTextoA(e.target.value)} spellCheck={false} />
                  </div>
                  <div className="form-row-2">
                    <div className="form-group">
                      <label className="form-label" htmlFor="c2-textoB">Vector b</label>
                      <input id="c2-textoB" type="text" className="form-input mono" value={textoB} onChange={(e) => cambiarTextoVector(e.target.value, setTextoB, setVectorB)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="c2-textoX0">Vector inicial x⁽⁰⁾</label>
                      <input id="c2-textoX0" type="text" className="form-input mono" value={textoX0} onChange={(e) => cambiarTextoVector(e.target.value, setTextoX0, setVectorX0)} />
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {errorMsg && (
            <div className="alert-box alert-error" role="alert">
              <strong>Revisa los datos:</strong> {errorMsg}
            </div>
          )}

          <div className="submit-bar">
            <button type="submit" className="btn-primary btn-ch2" disabled={cargando}>
              {cargando
                ? 'Calculando…'
                : metodo === 'comparar'
                ? 'Comparar Jacobi, Gauss-Seidel y SOR'
                : `Resolver con ${infoMetodoActual.nombre}`}
            </button>
          </div>
        </form>

        <div className="results-panel">
          {metodo === 'comparar' ? (
            <ComparativeReportCap2 comparacion={comparacion} />
          ) : resultado ? (
            <>
              <div className="kpi-grid">
                <div className={`kpi-card ${resultado.puede_converger ? 'highlight-ch2' : 'highlight-warn'}`}>
                  <span className="kpi-label">Radio espectral ρ(T)</span>
                  <div className="kpi-value mono">{fmtNum(resultado.radio_espectral, 6)}</div>
                  <span className="kpi-sub">
                    {resultado.puede_converger ? 'ρ(T) < 1: el método converge' : 'ρ(T) ≥ 1: el método no converge en general'}
                  </span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-label">Iteraciones</span>
                  <div className="kpi-value mono">{resultado.iteraciones_usadas}</div>
                  <span className="kpi-sub">
                    {resultado.dominancia?.es_edd ? 'A es diagonalmente dominante (EDD)' : 'A no es EDD (decide ρ(T))'}
                  </span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-label">Error final ({NOMBRE_ERROR[tipoError].toLowerCase()})</span>
                  <div className="kpi-value mono">{fmtSci(resultado.error_final)}</div>
                  <span className="kpi-sub">Residuo ‖b − Ax‖: {fmtSci(resultado.residuo_norma)}</span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-label">Número de condición κ(A)</span>
                  <div className="kpi-value mono">{fmtNum(resultado.condicion_matriz, 4)}</div>
                  <span className="kpi-sub">Sensibilidad del sistema a perturbaciones</span>
                </div>
              </div>

              <EstadoMetodo
                exito={resultado.exito}
                estado={resultado.estado}
                mensaje={resultado.mensaje}
                avisos={resultado.avisos || []}
              />

              <div className="glass-card">
                <div className="table-header-bar">
                  <h3>Solución aproximada <MathTex tex="\mathbf{x}^*" /></h3>
                  {resultado.matrices && (
                    <button type="button" className="btn-secondary" onClick={() => setVerMatricesDescomp((v) => !v)}>
                      {verMatricesDescomp ? 'Ocultar T, C, D, L, U' : 'Ver T, C, D, L, U'}
                    </button>
                  )}
                </div>

                <div className="solution-pills">
                  {(resultado.solucion || []).map((val, idx) => (
                    <div key={idx} className="solution-pill">
                      <span className="sol-var">x<sub>{idx + 1}</sub> =</span>
                      <span className="mono">{fmtNum(val, 8)}</span>
                    </div>
                  ))}
                </div>

                {verMatricesDescomp && resultado.matrices && (
                  <div className="decomp-matrices-grid">
                    <MatrixView matrix={resultado.matrices.T} label="Matriz de iteración T" digits={5} />
                    <MatrixView matrix={resultado.matrices.C} label="Vector C" digits={5} />
                    <MatrixView matrix={resultado.matrices.D} label="Matriz diagonal D" digits={4} />
                    <MatrixView matrix={resultado.matrices.L} label="Matriz L" digits={4} />
                    <MatrixView matrix={resultado.matrices.U} label="Matriz U" digits={4} />
                  </div>
                )}
              </div>

              {resultado.iteraciones && resultado.iteraciones.length > 0 && (
                <>
                  <ConvergenceChart
                    series={[
                      { name: 'Error relativo', color: '#00f5d4', values: resultado.iteraciones.map((r) => r.error_rel) },
                      { name: 'Error absoluto', color: '#7c5cff', values: resultado.iteraciones.map((r) => r.error_abs) },
                      { name: 'Condición ‖b − Ax‖', color: '#ffbe0b', values: resultado.iteraciones.map((r) => r.error_cond) }
                    ]}
                    titulo={`Evolución de los errores · ${resultado.metodo} (ρ(T) = ${fmtNum(resultado.radio_espectral, 4)})`}
                  />

                  <div className="glass-card">
                    <div className="table-header-bar">
                      <h3>Tabla solución · {resultado.metodo}</h3>
                      <button type="button" className="btn-secondary" onClick={exportarCSV}>
                        Exportar CSV
                      </button>
                    </div>
                    <div className="table-scroll">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>k</th>
                            {(resultado.solucion || []).map((_, idx) => (
                              <th key={idx}>x<sub>{idx + 1}</sub></th>
                            ))}
                            <th>Error absoluto</th>
                            <th>Error relativo</th>
                            <th>Error de condición ‖b − Ax‖</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultado.iteraciones.map((row, idx) => (
                            <tr key={idx}>
                              <td className="mono">{row.iteracion}</td>
                              {(row.x || []).map((val, j) => (
                                <td key={j} className="mono">{fmtNum(val, 7)}</td>
                              ))}
                              <td className="mono">{fmtSci(row.error_abs)}</td>
                              <td className="mono">{fmtSci(row.error_rel)}</td>
                              <td className="mono">{fmtSci(row.error_cond)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ComparativeReportCap2({ comparacion }) {
  const [criterioGrafica, setCriterioGrafica] = useState(null);

  if (!comparacion) {
    return (
      <div className="glass-card">
        <p style={{ color: 'var(--text-secondary)' }}>
          Presiona <strong>"Comparar Jacobi, Gauss-Seidel y SOR"</strong> para correr cada método con los tres tipos de error.
        </p>
      </div>
    );
  }

  const { metodos = [], metodos_por_criterio: porCriterio = {}, informe = {}, propiedades_matriz = {} } = comparacion;
  const criterio = criterioGrafica || comparacion.tipo_error || 'rel';
  const colores = ['#00f5d4', '#7c5cff', '#ffbe0b'];

  const seriesGrafica = (porCriterio[criterio] || [])
    .filter((m) => m.historia && m.historia.length > 0)
    .map((m, i) => ({
      name: `${m.metodo} (ρ = ${fmtNum(m.radio_espectral, 3)})`,
      color: colores[i % colores.length],
      values: m.historia.map((h) => h[CLAVE_ERROR_C2[criterio]])
    }));

  return (
    <div className="comparative-report">
      <div className="kpi-grid">
        <div className="kpi-card highlight-ch2">
          <span className="kpi-label">Menor radio espectral</span>
          <div className="kpi-value">{informe.metodo_menor_radio || 'N/A'}</div>
          <span className="kpi-sub">Menor ρ(T): converge más rápido</span>
        </div>
        {['abs', 'rel', 'cond'].map((c) => (
          <div key={c} className="kpi-card">
            <span className="kpi-label">Más rápido · error {NOMBRE_ERROR[c].toLowerCase()}</span>
            <div className="kpi-value">{informe[`ganador_${c}`] || 'Ninguno'}</div>
            <span className="kpi-sub">Menos iteraciones parando con ese error</span>
          </div>
        ))}
      </div>

      <div className="glass-card">
        <div className="table-header-bar">
          <h3>Gráfica comparativa (Jacobi, Gauss-Seidel y SOR)</h3>
          <div className="segmented-control compact" role="radiogroup" aria-label="Criterio de la gráfica">
            {['rel', 'abs', 'cond'].map((c) => (
              <button
                key={c}
                type="button"
                role="radio"
                aria-checked={criterio === c}
                className={`segment-btn ${criterio === c ? 'active' : ''}`}
                onClick={() => setCriterioGrafica(c)}
              >
                {NOMBRE_ERROR[c]}
              </button>
            ))}
          </div>
        </div>
        <ConvergenceChart series={seriesGrafica} titulo={`Los tres métodos parando con error ${NOMBRE_ERROR[criterio].toLowerCase()}`} />
      </div>

      <div className="glass-card">
        <h3 style={{ marginBottom: '6px' }}>Comparación ante los tres tipos de error</h3>
        <p className="texto-ayuda">
          Cada método se corrió tres veces, deteniéndose con cada criterio. Cada celda muestra el estado, las iteraciones y el error final.
        </p>
        <TablaCriterios metodosPorCriterio={porCriterio} />
      </div>

      <div className="glass-card">
        <h3 style={{ marginBottom: '10px' }}>Informe</h3>
        <p className="texto-informe">{informe.conclusion_general}</p>
        <p className="texto-ayuda">
          κ(A) = {fmtNum(propiedades_matriz.condicion_matriz, 4)} · det(A) = {fmtSci(propiedades_matriz.determinante)} ·{' '}
          {propiedades_matriz.es_edd ? 'A es diagonalmente dominante' : 'A no es diagonalmente dominante'}
        </p>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Método</th>
                <th>Radio espectral ρ(T)</th>
                <th>¿Puede converger? (ρ &lt; 1)</th>
                <th>Estado</th>
                <th>Iteraciones</th>
                <th>Error absoluto</th>
                <th>Error relativo</th>
                <th>Error de condición ‖b − Ax‖</th>
              </tr>
            </thead>
            <tbody>
              {metodos.map((m, idx) => (
                <tr key={idx}>
                  <td><strong>{m.metodo}</strong></td>
                  <td className="mono">{fmtNum(m.radio_espectral, 6)}</td>
                  <td>
                    <span className={`status-pill ${m.puede_converger ? 'ok' : 'warn'}`}>
                      {m.puede_converger ? 'Sí (ρ < 1)' : 'No (ρ ≥ 1)'}
                    </span>
                  </td>
                  <td title={m.mensaje || ''}>
                    <span className={`status-pill ${m.convergio ? 'ok' : 'warn'}`}>{ETIQUETA_ESTADO[m.estado] || m.estado}</span>
                  </td>
                  <td className="mono">{m.iteraciones_usadas}</td>
                  <td className="mono">{fmtSci(m.error_abs)}</td>
                  <td className="mono">{fmtSci(m.error_rel)}</td>
                  <td className="mono">{fmtSci(m.error_cond)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

window.Chapter2 = Chapter2;
