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
          {Object.entries(SECONDARY_NAVIGATION).map(([group, items]) => (
            <nav key={group} aria-label={group}>
              <p className="app-navigation__group">{group}</p>
              <ul className="app-navigation app-navigation--secondary">
                {items.map((item) => {
                  const active = isSecondaryNavigationActive(item, activeSecondary);
                  return (
                    <li key={item.label}>
                      {item.href === null ? (
                        <span
                          className="app-navigation__link app-navigation__link--disabled"
                          data-disabled="true"
                          aria-disabled="true"
                          title={item.disabledReason}
                        >
                          <span>{item.label}</span>
                          <span className="app-navigation__availability" aria-hidden="true">
                            Pending
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
          ))}
        </div>
      </aside>
      <main id="main-content" className="app-shell__main">
        {children}
      </main>
    </div>
  );
}
