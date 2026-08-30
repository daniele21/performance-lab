import type { ReactNode } from "react";

import performanceLabMark from "../assets/brand/mark.svg";
import { PRIMARY_NAVIGATION, SECONDARY_NAVIGATION } from "../navigation";

type SecondaryItem = (typeof SECONDARY_NAVIGATION)[keyof typeof SECONDARY_NAVIGATION][number];

interface AppShellProps {
  activePrimary?: (typeof PRIMARY_NAVIGATION)[number];
  activeSecondary?: SecondaryItem;
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
                {items.map((item) => (
                  <li key={item}>
                    <a
                      className="app-navigation__link"
                      data-current={item === activeSecondary ? "true" : undefined}
                      href={`#${slug(item)}`}
                      aria-current={item === activeSecondary ? "page" : undefined}
                    >
                      {item}
                    </a>
                  </li>
                ))}
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
