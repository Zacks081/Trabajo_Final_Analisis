// ============================================================================
// CAPÍTULO 1: ECUACIONES NO LINEALES f(x) = 0
// Métodos: Bisección, Regla Falsa, Punto Fijo, Newton-Raphson, Secante,
//          Raíces Múltiples y comparación de todos los métodos
// ============================================================================

const { useState, useEffect, useCallback, useRef } = React;

const METODOS_CAP1 = [
  { id: 'biseccion', nombre: 'Bisección', req: 'Intervalo [a, b] con cambio de signo' },
  { id: 'regla_falsa', nombre: 'Regla Falsa', req: 'Intervalo [a, b] con cambio de signo' },
  { id: 'punto_fijo', nombre: 'Punto Fijo', req: 'Función g(x) tal que x = g(x)' },
  { id: 'newton', nombre: 'Newton-Raphson', req: 'Valor inicial x₀ (la derivada se calcula sola)' },
  { id: 'secante', nombre: 'Secante', req: 'Valores iniciales x₀ y x₁' },
  { id: 'raices_multiples', nombre: 'Raíces Múltiples', req: 'Valor inicial x₀ y multiplicidad m o f\'\'(x)' },
  { id: 'comparar', nombre: 'Comparar todos', req: 'Compara todos los métodos con error absoluto, relativo y de condición' }
];

const EJEMPLOS_CAP1 = [
  { nombre: 'exp(-x) - x', fx: 'exp(-x) - x', gx: 'exp(-x)', a: '0', b: '1', x0: '0.5', x1: '0.6', m: '1' },
  { nombre: 'ln(sin(x)^2 + 1) - 1/2', fx: 'ln(sin(x)^2 + 1) - 1/2', gx: 'ln(sin(x)^2 + 1) - 1/2 + x', a: '0', b: '1', x0: '0.5', x1: '0.8', m: '1' },
  { nombre: 'Raíz doble (x-1)²(x+2)', fx: '(x - 1)^2 * (x + 2)', gx: 'x - ((x - 1)^2 * (x + 2)) / 6', a: '0', b: '2', x0: '1.4', x1: '1.3', m: '2' },
  { nombre: 'x³ + 4x² - 10', fx: 'x^3 + 4*x^2 - 10', gx: 'sqrt(10 / (x + 4))', a: '1', b: '2', x0: '1.5', x1: '1.2', m: '1' }
];

const CLAVE_ERROR = { abs: 'error_abs', rel: 'error_rel', cond: 'error_cond' };

function Chapter1({ apiUrl, notify }) {
  const [metodo, setMetodo] = useState('biseccion');
  const [fx, setFx] = useState('ln(sin(x)^2 + 1) - 1/2');
  const [dfx, setDfx] = useState('');
  const [ddfx, setDdfx] = useState('');
  const [usarDerivadaManual, setUsarDerivadaManual] = useState(false);
  const [gx, setGx] = useState('ln(sin(x)^2 + 1) - 1/2 + x');
  // f(x) para la que se eligió la g(x) actual; si f cambia, se propone una g nueva
  const [gPara, setGPara] = useState('ln(sin(x)^2 + 1) - 1/2');

  const [a, setA] = useState('0');
  const [b, setB] = useState('1');
  const [x0, setX0] = useState('0.5');
  const [x1, setX1] = useState('0.8');
  const [varianteRM, setVarianteRM] = useState('2');
  const [multiplicidad, setMultiplicidad] = useState('2');

  const [tol, setTol] = useState('1e-7');
  const [maxIter, setMaxIter] = useState('100');
  const [tipoError, setTipoError] = useState('rel');

  const [analisis, setAnalisis] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [comparacion, setComparacion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [mostrarGuiaDatos, setMostrarGuiaDatos] = useState(false);
  const inputFx = useRef(null);

  const analizarFuncion = useCallback(async (exprFx, valX0) => {
    if (!exprFx || !exprFx.trim()) return;
    try {
      const resp = await fetch(`${apiUrl}/analizar-funcion/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fx: exprFx, x0: valX0 })
      });
      const data = await resp.json();
      if (data.ok) {
        setAnalisis(data);
        if (!usarDerivadaManual) {
          setDfx(data.dfx || '');
          setDdfx(data.ddfx || '');
        }
      } else {
        setAnalisis({ ok: false, error: data.error });
      }
    } catch (err) {
      // Silencioso mientras se escribe
    }
  }, [apiUrl, usarDerivadaManual]);

  useEffect(() => {
    const timer = setTimeout(() => analizarFuncion(fx, x0), 300);
    return () => clearTimeout(timer);
  }, [fx, x0, analizarFuncion]);

  // Si f(x) cambió y la g(x) actual era de otra función, proponer la mejor sugerencia
  useEffect(() => {
    if (!analisis || !analisis.ok || !analisis.candidatas_g || analisis.candidatas_g.length === 0) return;
    if (gPara === fx) return;
    const mejor = analisis.candidatas_g.find((c) => c.converge) || analisis.candidatas_g[0];
    setGx(mejor.expr);
    setGPara(fx);
  }, [analisis]);

  const ejecutar = async (e) => {
    if (e) e.preventDefault();
    setCargando(true);
    setErrorMsg(null);

    try {
      const url = metodo === 'comparar' ? `${apiUrl}/capitulo-1/comparar/` : `${apiUrl}/capitulo-1/ejecutar/`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metodo,
          fx,
          dfx: usarDerivadaManual ? dfx : '',
          ddfx: usarDerivadaManual ? ddfx : '',
          gx,
          a,
          b,
          x0,
          x1,
          variante: parseInt(varianteRM, 10),
          m: multiplicidad,
          tol,
          max_iter: maxIter,
          tipo_error: tipoError
        })
      });
      const data = await resp.json();
      if (!data.ok) {
        setErrorMsg(data.error || 'Error al ejecutar el método.');
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

  const cambiarMetodo = (id) => {
    setMetodo(id);
    setErrorMsg(null);
    setResultado(null);
  };

  const cargarEjemplo = (ej) => {
    setFx(ej.fx);
    setGx(ej.gx);
    setGPara(ej.fx);
    setA(ej.a);
    setB(ej.b);
    setX0(ej.x0);
    setX1(ej.x1);
    setMultiplicidad(ej.m);
    setErrorMsg(null);
  };

  // Inserta la función donde está el cursor (o al final si el campo no tiene el foco)
  const insertarToken = (token) => {
    const el = inputFx.current;
    const ini = el && document.activeElement === el ? el.selectionStart : fx.length;
    const fin = el && document.activeElement === el ? el.selectionEnd : fx.length;
    const nuevo = fx.slice(0, ini) + token + fx.slice(fin);
    setFx(nuevo);
    requestAnimationFrame(() => {
      if (!el) return;
      el.focus();
      el.setSelectionRange(ini + token.length, ini + token.length);
    });
  };

  const exportarCSV = () => {
    if (!resultado || !resultado.iteraciones || !resultado.iteraciones.length) return;
    const cols = resultado.columnas || [];
    const header = cols.map((c) => c.label).join(',');
    const rows = resultado.iteraciones.map((row) => cols.map((c) => row[c.key] ?? '').join(','));
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `cap1_${metodo}_iteraciones.csv`;
    link.click();
  };

  const infoMetodoActual = METODOS_CAP1.find((m) => m.id === metodo) || METODOS_CAP1[0];

  return (
    <div className="chapter-view">
      <div className="chapter-header">
        <div>
          <h1 className="chapter-title">
            Capítulo 1 · Ecuaciones no lineales <MathTex tex="f(x) = 0" />
          </h1>
          <p className="chapter-subtitle">{infoMetodoActual.req}</p>
        </div>
        <button type="button" className="btn-secondary" onClick={() => setMostrarGuiaDatos((v) => !v)}>
          {mostrarGuiaDatos ? 'Ocultar ayuda' : '? Cómo ingresar datos'}
        </button>
      </div>

      {mostrarGuiaDatos && (
        <div className="glass-card help-banner">
          <div className="help-banner-header">
            <strong>Cómo ingresar los datos · Capítulo 1</strong>
            <button type="button" className="btn-ghost" onClick={() => setMostrarGuiaDatos(false)} aria-label="Cerrar ayuda">✕</button>
          </div>
          <div className="help-banner-grid">
            <div>
              <h4>Funciones</h4>
              <p>
                Usa <code>x</code> como variable. Potencias con <code>^</code> o <code>**</code> y funciones como <code>sin(x)</code>, <code>cos(x)</code>, <code>exp(x)</code>, <code>ln(x)</code>, <code>sqrt(x)</code>. En los campos numéricos puedes escribir <code>pi/2</code> o <code>1e-7</code>.
              </p>
            </div>
            <div>
              <h4>Derivadas</h4>
              <p>
                <MathTex tex="f'(x)" /> y <MathTex tex="f''(x)" /> se calculan solas. En punto fijo puedes elegir una de las <MathTex tex="g(x)" /> sugeridas con un clic.
              </p>
            </div>
            <div>
              <h4>Tipos de error</h4>
              <p>
                Relativo <MathTex tex="|x_i-x_{i-1}|/|x_i|" />, absoluto <MathTex tex="|x_i-x_{i-1}|" /> o de condición <MathTex tex="|f(x_i)|" />.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="method-tabs" role="tablist">
        {METODOS_CAP1.map((m) => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={metodo === m.id}
            className={`method-tab ${metodo === m.id ? 'active ch1' : ''} ${m.id === 'comparar' ? 'compare-tab' : ''}`}
            onClick={() => cambiarMetodo(m.id)}
          >
            {m.nombre}
          </button>
        ))}
      </div>

      <div className="preset-bar">
        <span className="preset-label">Ejemplos:</span>
        {EJEMPLOS_CAP1.map((ej, idx) => (
          <button key={idx} type="button" className="preset-chip" onClick={() => cargarEjemplo(ej)}>
            {ej.nombre}
          </button>
        ))}
      </div>

      <div className="workspace-stack">
        <form className="glass-card input-panel" onSubmit={ejecutar}>
          <div className="panel-title-row">
            <h3>Datos de entrada · {infoMetodoActual.nombre}</h3>
            <span className="badge badge-ch1">Capítulo 1</span>
          </div>

          <div className="input-grid-layout">
            {/* Columna 1: función y g(x) */}
            <div className="input-column">
              <div className="form-group">
                <label className="form-label" htmlFor="c1-fx">
                  <span>Función <MathTex tex="f(x)" /></span>
                  <span className="label-hint">variable x</span>
                </label>
                <input
                  id="c1-fx"
                  ref={inputFx}
                  type="text"
                  className="form-input mono"
                  value={fx}
                  onChange={(e) => setFx(e.target.value)}
                  placeholder="Ej: exp(-x) - x"
                  spellCheck={false}
                  autoComplete="off"
                  required
                />
                <div className="token-bar">
                  {['sin(x)', 'cos(x)', 'exp(x)', 'ln(x)', 'sqrt(x)', 'x^2', 'pi'].map((tok) => (
                    <button key={tok} type="button" className="token-btn" onClick={() => insertarToken(tok)}>
                      {tok}
                    </button>
                  ))}
                </div>
              </div>

              {(metodo === 'punto_fijo' || metodo === 'comparar') && (
                <div className="form-group">
                  <label className="form-label" htmlFor="c1-gx">
                    <span>Función <MathTex tex="g(x)" /> (punto fijo)</span>
                    <span className="label-hint">x = g(x)</span>
                  </label>
                  <input
                    id="c1-gx"
                    type="text"
                    className="form-input mono"
                    value={gx}
                    onChange={(e) => {
                      setGx(e.target.value);
                      setGPara(fx);
                    }}
                    spellCheck={false}
                    autoComplete="off"
                  />
                  {analisis?.candidatas_g && analisis.candidatas_g.length > 0 && (
                    <div className="gx-chips-row">
                      {analisis.candidatas_g.map((cand, i) => (
                        <button
                          key={i}
                          type="button"
                          className={`gx-chip ${cand.converge ? 'ok' : ''} ${gx === cand.expr ? 'selected' : ''}`}
                          onClick={() => {
                            setGx(cand.expr);
                            setGPara(fx);
                          }}
                          title={cand.descripcion}
                        >
                          <span>g(x) = {cand.expr}</span>
                          {cand.dg_x0 !== null && cand.dg_x0 !== undefined && (
                            <small>({cand.converge ? '✓' : '⚠'} |g'(x₀)| = {cand.dg_x0.toFixed(2)})</small>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Columna 2: intervalo, valores iniciales y criterio de parada */}
            <div className="input-column">
              <div className="form-row-4">
                {(metodo === 'biseccion' || metodo === 'regla_falsa' || metodo === 'comparar') && (
                  <>
                    <div className="form-group">
                      <label className="form-label" htmlFor="c1-a">Extremo a</label>
                      <input id="c1-a" type="text" inputMode="decimal" className="form-input mono" value={a} onChange={(e) => setA(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="c1-b">Extremo b</label>
                      <input id="c1-b" type="text" inputMode="decimal" className="form-input mono" value={b} onChange={(e) => setB(e.target.value)} required />
                    </div>
                  </>
                )}

                {(metodo === 'punto_fijo' || metodo === 'newton' || metodo === 'secante' || metodo === 'raices_multiples' || metodo === 'comparar') && (
                  <div className="form-group">
                    <label className="form-label" htmlFor="c1-x0">Valor inicial x₀</label>
                    <input id="c1-x0" type="text" inputMode="decimal" className="form-input mono" value={x0} onChange={(e) => setX0(e.target.value)} required />
                  </div>
                )}

                {(metodo === 'secante' || metodo === 'comparar') && (
                  <div className="form-group">
                    <label className="form-label" htmlFor="c1-x1">Valor x₁ (secante)</label>
                    <input id="c1-x1" type="text" inputMode="decimal" className="form-input mono" value={x1} onChange={(e) => setX1(e.target.value)} required />
                  </div>
                )}
              </div>

              {(metodo === 'raices_multiples' || metodo === 'comparar') && (
                <div className="form-row-2">
                  {metodo === 'raices_multiples' && (
                    <div className="form-group">
                      <label className="form-label" htmlFor="c1-variante">Variante de raíces múltiples</label>
                      <select id="c1-variante" className="form-select" value={varianteRM} onChange={(e) => setVarianteRM(e.target.value)}>
                        <option value="2">Con segunda derivada f''(x)</option>
                        <option value="1">Con multiplicidad m</option>
                      </select>
                    </div>
                  )}
                  {(varianteRM === '1' || metodo === 'comparar') && (
                    <div className="form-group">
                      <label className="form-label" htmlFor="c1-m">Multiplicidad m</label>
                      <input id="c1-m" type="text" inputMode="numeric" className="form-input mono" value={multiplicidad} onChange={(e) => setMultiplicidad(e.target.value)} />
                    </div>
                  )}
                </div>
              )}

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

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="c1-tol">Tolerancia</label>
                  <input id="c1-tol" type="text" inputMode="decimal" className="form-input mono" value={tol} onChange={(e) => setTol(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="c1-niter">Máx. iteraciones</label>
                  <input id="c1-niter" type="number" min="1" max="2000" className="form-input mono" value={maxIter} onChange={(e) => setMaxIter(e.target.value)} required />
                </div>
              </div>
            </div>
          </div>

          {analisis && analisis.ok && (
            <div className="symbolic-compact-bar">
              <div className="symbolic-items-inline">
                <span className="symbolic-inline-item">
                  <span className="symbolic-tag">f(x) =</span>
                  <MathTex tex={analisis.fx_latex} />
                </span>
                <span className="symbolic-inline-item">
                  <span className="symbolic-tag">f'(x) =</span>
                  <MathTex tex={analisis.dfx_latex} />
                </span>
                {(metodo === 'raices_multiples' || metodo === 'comparar') && (
                  <span className="symbolic-inline-item">
                    <span className="symbolic-tag">f''(x) =</span>
                    <MathTex tex={analisis.ddfx_latex} />
                  </span>
                )}
              </div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={usarDerivadaManual}
                  onChange={(e) => {
                    setUsarDerivadaManual(e.target.checked);
                    if (!e.target.checked && analisis) {
                      setDfx(analisis.dfx || '');
                      setDdfx(analisis.ddfx || '');
                    }
                  }}
                />
                <span>Escribir la derivada a mano</span>
              </label>
            </div>
          )}

          {analisis && analisis.ok === false && (
            <div className="alert-box alert-warning">{analisis.error}</div>
          )}

          {usarDerivadaManual && (
            <div className="form-row-2">
              <div className="form-group">
                <label className="form-label" htmlFor="c1-df">Primera derivada f'(x)</label>
                <input id="c1-df" type="text" className="form-input mono" value={dfx} onChange={(e) => setDfx(e.target.value)} spellCheck={false} />
              </div>
              {(metodo === 'raices_multiples' || metodo === 'comparar') && (
                <div className="form-group">
                  <label className="form-label" htmlFor="c1-d2f">Segunda derivada f''(x)</label>
                  <input id="c1-d2f" type="text" className="form-input mono" value={ddfx} onChange={(e) => setDdfx(e.target.value)} spellCheck={false} />
                </div>
              )}
            </div>
          )}

          {errorMsg && (
            <div className="alert-box alert-error" role="alert">
              <strong>Revisa los datos:</strong> {errorMsg}
            </div>
          )}

          <div className="submit-bar">
            <button type="submit" className="btn-primary btn-ch1" disabled={cargando}>
              {cargando
                ? 'Calculando…'
                : metodo === 'comparar'
                ? 'Comparar todos los métodos'
                : `Calcular con ${infoMetodoActual.nombre}`}
            </button>
          </div>
        </form>

        <div className="results-panel">
          {metodo === 'comparar' ? (
            <ComparativeReportCap1 comparacion={comparacion} />
          ) : resultado ? (
            <>
              <div className="kpi-grid">
                <div className="kpi-card highlight-ch1">
                  <span className="kpi-label">Raíz aproximada (x*)</span>
                  <div className="kpi-value mono">{fmtNum(resultado.raiz, 10)}</div>
                  <span className="kpi-sub">{ETIQUETA_ESTADO[resultado.estado] || resultado.estado}</span>
                </div>
                <div className="kpi-card">
                  <span className="kpi-label">f(x*)</span>
                  <div className="kpi-value mono">{fmtSci(resultado.f_raiz)}</div>
                  <span className="kpi-sub">Su valor absoluto es el error de condición</span>
                </div>
                <div className="kpi-card">
                  <span className="kpi-label">Iteraciones</span>
                  <div className="kpi-value mono">{resultado.iteraciones_usadas ?? '—'}</div>
                  <span className="kpi-sub">{resultado.orden_estimado ? `Orden estimado: p ≈ ${resultado.orden_estimado}` : 'Orden estimado: —'}</span>
                </div>
                <div className="kpi-card">
                  <span className="kpi-label">Error final ({NOMBRE_ERROR[tipoError].toLowerCase()})</span>
                  <div className="kpi-value mono">{fmtSci(resultado.error_final)}</div>
                  <span className="kpi-sub">Tolerancia: {tol}</span>
                </div>
              </div>

              <EstadoMetodo
                exito={resultado.convergio}
                estado={resultado.estado}
                mensaje={resultado.mensaje}
                avisos={resultado.advertencia ? [resultado.advertencia] : []}
              />

              <div className="charts-row-2">
                <FunctionChart
                  curva={resultado.curva}
                  raiz={resultado.raiz}
                  pasosAnimacion={resultado.pasos_animacion}
                  titulo={`Gráfica de f(x) · ${resultado.metodo}`}
                />

                {resultado.iteraciones && resultado.iteraciones.length > 0 && (
                  <ConvergenceChart
                    series={[
                      { name: 'Error relativo', color: '#00f5d4', values: resultado.iteraciones.map((r) => r.error_rel) },
                      { name: 'Error absoluto', color: '#7c5cff', values: resultado.iteraciones.map((r) => r.error_abs) },
                      { name: 'Condición |f(x)|', color: '#ffbe0b', values: resultado.iteraciones.map((r) => r.error_cond) }
                    ]}
                    titulo="Convergencia de los errores"
                  />
                )}
              </div>

              {resultado.iteraciones && resultado.iteraciones.length > 0 && (
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
                          {(resultado.columnas || []).map((col) => (
                            <th key={col.key}>{col.label}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {resultado.iteraciones.map((row, idx) => (
                          <tr key={idx}>
                            {(resultado.columnas || []).map((col) => {
                              const val = row[col.key];
                              let texto;
                              if (col.label === 'i') texto = String(val);
                              else if (col.key.startsWith('error_')) texto = fmtSci(val);
                              else texto = fmtNum(val, 8);
                              return (
                                <td key={col.key} className="mono">{texto}</td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ComparativeReportCap1({ comparacion }) {
  const [criterioGrafica, setCriterioGrafica] = useState(null);

  if (!comparacion) {
    return (
      <div className="glass-card">
        <p style={{ color: 'var(--text-secondary)' }}>
          Presiona <strong>"Comparar todos los métodos"</strong> para correr cada método con error absoluto, relativo y de condición.
        </p>
      </div>
    );
  }

  const { metodos = [], metodos_por_criterio: porCriterio = {}, informe = {} } = comparacion;
  const criterio = criterioGrafica || comparacion.tipo_error || 'rel';
  const colores = ['#00f5d4', '#7c5cff', '#ffbe0b', '#ff5c8a', '#38bdf8', '#a3e635', '#f97316'];

  // La gráfica usa las corridas que se detuvieron con el criterio elegido
  const seriesGrafica = (porCriterio[criterio] || [])
    .filter((m) => m.historia && m.historia.length > 0)
    .map((m, i) => ({
      name: m.metodo,
      color: colores[i % colores.length],
      values: m.historia.map((h) => h[CLAVE_ERROR[criterio]])
    }));

  return (
    <div className="comparative-report">
      <div className="kpi-grid">
        {['abs', 'rel', 'cond'].map((c, i) => (
          <div key={c} className={`kpi-card ${i === 0 ? 'highlight-ch1' : ''}`}>
            <span className="kpi-label">Más rápido · error {NOMBRE_ERROR[c].toLowerCase()}</span>
            <div className="kpi-value">{informe[`ganador_${c}`] || 'Ninguno'}</div>
            <span className="kpi-sub">Menos iteraciones parando con ese error</span>
          </div>
        ))}
        <div className="kpi-card">
          <span className="kpi-label">Criterio de la tabla detallada</span>
          <div className="kpi-value">{NOMBRE_ERROR[comparacion.tipo_error]}</div>
          <span className="kpi-sub">Tolerancia: {comparacion.tolerancia}</span>
        </div>
      </div>

      <div className="glass-card">
        <div className="table-header-bar">
          <h3>Gráfica comparativa de convergencia</h3>
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
        <ConvergenceChart series={seriesGrafica} titulo={`Todos los métodos parando con error ${NOMBRE_ERROR[criterio].toLowerCase()}`} />
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
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Método</th>
                <th>Estado</th>
                <th>Iteraciones</th>
                <th>Raíz aproximada</th>
                <th>Error absoluto</th>
                <th>Error relativo</th>
                <th>Error de condición |f(x*)|</th>
              </tr>
            </thead>
            <tbody>
              {metodos.map((m, idx) => (
                <tr key={idx}>
                  <td><strong>{m.metodo}</strong></td>
                  <td title={m.mensaje || ''}>
                    <span className={`status-pill ${m.convergio ? 'ok' : 'warn'}`}>
                      {ETIQUETA_ESTADO[m.estado] || m.estado}
                    </span>
                  </td>
                  <td className="mono">{m.iteraciones_usadas ?? '—'}</td>
                  <td className="mono">{fmtNum(m.raiz, 9)}</td>
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

window.Chapter1 = Chapter1;
