// ============================================================================
// CAPÍTULO 3: INTERPOLACIÓN (HASTA 10 DATOS)
// Métodos: Vandermonde, Newton, Lagrange, Splines (grado 1, 2 y 3) y comparación
// ============================================================================

const { useState, useEffect } = React;

const METODOS_CAP3 = [
  { id: 'vandermonde', nombre: 'Vandermonde', desc: 'Sistema V·a = y para hallar P(x) en la base 1, x, x², …' },
  { id: 'newton', nombre: 'Newton interpolante', desc: 'Polinomio a partir de la tabla de diferencias divididas' },
  { id: 'lagrange', nombre: 'Lagrange', desc: 'Combinación de los polinomios base Lᵢ(x)' },
  { id: 'spline_lineal', nombre: 'Spline lineal', desc: 'Trazador lineal por tramos (grado 1)' },
  { id: 'spline_cuadratico', nombre: 'Spline cuadrático', desc: 'Trazador cuadrático con primera derivada continua (grado 2)' },
  { id: 'spline_cubico', nombre: 'Spline cúbico', desc: 'Trazador cúbico natural con primera y segunda derivada continuas (grado 3)' },
  { id: 'comparar', nombre: 'Comparar todos', desc: 'Compara los 6 métodos y, si hay reserva, mide su error en los datos reservados' }
];

const EJEMPLOS_CAP3 = [
  {
    nombre: 'Exponencial (6 datos)',
    puntos: [
      { x: '1', y: '2.718282' },
      { x: '1.5', y: '4.481689' },
      { x: '2', y: '7.389056' },
      { x: '2.5', y: '12.182494' },
      { x: '3', y: '20.085537' },
      { x: '3.5', y: '33.115452' }
    ],
    xEval: '2.25',
    fxReal: 'exp(x)'
  },
  {
    nombre: 'Ejemplo de clase (4 datos)',
    puntos: [
      { x: '19', y: '5.8' },
      { x: '25', y: '2.1' },
      { x: '29', y: '-1.3' },
      { x: '33', y: '9.2' }
    ],
    xEval: '20',
    fxReal: ''
  },
  {
    nombre: 'Función de Runge (8 datos)',
    puntos: [
      { x: '-3', y: '0.1' },
      { x: '-2.1', y: '0.1848' },
      { x: '-1.2', y: '0.4098' },
      { x: '-0.4', y: '0.8621' },
      { x: '0.4', y: '0.8621' },
      { x: '1.2', y: '0.4098' },
      { x: '2.1', y: '0.1848' },
      { x: '3', y: '0.1' }
    ],
    xEval: '0',
    fxReal: '1 / (1 + x^2)'
  },
  {
    nombre: 'Seno (10 datos)',
    puntos: [
      { x: '0', y: '0' },
      { x: '1', y: '0.8415' },
      { x: '2', y: '0.9093' },
      { x: '3', y: '0.1411' },
      { x: '4', y: '-0.7568' },
      { x: '5', y: '-0.9589' },
      { x: '6', y: '-0.2794' },
      { x: '7', y: '0.657' },
      { x: '8', y: '0.9894' },
      { x: '9', y: '0.4121' }
    ],
    xEval: '4.5',
    fxReal: 'sin(x)'
  }
];

const vacioC3 = (v) => v === null || v === undefined || String(v).trim() === '';

function puntosATexto(pts) {
  return {
    x: pts.map((p) => p.x).join(' '),
    y: pts.map((p) => p.y).join(' ')
  };
}

// Mismo cálculo que el backend: k = round(n·p), al menos 1 y dejando 2 puntos para construir
function puntosReservados(n, pct) {
  if (!pct || n < 4) return 0;
  return Math.min(Math.max(1, Math.round((n * pct) / 100)), n - 2);
}

function Chapter3({ apiUrl, notify }) {
  const [metodo, setMetodo] = useState('newton');
  const [modoEntrada, setModoEntrada] = useState('tabla');
  const [puntos, setPuntos] = useState(EJEMPLOS_CAP3[0].puntos);
  const [textoX, setTextoX] = useState(puntosATexto(EJEMPLOS_CAP3[0].puntos).x);
  const [textoY, setTextoY] = useState(puntosATexto(EJEMPLOS_CAP3[0].puntos).y);

  const [porcentajeReserva, setPorcentajeReserva] = useState(0);
  const [guardados, setGuardados] = useState([]);
  const [xEval, setXEval] = useState('2.25');
  const [fxReal, setFxReal] = useState('exp(x)');

  const [resultado, setResultado] = useState(null);
  const [comparacion, setComparacion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [mostrarGuiaDatos, setMostrarGuiaDatos] = useState(false);
  const [marcarVacias, setMarcarVacias] = useState(false);

  const nPuntos = modoEntrada === 'vectores' ? textoX.split(/[\s,;]+/).filter(Boolean).length : puntos.length;
  const kReserva = puntosReservados(nPuntos, porcentajeReserva);
  const reservaPosible = nPuntos >= 4;

  // Con menos de 4 puntos no se puede reservar: volver a usar todos
  useEffect(() => {
    if (!reservaPosible && porcentajeReserva !== 0) setPorcentajeReserva(0);
  }, [reservaPosible]);

  const actualizarPuntos = (nuevosPuntos) => {
    const limitados = nuevosPuntos.slice(0, 10);
    setPuntos(limitados);
    const txt = puntosATexto(limitados);
    setTextoX(txt.x);
    setTextoY(txt.y);
  };

  const cambiarCeldaPunto = (idx, campo, valor) => {
    const copia = puntos.map((p) => ({ ...p }));
    copia[idx][campo] = valor;
    actualizarPuntos(copia);
  };

  const agregarPunto = () => {
    if (puntos.length >= 10) return;
    const ultimoX = parseFloat(puntos[puntos.length - 1]?.x) || 0;
    actualizarPuntos([...puntos, { x: String(+(ultimoX + 1).toFixed(2)), y: '' }]);
  };

  const eliminarPunto = (idx) => {
    if (puntos.length <= 2) return;
    actualizarPuntos(puntos.filter((_, i) => i !== idx));
  };

  const cargarGuardados = async () => {
    try {
      const resp = await fetch(`${apiUrl}/capitulo-3/almacenamiento/`);
      const data = await resp.json();
      if (data.ok) setGuardados(data.datasets || []);
    } catch (e) {
      // Sin conexión: la lista queda vacía
    }
  };

  useEffect(() => {
    cargarGuardados();
  }, []);

  const datosActuales = () => ({
    x: modoEntrada === 'vectores' ? textoX : puntos.map((p) => String(p.x)),
    y: modoEntrada === 'vectores' ? textoY : puntos.map((p) => String(p.y))
  });

  const guardarDatos = async () => {
    const pct = porcentajeReserva > 0 ? porcentajeReserva : 20;
    try {
      const resp = await fetch(`${apiUrl}/capitulo-3/almacenamiento/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: `${nPuntos} puntos (${pct} % reservado)`, porcentaje_almacenado: pct, ...datosActuales() })
      });
      const data = await resp.json();
      if (data.ok) {
        setGuardados(data.datasets || []);
        notify(`Datos guardados (${pct} % reservado)`, 'success');
      } else {
        notify(data.error || 'No se pudieron guardar los datos.', 'warn');
      }
    } catch (e) {
      notify('No se pudieron guardar los datos.', 'warn');
    }
  };

  const borrarGuardado = async (id) => {
    try {
      const resp = await fetch(`${apiUrl}/capitulo-3/almacenamiento/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      const data = await resp.json();
      if (data.ok) setGuardados(data.datasets || []);
    } catch (e) {
      notify('No se pudo borrar el registro.', 'warn');
    }
  };

  const cargarEjemplo = (ej) => {
    actualizarPuntos(ej.puntos);
    setXEval(ej.xEval);
    setFxReal(ej.fxReal);
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

    if (modoEntrada === 'tabla' && puntos.some((p) => vacioC3(p.x) || vacioC3(p.y))) {
      setMarcarVacias(true);
      setErrorMsg('Hay casillas vacías en los puntos (marcadas en rojo). Escribe x e y en cada punto o elimínalo.');
      return;
    }
    setMarcarVacias(false);

    setCargando(true);
    try {
      const url = metodo === 'comparar' ? `${apiUrl}/capitulo-3/comparar/` : `${apiUrl}/capitulo-3/ejecutar/`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metodo,
          ...datosActuales(),
          porcentaje_reserva: porcentajeReserva,
          x_eval: xEval,
          fx_real: fxReal
        })
      });
      const data = await resp.json();
      if (!data.ok) {
        setErrorMsg(data.error || 'Error en el cálculo de interpolación.');
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

  const infoMetodoActual = METODOS_CAP3.find((m) => m.id === metodo) || METODOS_CAP3[0];

  // Curvas de la gráfica: polinomio y, si se dio, la función real como referencia
  const curvasResultado = resultado
    ? [
        { name: resultado.metodo, color: '#00f5d4', x: resultado.curva?.x || [], y: resultado.curva?.y || [] },
        ...(resultado.curva?.y_real
          ? [{ name: `f(x) = ${fxReal}`, color: '#94a3b8', x: resultado.curva.x, y: resultado.curva.y_real, dashed: true, referencia: true }]
          : [])
      ]
    : [];

  return (
    <div className="chapter-view">
      <div className="chapter-header">
        <div>
          <h1 className="chapter-title">
            Capítulo 3 · Interpolación <MathTex tex="P(x),\, S(x)" />
          </h1>
          <p className="chapter-subtitle">{infoMetodoActual.desc}</p>
        </div>
        <button type="button" className="btn-secondary" onClick={() => setMostrarGuiaDatos((v) => !v)}>
          {mostrarGuiaDatos ? 'Ocultar ayuda' : '? Cómo ingresar datos'}
        </button>
      </div>

      {mostrarGuiaDatos && (
        <div className="glass-card help-banner">
          <div className="help-banner-header">
            <strong>Cómo ingresar los datos · Capítulo 3 (hasta 10 puntos)</strong>
            <button type="button" className="btn-ghost" onClick={() => setMostrarGuiaDatos(false)} aria-label="Cerrar ayuda">✕</button>
          </div>
          <div className="help-banner-grid">
            <div>
              <h4>Hasta 10 puntos</h4>
              <p>
                Usa las casillas <MathTex tex="(x_i, y_i)" /> o el modo vectores, escribiendo <code>X</code> y <code>Y</code> separados por espacios. Los valores de <MathTex tex="x_i" /> no se pueden repetir.
              </p>
            </div>
            <div>
              <h4>Reservar el 20 % o 30 %</h4>
              <p>
                Los puntos reservados no se usan para construir el polinomio: se guardan para medir el error de interpolación en ellos. Con 0 % se usan todos los puntos. Se necesitan al menos 4 puntos para reservar.
              </p>
            </div>
            <div>
              <h4>Polinomio solución</h4>
              <p>
                Se muestra el polinomio <MathTex tex="P(x)" /> o, en los splines, la ecuación de cada tramo <MathTex tex="S_i(x)" />.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="method-tabs" role="tablist">
        {METODOS_CAP3.map((m) => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={metodo === m.id}
            className={`method-tab ${metodo === m.id ? 'active ch3' : ''} ${m.id === 'comparar' ? 'compare-tab' : ''}`}
            onClick={() => cambiarMetodo(m.id)}
          >
            {m.nombre}
          </button>
        ))}
      </div>

      <div className="preset-bar">
        <span className="preset-label">Ejemplos:</span>
        {EJEMPLOS_CAP3.map((ej, idx) => (
          <button key={idx} type="button" className="preset-chip" onClick={() => cargarEjemplo(ej)}>
            {ej.nombre}
          </button>
        ))}
      </div>

      {guardados.length > 0 && (
        <div className="preset-bar">
          <span className="preset-label">Datos guardados:</span>
          {guardados.slice(0, 6).map((ds) => (
            <span key={ds.id} className="preset-chip highlight saved-chip">
              <button
                type="button"
                className="saved-chip-load"
                onClick={() => {
                  if (Array.isArray(ds.x) && Array.isArray(ds.y)) {
                    actualizarPuntos(ds.x.map((vx, i) => ({ x: String(vx), y: String(ds.y[i] ?? '') })));
                    setPorcentajeReserva(ds.porcentaje_almacenado >= 25 ? 30 : 20);
                  }
                }}
                title={`Guardado el ${ds.fecha}`}
              >
                {ds.nombre}
              </button>
              <button type="button" className="saved-chip-del" onClick={() => borrarGuardado(ds.id)} aria-label={`Borrar ${ds.nombre}`}>
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="workspace-stack">
        <form className="glass-card input-panel" onSubmit={ejecutar}>
          <div className="panel-title-row">
            <h3>Datos ({nPuntos}/10 puntos)</h3>
            <span className="badge badge-ch3">{infoMetodoActual.nombre}</span>
          </div>

          <div className="input-grid-layout">
            {/* Columna izquierda: modo, reserva y evaluación */}
            <div className="input-column">
              <div className="form-group">
                <span className="form-label">Modo de ingreso</span>
                <div className="segmented-control two-cols">
                  <button type="button" className={`segment-btn ${modoEntrada === 'tabla' ? 'active' : ''}`} onClick={() => setModoEntrada('tabla')}>
                    Casillas (xᵢ, yᵢ)
                  </button>
                  <button type="button" className={`segment-btn ${modoEntrada === 'vectores' ? 'active' : ''}`} onClick={() => setModoEntrada('vectores')}>
                    Vectores X / Y
                  </button>
                </div>
              </div>

              <div className="form-group">
                <span className="form-label">
                  <span>Reservar datos para validar</span>
                  <button type="button" className="token-btn" onClick={guardarDatos} title="Guardar estos puntos con su reserva">
                    Guardar datos
                  </button>
                </span>
                <div className="segmented-control" role="radiogroup" aria-label="Porcentaje reservado">
                  {[
                    { val: 0, label: '0 % (usar todos)' },
                    { val: 20, label: '20 %' },
                    { val: 30, label: '30 %' }
                  ].map((opt) => (
                    <button
                      key={opt.val}
                      type="button"
                      role="radio"
                      aria-checked={porcentajeReserva === opt.val}
                      className={`segment-btn ${porcentajeReserva === opt.val ? 'active' : ''}`}
                      onClick={() => setPorcentajeReserva(opt.val)}
                      disabled={opt.val > 0 && !reservaPosible}
                      title={opt.val > 0 && !reservaPosible ? 'Se necesitan al menos 4 puntos para reservar datos' : ''}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <span className="texto-ayuda">
                  {!reservaPosible
                    ? 'Con menos de 4 puntos se usan todos (no se puede reservar).'
                    : porcentajeReserva === 0
                    ? `Se usan los ${nPuntos} puntos para construir el polinomio.`
                    : `Se reservan ${kReserva} de ${nPuntos} puntos (${Math.round((100 * kReserva) / nPuntos)} %) y se construye con los otros ${nPuntos - kReserva}.`}
                </span>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="c3-xeval">Evaluar en x* (opcional)</label>
                  <input id="c3-xeval" type="text" inputMode="decimal" className="form-input mono" value={xEval} onChange={(e) => setXEval(e.target.value)} placeholder="Ej: 2.25" />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="c3-freal">Función real f(x) (opcional)</label>
                  <input id="c3-freal" type="text" className="form-input mono" value={fxReal} onChange={(e) => setFxReal(e.target.value)} placeholder="Ej: exp(x)" spellCheck={false} />
                </div>
              </div>
            </div>

            {/* Columna derecha: puntos */}
            <div className="input-column">
              {modoEntrada === 'tabla' ? (
                <div className="form-group">
                  <div className="form-label">
                    <span>Puntos <MathTex tex="(x_i, y_i)" /> (máximo 10)</span>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '11.5px' }}
                      onClick={agregarPunto}
                      disabled={puntos.length >= 10}
                    >
                      + Agregar punto ({puntos.length}/10)
                    </button>
                  </div>
                  <div className="points-grid-compact">
                    {puntos.map((pt, idx) => (
                      <div key={idx} className="point-compact-card">
                        <span className="pt-index mono">{idx}</span>
                        <input
                          type="text"
                          inputMode="decimal"
                          className={`form-input mono${marcarVacias && vacioC3(pt.x) ? ' cell-error' : ''}`}
                          value={pt.x}
                          onChange={(e) => cambiarCeldaPunto(idx, 'x', e.target.value)}
                          aria-label={`x${idx}`}
                          placeholder={`x${idx}`}
                        />
                        <input
                          type="text"
                          inputMode="decimal"
                          className={`form-input mono${marcarVacias && vacioC3(pt.y) ? ' cell-error' : ''}`}
                          value={pt.y}
                          onChange={(e) => cambiarCeldaPunto(idx, 'y', e.target.value)}
                          aria-label={`y${idx}`}
                          placeholder={`y${idx}`}
                        />
                        <button
                          type="button"
                          className="btn-icon-del"
                          onClick={() => eliminarPunto(idx)}
                          aria-label={`Eliminar el punto ${idx}`}
                          disabled={puntos.length <= 2}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label" htmlFor="c3-vx">Vector X (separado por espacios)</label>
                    <input id="c3-vx" type="text" className="form-input mono" value={textoX} onChange={(e) => setTextoX(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="c3-vy">Vector Y (separado por espacios)</label>
                    <input id="c3-vy" type="text" className="form-input mono" value={textoY} onChange={(e) => setTextoY(e.target.value)} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {errorMsg && (
            <div className="alert-box alert-error" role="alert">
              <strong>Revisa los datos:</strong> {errorMsg}
            </div>
          )}

          <div className="submit-bar">
            <button type="submit" className="btn-primary btn-ch3" disabled={cargando}>
              {cargando
                ? 'Calculando…'
                : metodo === 'comparar'
                ? 'Comparar los 6 métodos'
                : `Calcular con ${infoMetodoActual.nombre}`}
            </button>
          </div>
        </form>

        <div className="results-panel">
          {metodo === 'comparar' ? (
            <ComparativeReportCap3 comparacion={comparacion} fxReal={fxReal} />
          ) : resultado ? (
            <>
              <div className="kpi-grid">
                <div className="kpi-card highlight-ch3">
                  <span className="kpi-label">Método</span>
                  <div className="kpi-value">{resultado.metodo}</div>
                  <span className="kpi-sub">
                    {resultado.tramos ? `${resultado.tramos.length} tramos de grado ${resultado.grado}` : `Grado ≤ ${resultado.grado}`}
                  </span>
                </div>

                <div className="kpi-card">
                  <span className="kpi-label">Puntos usados / reservados</span>
                  <div className="kpi-value mono">
                    {resultado.n_entrenamiento} / {resultado.n_reservados}
                  </div>
                  <span className="kpi-sub">
                    {resultado.n_reservados > 0 ? `Reservado: ${resultado.porcentaje_reserva} % de los datos` : 'Se usaron todos los puntos'}
                  </span>
                </div>

                {resultado.validacion_reserva && (
                  <div className="kpi-card">
                    <span className="kpi-label">Error medio en los reservados</span>
                    <div className="kpi-value mono">{fmtSci(resultado.validacion_reserva.error_abs_medio)}</div>
                    <span className="kpi-sub">Relativo: {fmtSci(resultado.validacion_reserva.error_rel_medio)}</span>
                  </div>
                )}

                {resultado.evaluacion_punto && (
                  <div className="kpi-card">
                    <span className="kpi-label">P(x*) con x* = {resultado.evaluacion_punto.x_eval}</span>
                    <div className="kpi-value mono">{fmtNum(resultado.evaluacion_punto.y_interp, 7)}</div>
                    <span className="kpi-sub">
                      {resultado.evaluacion_punto.error_abs !== undefined
                        ? `Error frente a f(x*): ${fmtSci(resultado.evaluacion_punto.error_abs)}`
                        : resultado.evaluacion_punto.tipo === 'extrapolacion'
                        ? 'x* fuera de [x₀, xₙ]: extrapolación'
                        : 'Valor interpolado'}
                    </span>
                  </div>
                )}
              </div>

              {resultado.avisos && resultado.avisos.length > 0 && (
                <EstadoMetodo exito={true} avisos={resultado.avisos} />
              )}

              <div className="glass-card">
                <div className="polynomial-card-header">
                  <h3>{resultado.tramos ? 'Trazadores' : 'Polinomio solución'} · {resultado.metodo}</h3>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      navigator.clipboard?.writeText(resultado.polinomio_texto || '');
                      notify('Polinomio copiado', 'info');
                    }}
                  >
                    Copiar
                  </button>
                </div>

                {resultado.polinomio_latex ? (
                  <div className="polynomial-latex-box">
                    <MathTex tex={`P(x) = ${resultado.polinomio_latex}`} block />
                    <div className="polynomial-plain-code">
                      <code>P(x) = {resultado.polinomio_texto}</code>
                    </div>
                  </div>
                ) : resultado.tramos ? (
                  <div className="spline-segments-list">
                    {resultado.tramos.map((tramo) => (
                      <div key={tramo.indice} className="spline-segment-row">
                        <span className="spline-interval mono">
                          Tramo {tramo.indice}: {fmtNum(tramo.intervalo[0], 4)} ≤ x ≤ {fmtNum(tramo.intervalo[1], 4)}
                        </span>
                        <MathTex tex={`S_{${tramo.indice}}(x) = ${tramo.latex}`} />
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>

              <InterpolationChart
                puntosEntrenamiento={resultado.puntos_entrenamiento}
                puntosReservados={resultado.puntos_reservados}
                curvas={curvasResultado}
                evaluacionPunto={resultado.evaluacion_punto}
                titulo={`Gráfica · ${resultado.metodo}`}
              />

              {resultado.validacion_reserva && resultado.validacion_reserva.detalle?.length > 0 && (
                <div className="glass-card">
                  <h3 style={{ marginBottom: '10px' }}>Validación en los datos reservados</h3>
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>xᵢ reservado</th>
                          <th>yᵢ real</th>
                          <th>P(xᵢ) interpolado</th>
                          <th>Error absoluto</th>
                          <th>Error relativo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resultado.validacion_reserva.detalle.map((d, i) => (
                          <tr key={i}>
                            <td className="mono">{fmtNum(d.x, 6)}</td>
                            <td className="mono">{fmtNum(d.y_real, 8)}</td>
                            <td className="mono">{fmtNum(d.y_interpolado, 8)}</td>
                            <td className="mono">{fmtSci(d.error_abs)}</td>
                            <td className="mono">{fmtSci(d.error_rel)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {resultado.tabla_diferencias && (
                <div className="glass-card">
                  <h3 style={{ marginBottom: '10px' }}>Tabla de diferencias divididas</h3>
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>
                          {resultado.tabla_diferencias.columnas.map((c) => (
                            <th key={c}>{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {resultado.tabla_diferencias.filas.map((fila, i) => (
                          <tr key={i}>
                            {fila.map((celda, j) => (
                              <td key={j} className={`mono${j === i + 2 ? ' celda-coef' : ''}`}>
                                {j === 0 ? celda : celda === null ? '' : fmtNum(celda, 8)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="texto-ayuda" style={{ marginTop: '10px' }}>
                    Los coeficientes <MathTex tex="b_i" /> son las celdas resaltadas (la diagonal de la tabla).
                  </p>
                  {resultado.forma_newton_latex && (
                    <div className="polynomial-latex-box" style={{ marginTop: '8px' }}>
                      <MathTex tex={`P(x) = ${resultado.forma_newton_latex}`} block />
                    </div>
                  )}
                </div>
              )}

              {resultado.matriz_vandermonde && (
                <div className="glass-card">
                  <h3 style={{ marginBottom: '10px' }}>Matriz de Vandermonde</h3>
                  <MatrixView matrix={resultado.matriz_vandermonde} label="Matriz V" digits={5} />
                </div>
              )}

              {resultado.polinomios_base && (
                <div className="glass-card">
                  <h3 style={{ marginBottom: '10px' }}>Polinomios base de Lagrange <MathTex tex="L_i(x)" /></h3>
                  <div className="spline-segments-list">
                    {resultado.polinomios_base.map((b) => (
                      <div key={b.indice} className="spline-segment-row">
                        <span className="spline-interval mono">
                          L<sub>{b.indice}</sub>(x) · y<sub>{b.indice}</sub> = {fmtNum(b.yi, 4)}
                        </span>
                        <MathTex tex={`L_{${b.indice}}(x) = ${b.latex}`} />
                      </div>
                    ))}
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

function ComparativeReportCap3({ comparacion, fxReal }) {
  if (!comparacion) {
    return (
      <div className="glass-card">
        <p style={{ color: 'var(--text-secondary)' }}>
          Presiona <strong>"Comparar los 6 métodos"</strong> para superponer las curvas y comparar sus errores.
        </p>
      </div>
    );
  }

  const { metodos = [], informe = {} } = comparacion;
  const colores = ['#00f5d4', '#7c5cff', '#ffbe0b', '#ff5c8a', '#38bdf8', '#a3e635'];
  const hayReserva = (comparacion.puntos_reservados || []).length > 0;

  const curvasSuperpuestas = metodos
    .filter((m) => m.curva && m.curva.x && m.curva.x.length > 0)
    .map((m, i) => ({
      name: m.metodo,
      color: colores[i % colores.length],
      x: m.curva.x,
      y: m.curva.y,
      dashed: m.id === 'newton' || m.id === 'lagrange'
    }));
  const conReal = metodos[0]?.curva?.y_real;
  if (conReal) {
    curvasSuperpuestas.push({ name: `f(x) = ${fxReal}`, color: '#94a3b8', x: metodos[0].curva.x, y: conReal, dashed: true, referencia: true });
  }

  return (
    <div className="comparative-report">
      <div className="kpi-grid">
        <div className="kpi-card highlight-ch3">
          <span className="kpi-label">Menor error absoluto (reservados)</span>
          <div className="kpi-value">{hayReserva ? informe.ganador_validacion_abs : 'Sin reserva'}</div>
          <span className="kpi-sub">{hayReserva ? `En el ${comparacion.porcentaje_reserva} % reservado` : 'Elige 20 % o 30 % para medirlo'}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Menor error relativo (reservados)</span>
          <div className="kpi-value">{hayReserva ? informe.ganador_validacion_rel : 'Sin reserva'}</div>
          <span className="kpi-sub">Error medio en los puntos reservados</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Condición de Vandermonde κ(V)</span>
          <div className="kpi-value mono">{fmtSci(informe.condicion_vandermonde)}</div>
          <span className="kpi-sub">Valores grandes: coeficientes sensibles al redondeo</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Puntos usados / reservados</span>
          <div className="kpi-value mono">
            {comparacion.puntos_entrenamiento?.length || 0} / {comparacion.puntos_reservados?.length || 0}
          </div>
          <span className="kpi-sub">{hayReserva ? `Reservado: ${comparacion.porcentaje_reserva} %` : 'Se usaron todos los puntos'}</span>
        </div>
      </div>

      <InterpolationChart
        puntosEntrenamiento={comparacion.puntos_entrenamiento}
        puntosReservados={comparacion.puntos_reservados}
        curvas={curvasSuperpuestas}
        titulo="Los 6 métodos superpuestos"
      />

      <div className="glass-card">
        <h3 style={{ marginBottom: '10px' }}>Informe</h3>
        <p className="texto-informe">{informe.conclusion_general}</p>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Método</th>
                <th>Polinomio / tramos</th>
                <th>Error abs. medio (reservados)</th>
                <th>Error rel. medio (reservados)</th>
                <th>P(x*)</th>
              </tr>
            </thead>
            <tbody>
              {metodos.map((m, idx) => (
                <tr key={idx}>
                  <td><strong>{m.metodo}</strong></td>
                  <td className="mono celda-polinomio" title={m.polinomio_texto}>{m.polinomio_texto}</td>
                  <td className="mono">{m.validacion_reserva ? fmtSci(m.validacion_reserva.error_abs_medio) : '—'}</td>
                  <td className="mono">{m.validacion_reserva ? fmtSci(m.validacion_reserva.error_rel_medio) : '—'}</td>
                  <td className="mono">{m.evaluacion_punto ? fmtNum(m.evaluacion_punto.y_interp, 6) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

window.Chapter3 = Chapter3;
