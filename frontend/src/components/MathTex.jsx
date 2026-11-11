/* Componentes utilitarios en React: KaTeX, Formateo Numérico y Visor de Matrices */
const { useEffect, useRef } = React;

window.fmtNum = function (v, dec = 8) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'string') return v;
  if (!Number.isFinite(v)) return '—';
  if (v === 0) return '0.00000000'.slice(0, dec + 2);
  const absV = Math.abs(v);
  if (absV < 1e-4 || absV >= 1e7) {
    return v.toExponential(3);
  }
  return Number(v).toFixed(dec);
};

window.fmtSci = function (v) {
  if (v === null || v === undefined || v === '' || !Number.isFinite(Number(v))) return '—';
  return Number(v).toExponential(3);
};

// 10 elevado a un entero con superíndices: -3 -> "10⁻³"
window.fmtPotencia10 = function (k) {
  const sup = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
  return '10' + String(Math.round(k)).split('').map((c) => sup[c] || c).join('');
};

// Nombre legible de cada criterio de error
window.NOMBRE_ERROR = { abs: 'Absoluto', rel: 'Relativo', cond: 'Condición' };

// Texto corto para cada estado que devuelve el backend
window.ETIQUETA_ESTADO = {
  raiz: 'Raíz exacta',
  aproximacion: 'Convergió',
  exito: 'Resuelto',
  intervalo: 'Intervalo hallado',
  fracaso: 'No convergió',
  diverge: 'Divergió',
  detenido: 'Se detuvo',
  inadecuado: 'Intervalo inválido',
  inconsistente: 'g(x) no válida',
  error: 'Error'
};

// Recuadro con el mensaje final del método y sus avisos (prevención de errores)
window.EstadoMetodo = function EstadoMetodo({ exito, estado, mensaje, avisos = [] }) {
  if (!mensaje && (!avisos || avisos.length === 0)) return null;
  const clase = exito ? 'alert-success' : estado === 'fracaso' ? 'alert-warning' : 'alert-error';
  return (
    <div className="estado-metodo" role="status">
      {mensaje && (
        <div className={`alert-box ${clase}`}>
          <strong>{ETIQUETA_ESTADO[estado] || 'Resultado'}:</strong> {mensaje}
        </div>
      )}
      {(avisos || []).map((a, i) => (
        <div key={i} className="alert-box alert-warning">{a}</div>
      ))}
    </div>
  );
};

// Tabla cruzada: cada método corrido con cada criterio de parada (absoluto, relativo, condición)
window.TablaCriterios = function TablaCriterios({ metodosPorCriterio }) {
  if (!metodosPorCriterio || !metodosPorCriterio.abs) return null;
  const criterios = ['abs', 'rel', 'cond'];
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Método</th>
            {criterios.map((c) => (
              <th key={c}>Parando con error {NOMBRE_ERROR[c].toLowerCase()}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metodosPorCriterio.abs.map((m, i) => (
            <tr key={m.metodo}>
              <td><strong>{m.metodo}</strong></td>
              {criterios.map((c) => {
                const r = metodosPorCriterio[c][i];
                return (
                  <td key={c} title={r.mensaje || ''}>
                    <span className={`status-pill ${r.convergio ? 'ok' : 'warn'}`}>
                      {ETIQUETA_ESTADO[r.estado] || r.estado}
                    </span>{' '}
                    <span className="mono">{r.iteraciones_usadas ?? '—'} it · {fmtSci(r.error_final)}</span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

window.MathTex = function MathTex({ tex, block = false, className = '' }) {
  const spanRef = useRef(null);

  useEffect(() => {
    if (!spanRef.current) return;
    if (window.katex && tex) {
      try {
        window.katex.render(String(tex), spanRef.current, {
          throwOnError: false,
          displayMode: block,
        });
        return;
      } catch (e) {
        // Fallback al texto plano si hay algún símbolo no estándar
      }
    }
    spanRef.current.textContent = tex || '';
  }, [tex, block]);

  return <span ref={spanRef} className={className} />;
};

window.MatrixView = function MatrixView({ title, label, data, matrix, dec = 5, digits }) {
  const matData = matrix || data;
  const matTitle = label || title;
  const numDec = digits !== undefined ? digits : dec;
  if (!matData) return null;
  const is2D = Array.isArray(matData) && Array.isArray(matData[0]);

  return (
    <div className="matrix-display-card">
      {matTitle && <div className="matrix-display-title">{matTitle}</div>}
      <div className="matrix-bracket-box">
        {is2D ? (
          <table style={{ borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            <tbody>
              {matData.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td
                      key={cIdx}
                      style={{
                        padding: '4px 9px',
                        textAlign: 'right',
                        color: rIdx === cIdx ? 'var(--accent-cyan)' : 'var(--text-primary)',
                        fontWeight: rIdx === cIdx ? 700 : 400,
                      }}
                    >
                      {typeof cell === 'number' ? Number(cell).toFixed(numDec) : String(cell ?? '—')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : Array.isArray(matData) ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontFamily: 'var(--font-mono)', fontSize: '12.5px' }}>
            {matData.map((val, idx) => (
              <span key={idx} style={{ padding: '2px 6px', background: 'rgba(99,102,241,0.1)', borderRadius: '6px' }}>
                {typeof val === 'number' ? Number(val).toFixed(numDec) : String(val)}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>{String(matData)}</div>
        )}
      </div>
    </div>
  );
};
