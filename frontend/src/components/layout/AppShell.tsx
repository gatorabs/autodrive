import { ReactNode } from "react";

interface AppShellProps {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function AppShell({ title, eyebrow, actions, children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-3 py-3 sm:px-5 lg:px-6">
        <header className="sticky top-0 z-20 mb-4 rounded-2xl border border-slate-800 bg-slate-950/95 px-3 py-3 shadow-lg shadow-black/20 backdrop-blur sm:px-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              {eyebrow && (
                <p className="truncate text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500 sm:text-xs">
                  {eyebrow}
                </p>
              )}
              <h1 className="truncate text-lg font-semibold text-white sm:text-2xl">{title}</h1>
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
