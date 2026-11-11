// ============================================================================
// APLICACIÓN PRINCIPAL: navegación por capítulos, portada y ayuda
// Análisis Numérico · Universidad EAFIT · Trabajo Final
// ============================================================================

const { useState, useEffect } = React;

// Datos de la entrega
const INTEGRANTES = ['Santiago Vélez Blandón'];
const REPO_URL = 'https://github.com/Zacks081/Trabajo_Final_Analisis';

function App() {
  const [vista, setVista] = useState('inicio'); // 'inicio' | 'cap1' | 'cap2' | 'cap3'
  const [tema, setTema] = useState(() => {
    try {
      return localStorage.getItem('numlab_tema') || 'dark';
    } catch (e) {
      return 'dark';
    }
  });
  const [modalAyuda, setModalAyuda] = useState(false);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema);
    try {
      localStorage.setItem('numlab_tema', tema);
    } catch (e) {
      // Sin almacenamiento disponible: el tema solo dura esta sesión
    }
  }, [tema]);

  const notify = (mensaje, tipo = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev.slice(-3), { id, mensaje, tipo }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3600);
  };

  const apiUrl = '/api';

  const capitulos = [
    { id: 'cap1', icono: 'f(x)', titulo: 'Capítulo 1 · Raíces', desc: 'Bisección, Newton, Secante…' },
    { id: 'cap2', icono: 'Ax=b', titulo: 'Capítulo 2 · Sistemas', desc: 'Jacobi, Gauss-Seidel, SOR' },
    { id: 'cap3', icono: 'P(x)', titulo: 'Capítulo 3 · Interpolación', desc: 'Vandermonde, Newton, Lagrange, Splines' },
  ];

  return (
    <div className="app-shell">
      <div className="ambient-backdrop" aria-hidden="true">
        <div className="aurora-orb orb-1" />
        <div className="aurora-orb orb-2" />
        <div className="aurora-orb orb-3" />
        <div className="grid-overlay" />
      </div>

      {/* BARRA LATERAL */}
      <aside className="sidebar">
        <button type="button" className="brand-box" onClick={() => setVista('inicio')}>
          <div className="brand-logo">
            <span>∑</span>
          </div>
          <div className="brand-text">
            <span className="brand-name">NumLab</span>
            <span className="brand-sub">Análisis Numérico · EAFIT</span>
          </div>
        </button>

        <nav className="sidebar-nav">
          <button
            type="button"
            className={`nav-item ${vista === 'inicio' ? 'active home' : ''}`}
            onClick={() => setVista('inicio')}
          >
            <span className="nav-icon">⌂</span>
            <div className="nav-item-text">
              <span className="nav-title">Inicio</span>
              <span className="nav-desc">Resumen y datos de la entrega</span>
            </div>
          </button>

          <div className="nav-section-label">CAPÍTULOS</div>

          {capitulos.map((c, i) => (
            <button
              key={c.id}
              type="button"
              className={`nav-item ${vista === c.id ? `active ch${i + 1}` : ''}`}
              onClick={() => setVista(c.id)}
            >
              <span className={`nav-icon ch${i + 1}-dot`}>{c.icono}</span>
              <div className="nav-item-text">
                <span className="nav-title">{c.titulo}</span>
                <span className="nav-desc">{c.desc}</span>
              </div>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button type="button" className="sidebar-util-btn" onClick={() => setModalAyuda(true)}>
            <span aria-hidden="true">?</span>
            <span>Ayuda y uso de la app</span>
          </button>

          <div className="theme-repo-row">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={() => setTema((t) => (t === 'dark' ? 'light' : 'dark'))}
              title="Cambiar el tema de color"
            >
              {tema === 'dark' ? 'Tema claro' : 'Tema oscuro'}
            </button>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="repo-mini-link">
              GitHub ↗
            </a>
          </div>
        </div>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="main-stage">
        {vista === 'inicio' && (
          <HomeView onSelectChapter={setVista} onOpenHelp={() => setModalAyuda(true)} notify={notify} />
        )}
        {vista === 'cap1' && <Chapter1 apiUrl={apiUrl} notify={notify} />}
        {vista === 'cap2' && <Chapter2 apiUrl={apiUrl} notify={notify} />}
        {vista === 'cap3' && <Chapter3 apiUrl={apiUrl} notify={notify} />}
      </main>

      {modalAyuda && <HelpModal onClose={() => setModalAyuda(false)} />}

      <div className="toast-container" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast-item toast-${t.tipo}`}>
            <span>{t.mensaje}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// PORTADA: capítulos y datos de la entrega
// ============================================================================
function HomeView({ onSelectChapter, onOpenHelp, notify }) {
  const copiarEnlace = () => {
    navigator.clipboard?.writeText(REPO_URL);
    notify('Enlace del repositorio copiado', 'info');
  };

  return (
    <div className="home-view">
      <section className="hero-banner glass-card">
        <div className="hero-badge-row">
          <span className="hero-pill">UNIVERSIDAD EAFIT · ANÁLISIS NUMÉRICO</span>
          <span className="hero-pill accent">TRABAJO FINAL</span>
        </div>

        <h1 className="hero-title">
          Métodos numéricos del curso, <span className="gradient-text">por capítulos</span>
        </h1>

        <p className="hero-description">
          Raíces de ecuaciones no lineales, sistemas de ecuaciones lineales e interpolación. Cada método muestra
          su tabla de iteraciones, su gráfica y un informe que compara los métodos con error absoluto, relativo
          y de condición.
        </p>

        <div className="hero-cta-row">
          <button type="button" className="btn-primary btn-ch1" onClick={() => onSelectChapter('cap1')}>
            Ir al Capítulo 1 →
          </button>
          <button type="button" className="btn-secondary" onClick={onOpenHelp}>
            Cómo usar la app
          </button>
        </div>
      </section>

      <section className="chapters-showcase-grid">
        <button type="button" className="chapter-showcase-card ch1-card" onClick={() => onSelectChapter('cap1')}>
          <div className="showcase-top">
            <span className="showcase-num">CAPÍTULO 1</span>
            <span className="showcase-math"><MathTex tex="f(x) = 0" /></span>
          </div>
          <h2>Ecuaciones no lineales</h2>
          <p>Raíces de funciones algebraicas y trascendentes, con derivadas calculadas automáticamente.</p>
          <ul className="showcase-list">
            <li>✓ Bisección, regla falsa y punto fijo</li>
            <li>✓ Newton-Raphson, secante y raíces múltiples</li>
            <li>✓ Cálculo automático de <MathTex tex="f'(x),\, f''(x)" /></li>
            <li>✓ Comparación con error absoluto, relativo y de condición</li>
          </ul>
          <span className="showcase-link">Abrir Capítulo 1 →</span>
        </button>

        <button type="button" className="chapter-showcase-card ch2-card" onClick={() => onSelectChapter('cap2')}>
          <div className="showcase-top">
            <span className="showcase-num">CAPÍTULO 2</span>
            <span className="showcase-math"><MathTex tex="A\mathbf{x} = \mathbf{b}" /></span>
          </div>
          <h2>Sistemas de ecuaciones lineales</h2>
          <p>
            Matrices de hasta <MathTex tex="8\times 8" />, con radio espectral <MathTex tex="\rho(T)" /> y diagnóstico de convergencia.
          </p>
          <ul className="showcase-list">
            <li>✓ Jacobi, Gauss-Seidel y SOR</li>
            <li>✓ Matrices <MathTex tex="T" /> y <MathTex tex="C" />, y radio espectral</li>
            <li>✓ Indica si el método converge según <MathTex tex="\rho(T) < 1" /></li>
            <li>✓ Comparación con los 3 tipos de error</li>
          </ul>
          <span className="showcase-link">Abrir Capítulo 2 →</span>
        </button>

        <button type="button" className="chapter-showcase-card ch3-card" onClick={() => onSelectChapter('cap3')}>
          <div className="showcase-top">
            <span className="showcase-num">CAPÍTULO 3</span>
            <span className="showcase-math"><MathTex tex="P(x),\, S(x)" /></span>
          </div>
          <h2>Interpolación</h2>
          <p>Polinomio interpolante y trazadores para hasta 10 puntos.</p>
          <ul className="showcase-list">
            <li>✓ Vandermonde, Newton y Lagrange</li>
            <li>✓ Splines lineal, cuadrático y cúbico</li>
            <li>✓ Reserva del 20 % o 30 % de los datos para validar</li>
            <li>✓ Gráfica comparativa de los 6 métodos</li>
          </ul>
          <span className="showcase-link">Abrir Capítulo 3 →</span>
        </button>
      </section>

      <section className="team-repo-section glass-card">
        <div className="team-header-row">
          <div>
            <span className="chapter-eyebrow">DATOS DE LA ENTREGA</span>
            <h3>Integrantes y repositorio</h3>
          </div>
        </div>

        <div className="team-members-grid">
          {INTEGRANTES.map((nombre, idx) => (
            <div key={nombre} className="member-card">
              <div className="member-avatar">{idx + 1}</div>
              <div className="member-info">
                <strong>{nombre}</strong>
              </div>
            </div>
          ))}
        </div>

        <div className="repo-banner-box">
          <div className="repo-banner-info">
            <span className="repo-label">Repositorio con el código:</span>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="repo-url-link mono">
              {REPO_URL}
            </a>
          </div>
          <div className="repo-banner-actions">
            <button type="button" className="btn-secondary" onClick={copiarEnlace}>
              Copiar enlace
            </button>
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="btn-primary">
              Abrir repositorio ↗
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

// ============================================================================
// MODAL DE AYUDA
// ============================================================================
function HelpModal({ onClose }) {
  useEffect(() => {
    const cerrarConEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', cerrarConEsc);
    return () => window.removeEventListener('keydown', cerrarConEsc);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card glass-card" role="dialog" aria-modal="true" aria-labelledby="titulo-ayuda" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="chapter-eyebrow">AYUDA</span>
            <h2 id="titulo-ayuda">Cómo ingresar los datos y qué revisa la app</h2>
          </div>
          <button type="button" className="btn-ghost" onClick={onClose} aria-label="Cerrar ayuda">✕</button>
        </div>

        <div className="modal-body-grid">
          <div className="help-block">
            <h3>Capítulo 1 · Funciones y derivadas</h3>
            <p>
              • <strong>Funciones:</strong> usa <code>x</code> como variable. Las potencias se escriben con <code>^</code> o <code>**</code> (ej. <code>x^3 - 4x + 1</code>) y puedes usar <code>sin(x)</code>, <code>cos(x)</code>, <code>exp(x)</code> o <code>e^x</code>, <code>ln(x)</code>, <code>sqrt(x)</code>, <code>abs(x)</code>.
            </p>
            <p>
              • <strong>Derivadas:</strong> <MathTex tex="f'(x)" /> y <MathTex tex="f''(x)" /> se calculan solas. En punto fijo la app sugiere funciones <MathTex tex="g(x)" /> y marca las que cumplen <MathTex tex="|g'(x_0)| < 1" />.
            </p>
            <p>
              • <strong>Números:</strong> además de decimales puedes escribir <code>1e-7</code>, <code>pi/2</code> o <code>1/3</code>.
            </p>
            <p>
              • <strong>Validaciones:</strong> en bisección y regla falsa se exige <MathTex tex="f(a)\cdot f(b) < 0" />. Newton, secante y raíces múltiples se detienen si el denominador se hace 0. En punto fijo se avisa si <MathTex tex="g(x)" /> no corresponde a <MathTex tex="f(x)" />.
            </p>
          </div>

          <div className="help-block">
            <h3>Capítulo 2 · Matrices hasta 8×8</h3>
            <p>
              • <strong>Cuadrícula o texto:</strong> elige el tamaño de 2×2 a 8×8. En modo texto separa las columnas con comas <code>,</code> y las filas con punto y coma <code>;</code>.
            </p>
            <p>
              • <strong>Radio espectral:</strong> <MathTex tex="\rho(T)" /> es el mayor valor absoluto de los valores propios de la matriz de iteración <MathTex tex="T" />. El método converge para cualquier vector inicial si y solo si <MathTex tex="\rho(T) < 1" />.
            </p>
            <p>
              • <strong>Validaciones:</strong> no se permiten celdas vacías ni ceros en la diagonal, y en SOR se avisa si <MathTex tex="\omega" /> está fuera de <MathTex tex="(0, 2)" />.
            </p>
          </div>

          <div className="help-block">
            <h3>Capítulo 3 · Interpolación</h3>
            <p>
              • <strong>Hasta 10 puntos:</strong> escríbelos en las casillas o como vectores <code>X</code> y <code>Y</code> separados por espacios.
            </p>
            <p>
              • <strong>Reservar el 20 % o 30 %:</strong> esos puntos no se usan para construir el polinomio; se guardan para medir el error de interpolación en ellos. Por defecto se usan todos los puntos (0 %).
            </p>
            <p>
              • <strong>Validaciones:</strong> no se permiten valores de <MathTex tex="x" /> repetidos, y en los splines los puntos se ordenan automáticamente.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}
