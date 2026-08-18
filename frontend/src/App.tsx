import { PRIMARY_NAVIGATION } from "./navigation";
import "./foundation.css";

export function App() {
  return (
    <div className="foundation-shell">
      <aside className="foundation-sidebar">
        <a className="foundation-brand" href="#main-content" aria-label="Performance Lab home">
          <span aria-hidden="true">◈</span>
          <span>Performance Lab</span>
        </a>
        <nav aria-label="Primary navigation">
          <ul className="foundation-nav-list">
            {PRIMARY_NAVIGATION.map((item, index) => (
              <li key={item}>
                <a
                  className={index === 0 ? "foundation-nav-link is-current" : "foundation-nav-link"}
                  href={`#${item.toLowerCase().replaceAll(" ", "-")}`}
                  aria-current={index === 0 ? "page" : undefined}
                >
                  {item}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <main id="main-content" className="foundation-content">
        <p className="foundation-eyebrow">UIF-001 · frontend foundation</p>
        <h1>Performance Lab browser surface is ready for product slices.</h1>
        <p className="foundation-copy">
          This shell proves the React, TypeScript, Vite and validation boundary only. Overview,
          Runs, Test a model and Compare are implemented in their dedicated product tasks against
          the canonical design and application contracts.
        </p>
        <section className="foundation-status" aria-labelledby="foundation-status-title">
          <h2 id="foundation-status-title">Foundation contract</h2>
          <ul>
            <li>Task-model-first navigation is wired from one typed source.</li>
            <li>Development and preview servers bind to loopback.</li>
            <li>Formatting, lint, typecheck, tests and production build have explicit gates.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}
