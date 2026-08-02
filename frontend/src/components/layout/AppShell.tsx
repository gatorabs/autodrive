import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

interface AppShellProps {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/manual-mode", label: "Manual Drive" },
];

function BrandMark() {
  return (
    <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0 text-primary" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="13" stroke="currentColor" strokeWidth="2.4" />
      <circle cx="16" cy="16" r="4.5" stroke="currentColor" strokeWidth="2" />
      <path d="M16 4.5V11.5" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M7 21L11.7 18.3" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M25 21L20.3 18.3" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export function AppShell({ title, eyebrow, actions, children }: AppShellProps) {
  const location = useLocation();

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-3 py-3 sm:px-5 lg:px-6">
        <header className="sticky top-0 z-20 mb-4 rounded-2xl border border-border bg-background/95 px-3 py-3 shadow-lg shadow-black/20 backdrop-blur sm:px-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <BrandMark />
              <div className="min-w-0">
                {eyebrow && (
                  <p className="truncate text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground sm:text-xs">
                    {eyebrow}
                  </p>
                )}
                <h1 className="truncate text-lg font-semibold text-foreground sm:text-2xl">{title}</h1>
              </div>
            </div>

            <nav className="flex items-center gap-1 self-start rounded-xl border border-border bg-surface p-1 lg:self-auto">
              {NAV_ITEMS.map((item) => {
                const isActive = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                      isActive
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:bg-surface-alt hover:text-foreground"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {actions && (
              <div className="grid grid-cols-1 gap-2 sm:flex sm:flex-wrap sm:items-center lg:justify-end">
                {actions}
              </div>
            )}
          </div>
        </header>

        <div className="flex-1">{children}</div>
      </div>
    </main>
  );
}
