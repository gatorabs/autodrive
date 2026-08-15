import { ReactNode } from "react";

interface PanelProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, subtitle, action, children, className = "" }: PanelProps) {
  return (
    <section className={`border border-border bg-surface shadow-lg shadow-black/20 ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-3 border-b border-border bg-surface-alt/60 px-4 py-2.5">
          <div>
            {title && (
              <h2 className="font-display text-sm font-bold uppercase tracking-[0.14em] text-foreground">{title}</h2>
            )}
            {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}
