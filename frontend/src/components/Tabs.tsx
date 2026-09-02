import type { ReactNode } from "react";

interface TabItem<T extends string> {
  value: T;
  label: string;
  panel: ReactNode;
}

interface TabsProps<T extends string> {
  label: string;
  value: T;
  items: readonly TabItem<T>[];
  onChange: (value: T) => void;
}

export function Tabs<T extends string>({ label, value, items, onChange }: TabsProps<T>) {
  const active = items.find((item) => item.value === value);
  return (
    <div className="tabs">
      <div className="tabs__list" role="tablist" aria-label={label}>
        {items.map((item) => {
          const selected = item.value === value;
          return (
            <button
              className="tabs__tab"
              id={`tab-${item.value}`}
              key={item.value}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`panel-${item.value}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(item.value)}
            >
              {item.label}
            </button>
          );
        })}
      </div>
      {active ? (
        <div
          className="tabs__panel"
          id={`panel-${active.value}`}
          role="tabpanel"
          aria-labelledby={`tab-${active.value}`}
        >
          {active.panel}
        </div>
      ) : null}
    </div>
  );
}
