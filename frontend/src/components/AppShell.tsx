import type { ReactNode } from "react";

import performanceLabMark from "../assets/brand/mark.svg";
import {
  PRIMARY_NAVIGATION,
  SECONDARY_NAVIGATION,
  isSecondaryNavigationActive,
} from "../navigation";

interface AppShellProps {
  activePrimary?: (typeof PRIMARY_NAVIGATION)[number];
  activeSecondary?: string;
  children: ReactNode;
}

function slug(label: string) {
  return label.toLowerCase().replaceAll(" / ", "-").replaceAll(" ", "-");
}

export function AppShell({ activePrimary, activeSecondary, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to main content
      </a>
      <aside className="app-shell__sidebar">
        <a className="app-shell__brand" href="#overview" aria-label="Performance Lab home">
          <img className="app-shell__mark" src={performanceLabMark} alt="" aria-hidden="true" />
          <span>Performance Lab</span>
        </a>

        <nav aria-label="Primary navigation">
          <ul className="app-navigation">
            {PRIMARY_NAVIGATION.map((item) => (
              <li key={item}>
                <a
                  className="app-navigation__link"
                  data-current={item === activePrimary ? "true" : undefined}
                  href={`#${slug(item)}`}
                  aria-current={item === activePrimary ? "page" : undefined}
                >
                  {item}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="app-shell__secondary">
          {Object.entries(SECONDARY_NAVIGATION).map(([group, items]) => {
            const groupActive = items.some((item) =>
              isSecondaryNavigationActive(item, activeSecondary),
            );

            return (
              <details
                key={group}
                className="app-navigation-group"
                data-current={groupActive ? "true" : undefined}
                open={groupActive}
              >
                <summary className="app-navigation__group">
                  <span>{group}</span>
                </summary>
                <nav aria-label={group}>
                  <ul className="app-navigation app-navigation--secondary">
                    {items.map((item) => {
                      const active = isSecondaryNavigationActive(item, activeSecondary);
                      const reasonId = `nav-${slug(group)}-${slug(item.label)}-reason`;

                      return (
                        <li key={item.label}>
                          {item.href === null ? (
                            <span
                              className="app-navigation__link app-navigation__link--disabled"
                              data-disabled="true"
                              aria-disabled="true"
                              aria-describedby={reasonId}
                              title={item.disabledReason}
                            >
                              <span>{item.label}</span>
                              <span id={reasonId} className="app-navigation__disabled-reason">
                                Unavailable. {item.disabledReason}
                              </span>
                            </span>
                          ) : (
                            <a
                              className="app-navigation__link"
                              data-current={active ? "true" : undefined}
                              href={item.href}
                              aria-current={active ? "page" : undefined}
                            >
                              {item.label}
                            </a>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </nav>
              </details>
            );
          })}
        </div>
      </aside>
      <main id="main-content" className="app-shell__main" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}