import { ReactNode } from "react";

interface AppShellProps {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}

function BrandMark() {
  return (
    <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0 text-primary" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 24L14 6h4l10 18h-5l-2-4H11l-2 4H4Z" fill="currentColor" />
      <path d="M13.2 16h5.6L16 10.4 13.2 16Z" fill="hsl(var(--background))" />
    </svg>
  );
}

export function AppShell({ title, eyebrow, actions, children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-3 py-3 sm:px-5 lg:px-6">
        <header className="sticky top-0 z-20 mb-4 overflow-hidden border border-border bg-sidebar/95 shadow-lg shadow-black/40 backdrop-blur">
          <div className="h-[3px] w-full bg-diagonal-stripes" />
          <div className="flex flex-col gap-3 px-3 py-3 sm:px-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center gap-3">
              <BrandMark />
              <div className="min-w-0">
                {eyebrow && (
                  <p className="truncate text-[0.68rem] font-semibold uppercase tracking-[0.28em] text-muted-foreground sm:text-xs">
                    {eyebrow}
                  </p>
                )}
                <h1 className="truncate font-display text-xl font-bold uppercase tracking-wide text-foreground sm:text-2xl">
                  {title}
                </h1>
              </div>
            </div>

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
