// ============================================================================
// GRÁFICAS INTERACTIVAS SVG CON ANIMADOR PASO A PASO DE ITERACIONES
// ============================================================================

const { useState, useEffect } = React;

const PALETTE = [
  '#00f5d4', // Cyan Aurora
  '#7c5cff', // Violet
  '#ffbe0b', // Amber
  '#ff5c8a', // Rose
  '#38bdf8', // Sky
  '#a3e635', // Lime
  '#f97316'  // Orange
];

// Títulos de los ejes (x abajo, y vertical a la izquierda)
function AxisTitles({ W, H, xLabel, yLabel }) {
  return (
    <g fill="var(--text-secondary)" fontSize="12" fontFamily="JetBrains Mono">
      <text x={W / 2} y={H - 2} textAnchor="middle">{xLabel}</text>
      <text x={14} y={H / 2} textAnchor="middle" transform={`rotate(-90 14 ${H / 2})`}>{yLabel}</text>
    </g>
  );
}

function buildSmoothPath(points) {
  let d = '';
  let penDown = false;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (p.sx === null || p.sy === null || !Number.isFinite(p.sx) || !Number.isFinite(p.sy)) {
      penDown = false;
      continue;
    }
    d += `${penDown ? 'L' : 'M'} ${p.sx.toFixed(2)} ${p.sy.toFixed(2)} `;
    penDown = true;
  }
  return d;
}

/* ============================================================================
   1. GRÁFICA DE FUNCIONES Y ANIMADOR DE ITERACIONES (CAPÍTULO 1)
   ============================================================================ */
window.FunctionChart = function FunctionChart({
  curva,
  grafica,
  pasosAnimacion = [],
  pasos = [],
  titulo = 'Visualización Geométrica de f(x)'
}) {
  const datosGrafica = curva || grafica;
  const listaPasos = pasosAnimacion && pasosAnimacion.length > 0 ? pasosAnimacion : pasos;

  const [showDf, setShowDf] = useState(false);
  const [showG, setShowG] = useState(true);
  const [stepIdx, setStepIdx] = useState(listaPasos.length > 0 ? listaPasos.length - 1 : 0);
  const [playing, setPlaying] = useState(false);
  const [hoverPt, setHoverPt] = useState(null);

  useEffect(() => {
    setStepIdx(listaPasos.length > 0 ? listaPasos.length - 1 : 0);
    setPlaying(false);
  }, [datosGrafica, listaPasos.length]);

  useEffect(() => {
    if (!playing || listaPasos.length === 0) return;
    const timer = setInterval(() => {
      setStepIdx((prev) => {
        if (prev >= listaPasos.length - 1) {
          setPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 800);
    return () => clearInterval(timer);
  }, [playing, listaPasos]);

  if (!datosGrafica || !datosGrafica.curva || datosGrafica.curva.length === 0) return null;

  const W = 780;
  const H = 380;
  const PAD = { top: 24, right: 28, bottom: 58, left: 84 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const ptsCurva = datosGrafica.curva;
  const hasDf = ptsCurva.some((p) => p.dfx !== null && p.dfx !== undefined);
  const hasG = ptsCurva.some((p) => p.gx !== null && p.gx !== undefined);

  const xMin = datosGrafica.rango_x ? datosGrafica.rango_x[0] : Math.min(...ptsCurva.map((p) => p.x));
  const xMax = datosGrafica.rango_x ? datosGrafica.rango_x[1] : Math.max(...ptsCurva.map((p) => p.x));

  const yVals = [0];
  ptsCurva.forEach((p) => {
    if (Number.isFinite(p.fx)) yVals.push(p.fx);
    if (showDf && hasDf && Number.isFinite(p.dfx)) yVals.push(p.dfx);
    if (showG && hasG && Number.isFinite(p.gx)) {
      yVals.push(p.gx);
      yVals.push(p.yx);
    }
  });

  let yMin = Math.min(...yVals);
  let yMax = Math.max(...yVals);
  if (yMax - yMin < 1e-6) {
    yMin -= 1;
    yMax += 1;
  } else {
    const padY = 0.12 * (yMax - yMin);
    yMin -= padY;
    yMax += padY;
  }

  const sx = (x) => PAD.left + ((x - xMin) / Math.max(1e-9, xMax - xMin)) * plotW;
  const sy = (y) => PAD.top + (1 - (y - yMin) / Math.max(1e-9, yMax - yMin)) * plotH;

  const pathF = buildSmoothPath(ptsCurva.map((p) => ({ sx: sx(p.x), sy: Number.isFinite(p.fx) ? sy(p.fx) : null })));
  const pathDf = showDf && hasDf
    ? buildSmoothPath(ptsCurva.map((p) => ({ sx: sx(p.x), sy: Number.isFinite(p.dfx) ? sy(p.dfx) : null })))
    : '';
  const pathG = showG && hasG
    ? buildSmoothPath(ptsCurva.map((p) => ({ sx: sx(p.x), sy: Number.isFinite(p.gx) ? sy(p.gx) : null })))
    : '';
  const pathYX = showG && hasG
    ? buildSmoothPath(ptsCurva.map((p) => ({ sx: sx(p.x), sy: Number.isFinite(p.yx) ? sy(p.yx) : null })))
    : '';

  const pasoActual = listaPasos[stepIdx] || null;
  const zeroY = sy(0);

  const xTicks = Array.from({ length: 6 }, (_, i) => xMin + (i / 5) * (xMax - xMin));
  const yTicks = Array.from({ length: 5 }, (_, i) => yMin + (i / 4) * (yMax - yMin));

  return (
    <div className="chart-box">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
        <strong style={{ fontFamily: 'var(--font-display)', fontSize: '15px' }}>{titulo}</strong>
        {hoverPt && (
          <span className="mono" style={{ fontSize: '12px', color: 'var(--accent-cyan)' }}>
            x = {hoverPt.x.toFixed(4)} | f(x) = {hoverPt.fx !== null ? hoverPt.fx.toFixed(5) : '—'}
          </span>
        )}
      </div>

      {listaPasos.length > 0 && (
        <div className="animator-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <span className="badge-pill emerald">
              Paso #{pasoActual ? pasoActual.i : stepIdx} / {listaPasos[listaPasos.length - 1]?.i ?? listaPasos.length - 1}
            </span>
            {pasoActual && pasoActual.xm !== undefined && (
              <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                [{Number(pasoActual.a).toFixed(4)}, {Number(pasoActual.b).toFixed(4)}] → xm = {Number(pasoActual.xm).toFixed(6)}
              </span>
            )}
            {pasoActual && pasoActual.xn !== undefined && (
              <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                xᵢ = {Number(pasoActual.x).toFixed(5)} → xᵢ₊₁ = {Number(pasoActual.xn).toFixed(6)}
              </span>
            )}
            {pasoActual && pasoActual.gx !== undefined && (
              <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                xᵢ = {Number(pasoActual.x).toFixed(5)} → g(xᵢ) = {Number(pasoActual.gx).toFixed(6)}
              </span>
            )}
          </div>
          <div className="animator-controls">
            <button type="button" className="btn-secondary" onClick={() => { setPlaying(false); setStepIdx(0); }}>⏮</button>
            <button type="button" className="btn-secondary" onClick={() => { setPlaying(false); setStepIdx((s) => Math.max(0, s - 1)); }}>◀</button>
            <button
              type="button"
              className="btn-secondary"
              style={{ borderColor: 'var(--accent-indigo)', color: 'var(--accent-cyan)' }}
              onClick={() => {
                if (stepIdx >= listaPasos.length - 1) setStepIdx(0);
                setPlaying((p) => !p);
              }}
            >
              {playing ? '⏸ Pausar' : '▶ Animar Iteraciones'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => { setPlaying(false); setStepIdx((s) => Math.min(listaPasos.length - 1, s + 1)); }}>▶</button>
            <button type="button" className="btn-secondary" onClick={() => { setPlaying(false); setStepIdx(listaPasos.length - 1); }}>⏭</button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '14px', fontSize: '12px', fontFamily: 'var(--font-mono)', marginBottom: '8px', flexWrap: 'wrap' }}>
        <span style={{ color: '#00f5d4', fontWeight: 700 }}>● f(x)</span>
        {hasDf && (
          <label style={{ cursor: 'pointer', color: '#a855f7' }}>
            <input type="checkbox" checked={showDf} onChange={(e) => setShowDf(e.target.checked)} style={{ marginRight: '5px' }} />
            Mostrar f'(x)
          </label>
        )}
        {hasG && (
          <label style={{ cursor: 'pointer', color: '#10b981' }}>
            <input type="checkbox" checked={showG} onChange={(e) => setShowG(e.target.checked)} style={{ marginRight: '5px' }} />
            g(x) y recta identidad y = x
          </label>
        )}
        <span style={{ color: '#f59e0b' }}>● Iteraciones xᵢ</span>
        {datosGrafica.raiz && <span style={{ color: '#f43f5e', fontWeight: 700 }}>★ Raíz ≈ {Number(datosGrafica.raiz.x).toFixed(7)}</span>}
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', height: 'auto', display: 'block', userSelect: 'none' }}
        onMouseLeave={() => setHoverPt(null)}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const relX = ((e.clientX - rect.left) / rect.width) * W;
          if (relX < PAD.left || relX > W - PAD.right) return;
          const ratio = (relX - PAD.left) / plotW;
          const idx = Math.min(ptsCurva.length - 1, Math.max(0, Math.round(ratio * (ptsCurva.length - 1))));
          setHoverPt(ptsCurva[idx]);
        }}
      >
        <defs>
          <clipPath id="plot-clip-cap1">
            <rect x={PAD.left} y={PAD.top} width={plotW} height={plotH} />
          </clipPath>
        </defs>

        {xTicks.map((tk, i) => (
          <g key={`xt-${i}`}>
            <line x1={sx(tk)} y1={PAD.top} x2={sx(tk)} y2={H - PAD.bottom} stroke="rgba(148,163,184,0.12)" strokeDasharray="4 4" />
            <text x={sx(tk)} y={H - PAD.bottom + 20} fill="var(--text-muted)" fontSize="12" fontFamily="JetBrains Mono" textAnchor="middle">
              {tk.toFixed(2)}
            </text>
          </g>
        ))}
        <AxisTitles W={W} H={H} xLabel="x" yLabel="f(x)" />
        {yTicks.map((tk, i) => (
          <g key={`yt-${i}`}>
            <line x1={PAD.left} y1={sy(tk)} x2={W - PAD.right} y2={sy(tk)} stroke="rgba(148,163,184,0.12)" strokeDasharray="4 4" />
            <text x={PAD.left - 8} y={sy(tk) + 4} fill="var(--text-muted)" fontSize="12" fontFamily="JetBrains Mono" textAnchor="end">
              {Math.abs(tk) >= 1000 ? tk.toExponential(1) : tk.toFixed(2)}
            </text>
          </g>
        ))}

        {zeroY >= PAD.top && zeroY <= H - PAD.bottom && (
          <line x1={PAD.left} y1={zeroY} x2={W - PAD.right} y2={zeroY} stroke="rgba(241,245,249,0.45)" strokeWidth="1.4" />
        )}

        <g clipPath="url(#plot-clip-cap1)">
          {/* Intervalo [a, b] en Bisección / Regla Falsa */}
          {pasoActual && pasoActual.a !== undefined && pasoActual.b !== undefined && (
            <rect
              x={sx(Math.min(pasoActual.a, pasoActual.b))}
              y={PAD.top}
              width={Math.max(2, Math.abs(sx(pasoActual.b) - sx(pasoActual.a)))}
              height={plotH}
              fill="rgba(0, 245, 212, 0.11)"
            />
          )}

          {/* Cuerda en Regla Falsa */}
          {pasoActual && pasoActual.fa !== undefined && pasoActual.fb !== undefined && (
            <line
              x1={sx(pasoActual.a)}
              y1={sy(pasoActual.fa)}
              x2={sx(pasoActual.b)}
              y2={sy(pasoActual.fb)}
              stroke="#ffbe0b"
              strokeWidth="1.8"
              strokeDasharray="5 4"
            />
          )}

          {/* Tangente en Newton / Raíces Múltiples */}
          {pasoActual && pasoActual.xn !== undefined && pasoActual.x !== undefined && pasoActual.fx !== undefined && (
            <g>
              <line x1={sx(pasoActual.x)} y1={zeroY} x2={sx(pasoActual.x)} y2={sy(pasoActual.fx)} stroke="rgba(245,158,11,0.5)" strokeDasharray="3 3" />
              <line x1={sx(pasoActual.x)} y1={sy(pasoActual.fx)} x2={sx(pasoActual.xn)} y2={zeroY} stroke="#ffbe0b" strokeWidth="2.2" />
            </g>
          )}

          {/* Secante */}
          {pasoActual && pasoActual.x0 !== undefined && pasoActual.x1 !== undefined && pasoActual.x2 !== undefined && (
            <line
              x1={sx(pasoActual.x0)}
              y1={sy(pasoActual.f0)}
              x2={sx(pasoActual.x2)}
              y2={zeroY}
              stroke="#ffbe0b"
              strokeWidth="2"
              strokeDasharray="4 3"
            />
          )}

          {/* Telaraña (Cobweb) en Punto Fijo */}
          {pasoActual && pasoActual.gx !== undefined && pasoActual.x !== undefined && (
            <g>
              <line x1={sx(pasoActual.x)} y1={sy(pasoActual.x)} x2={sx(pasoActual.x)} y2={sy(pasoActual.gx)} stroke="#ffbe0b" strokeWidth="2" />
              <line x1={sx(pasoActual.x)} y1={sy(pasoActual.gx)} x2={sx(pasoActual.gx)} y2={sy(pasoActual.gx)} stroke="#ffbe0b" strokeWidth="2" strokeDasharray="4 3" />
            </g>
          )}

          {pathYX && <path d={pathYX} fill="none" stroke="rgba(148,163,184,0.55)" strokeWidth="1.4" strokeDasharray="6 4" />}
          {pathG && <path d={pathG} fill="none" stroke="#10b981" strokeWidth="2.2" />}
          {pathDf && <path d={pathDf} fill="none" stroke="#a855f7" strokeWidth="1.8" strokeDasharray="4 4" />}
          <path d={pathF} fill="none" stroke="#00f5d4" strokeWidth="2.8" />

          {(datosGrafica.iteraciones || []).slice(0, stepIdx + 2).map((pt, idx) => (
            <circle
              key={idx}
              cx={sx(pt.x)}
              cy={sy(pt.fx ?? 0)}
              r={idx === stepIdx ? 6 : 4}
              fill={idx === stepIdx ? '#10b981' : '#f59e0b'}
              stroke="#07090e"
              strokeWidth="1.5"
            />
          ))}

          {datosGrafica.raiz && datosGrafica.raiz.x !== null && (
            <g>
              <line x1={sx(datosGrafica.raiz.x)} y1={PAD.top} x2={sx(datosGrafica.raiz.x)} y2={H - PAD.bottom} stroke="rgba(244,63,94,0.55)" strokeDasharray="3 3" />
              <circle cx={sx(datosGrafica.raiz.x)} cy={sy(datosGrafica.raiz.fx ?? 0)} r="7" fill="#f43f5e" stroke="#fff" strokeWidth="2" />
            </g>
          )}

          {hoverPt && Number.isFinite(hoverPt.fx) && (
            <g>
              <line x1={sx(hoverPt.x)} y1={PAD.top} x2={sx(hoverPt.x)} y2={H - PAD.bottom} stroke="rgba(0,245,212,0.35)" />
              <circle cx={sx(hoverPt.x)} cy={sy(hoverPt.fx)} r="5" fill="#00f5d4" stroke="#fff" strokeWidth="1.5" />
            </g>
          )}
        </g>
      </svg>
    </div>
  );
};

/* ============================================================================
   2. GRÁFICA DE CONVERGENCIA DE ERRORES EN ESCALA LOG10 (CAPÍTULOS 1 Y 2)
   Soporta: series = [{ name, color, values: [...] }]
   ============================================================================ */
window.ConvergenceChart = function ConvergenceChart({
  series = [],
  titulo = 'Evolución Logarítmica del Error por Iteración (log₁₀)'
}) {
  if (!series || series.length === 0) return null;

  const W = 780;
  const H = 330;
  const PAD = { top: 24, right: 30, bottom: 58, left: 84 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const logValues = [];
  let maxLen = 1;
  series.forEach((s) => {
    const vals = s.values || [];
    maxLen = Math.max(maxLen, vals.length - 1);
    vals.forEach((v) => {
      if (v !== null && v !== undefined && Number.isFinite(v) && v > 0) {
        logValues.push(Math.log10(v));
      }
    });
  });

  if (logValues.length === 0) {
    return (
      <div className="chart-box" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)' }}>
        Convergencia alcanzada de forma inmediata (error nulo exacto).
      </div>
    );
  }

  const yMin = Math.floor(Math.min(...logValues));
  const yMax = Math.ceil(Math.max(...logValues)) + (Math.max(...logValues) === Math.ceil(Math.max(...logValues)) ? 1 : 0);

  const sx = (iter) => PAD.left + (iter / Math.max(1, maxLen)) * plotW;
  const sy = (logVal) => PAD.top + (1 - (logVal - yMin) / Math.max(1, yMax - yMin)) * plotH;

  // Marcas en potencias enteras de 10 (como mucho unas 7)
  const pasoY = Math.max(1, Math.ceil((yMax - yMin) / 6));
  const yTicks = [];
  for (let k = yMin; k <= yMax; k += pasoY) yTicks.push(k);
  const xStep = Math.max(1, Math.ceil(maxLen / 8));
  const xTicks = [];
  for (let i = 0; i <= maxLen; i += xStep) xTicks.push(i);

  return (
    <div className="chart-box">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
        <strong style={{ fontFamily: 'var(--font-display)', fontSize: '14.5px' }}>{titulo}</strong>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
          {series.map((s, idx) => (
            <span key={idx} style={{ color: s.color || PALETTE[idx % PALETTE.length], fontWeight: 700 }}>
              ● {s.name}
            </span>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {xTicks.map((tk) => (
          <g key={`cx-${tk}`}>
            <line x1={sx(tk)} y1={PAD.top} x2={sx(tk)} y2={H - PAD.bottom} stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
            <text x={sx(tk)} y={H - PAD.bottom + 20} fill="var(--text-muted)" fontSize="12" fontFamily="JetBrains Mono" textAnchor="middle">
              {tk}
            </text>
          </g>
        ))}
        {yTicks.map((tk, idx) => (
          <g key={`cy-${idx}`}>
            <line x1={PAD.left} y1={sy(tk)} x2={W - PAD.right} y2={sy(tk)} stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
            <text x={PAD.left - 8} y={sy(tk) + 4} fill="var(--text-muted)" fontSize="13" fontFamily="system-ui, sans-serif" textAnchor="end">
              {fmtPotencia10(tk)}
            </text>
          </g>
        ))}
        <AxisTitles W={W} H={H} xLabel="Iteración k" yLabel="Error (escala log)" />

        {series.map((s, idx) => {
          const color = s.color || PALETTE[idx % PALETTE.length];
          const pts = (s.values || []).map((v, k) => {
            const valid = v !== null && v !== undefined && Number.isFinite(v) && v > 0;
            return {
              sx: sx(k),
              sy: valid ? sy(Math.log10(v)) : null,
              iter: k,
              val: v
            };
          });
          const d = buildSmoothPath(pts);
          return (
            <g key={idx}>
              <path d={d} fill="none" stroke={color} strokeWidth="2.5" />
              {pts.filter((p) => p.sy !== null).map((p, pIdx) => (
                <circle key={pIdx} cx={p.sx} cy={p.sy} r="3.8" fill={color} stroke="#07090e" strokeWidth="1.2">
                  <title>{`${s.name} (k=${p.iter}): ${Number(p.val).toExponential(4)}`}</title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/* ============================================================================
   3. GRÁFICA DE INTERPOLACIÓN Y VALIDACIÓN DEL 20% / 30% (CAPÍTULO 3)
   ============================================================================ */
window.InterpolationChart = function InterpolationChart({
  puntosEntrenamiento = [],
  puntosReservados = [],
  curvas = [],
  evaluacionPunto = null,
  titulo = 'Gráfica del Polinomio Interpolante y Puntos Reservados'
}) {
  if (!curvas || curvas.length === 0) return null;

  const W = 780;
  const H = 380;
  const PAD = { top: 24, right: 30, bottom: 58, left: 84 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const xVals = [];
  const yVals = [];

  // Las curvas de referencia (f(x) real) no definen la escala: si tienen asíntotas la deformarían
  curvas.forEach((c) => {
    (c.x || []).forEach((vx) => { if (Number.isFinite(vx)) xVals.push(vx); });
    if (!c.referencia) (c.y || []).forEach((vy) => { if (Number.isFinite(vy)) yVals.push(vy); });
  });
  puntosEntrenamiento.forEach((p) => {
    if (Number.isFinite(p.x)) xVals.push(p.x);
    if (Number.isFinite(p.y)) yVals.push(p.y);
  });
  puntosReservados.forEach((p) => {
    if (Number.isFinite(p.x)) xVals.push(p.x);
    if (Number.isFinite(p.y)) yVals.push(p.y);
  });

  if (xVals.length === 0 || yVals.length === 0) return null;

  const xMin = Math.min(...xVals);
  const xMax = Math.max(...xVals);
  let yMin = Math.min(...yVals);
  let yMax = Math.max(...yVals);
  const padY = 0.12 * Math.max(1, yMax - yMin);
  yMin -= padY;
  yMax += padY;

  const sx = (x) => PAD.left + ((x - xMin) / Math.max(1e-9, xMax - xMin)) * plotW;
  const sy = (y) => PAD.top + (1 - (y - yMin) / Math.max(1e-9, yMax - yMin)) * plotH;

  const xTicks = Array.from({ length: 6 }, (_, i) => xMin + (i / 5) * (xMax - xMin));
  const yTicks = Array.from({ length: 5 }, (_, i) => yMin + (i / 4) * (yMax - yMin));

  const xEv = evaluacionPunto?.x_eval ?? evaluacionPunto?.x;
  const yEv = evaluacionPunto?.y_interp ?? evaluacionPunto?.y;

  return (
    <div className="chart-box">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
        <strong style={{ fontFamily: 'var(--font-display)', fontSize: '15px' }}>{titulo}</strong>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
          {curvas.map((c, i) => (
            <span key={i} style={{ color: c.color || PALETTE[i % PALETTE.length], fontWeight: 700 }}>
              ● {c.name}
            </span>
          ))}
          <span style={{ color: '#10b981', fontWeight: 700 }}>● Puntos usados ({puntosEntrenamiento.length})</span>
          {puntosReservados.length > 0 && (
            <span style={{ color: '#ffbe0b', fontWeight: 700 }}>◆ Puntos reservados ({puntosReservados.length})</span>
          )}
          {xEv !== undefined && xEv !== null && (
            <span style={{ color: '#ff5c8a', fontWeight: 700 }}>★ x* = {xEv}</span>
          )}
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        <defs>
          <clipPath id="plot-clip-cap3">
            <rect x={PAD.left} y={PAD.top} width={plotW} height={plotH} />
          </clipPath>
        </defs>
        {xTicks.map((tk, i) => (
          <g key={`ix-${i}`}>
            <line x1={sx(tk)} y1={PAD.top} x2={sx(tk)} y2={H - PAD.bottom} stroke="rgba(148,163,184,0.12)" strokeDasharray="4 4" />
            <text x={sx(tk)} y={H - PAD.bottom + 20} fill="var(--text-muted)" fontSize="12" fontFamily="JetBrains Mono" textAnchor="middle">
              {tk.toFixed(2)}
            </text>
          </g>
        ))}
        <AxisTitles W={W} H={H} xLabel="x" yLabel="y" />
        {yTicks.map((tk, i) => (
          <g key={`iy-${i}`}>
            <line x1={PAD.left} y1={sy(tk)} x2={W - PAD.right} y2={sy(tk)} stroke="rgba(148,163,184,0.12)" strokeDasharray="4 4" />
            <text x={PAD.left - 8} y={sy(tk) + 4} fill="var(--text-muted)" fontSize="12" fontFamily="JetBrains Mono" textAnchor="end">
              {tk.toFixed(2)}
            </text>
          </g>
        ))}

        <g clipPath="url(#plot-clip-cap3)">
          {curvas.map((c, idx) => {
            const pts = (c.x || []).map((vx, i) => ({
              sx: sx(vx),
              sy: Number.isFinite(c.y?.[i]) ? sy(c.y[i]) : null
            }));
            const d = buildSmoothPath(pts);
            return (
              <path
                key={idx}
                d={d}
                fill="none"
                stroke={c.color || PALETTE[idx % PALETTE.length]}
                strokeWidth={c.referencia ? 1.8 : 2.5}
                strokeDasharray={c.dashed ? '6 4' : undefined}
              />
            );
          })}
        </g>

        {/* Nodos de entrenamiento */}
        {puntosEntrenamiento.map((n, idx) => (
          <circle key={`n-${idx}`} cx={sx(n.x)} cy={sy(n.y)} r="5.5" fill="#10b981" stroke="#07090e" strokeWidth="1.6">
            <title>{`Punto usado (${n.x}, ${n.y})`}</title>
          </circle>
        ))}

        {/* Nodos almacenados (20% o 30% reservados) */}
        {puntosReservados.map((a, idx) => (
          <g key={`a-${idx}`}>
            <line x1={sx(a.x)} y1={PAD.top} x2={sx(a.x)} y2={H - PAD.bottom} stroke="rgba(255,190,11,0.35)" strokeDasharray="3 3" />
            <circle cx={sx(a.x)} cy={sy(a.y)} r="7" fill="#ffbe0b" stroke="#fff" strokeWidth="2">
              <title>{`Punto reservado (${a.x}, ${a.y})`}</title>
            </circle>
          </g>
        ))}

        {/* Punto evaluado x* */}
        {xEv !== undefined && xEv !== null && Number.isFinite(yEv) && (
          <g>
            <line x1={sx(xEv)} y1={PAD.top} x2={sx(xEv)} y2={H - PAD.bottom} stroke="rgba(244,63,94,0.5)" strokeDasharray="4 3" />
            <circle cx={sx(xEv)} cy={sy(yEv)} r="7.5" fill="#ff5c8a" stroke="#fff" strokeWidth="2">
              <title>{`Evaluación P(${xEv}) = ${yEv}`}</title>
            </circle>
          </g>
        )}
      </svg>
    </div>
  );
};
