import { ReactNode } from "react";

interface AppShellProps {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function AppShell({ title, eyebrow, actions, children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-[#070b12] text-slate-100">
      <div className="mx-auto flex min-h-screen w-full max-w-[1480px] flex-col px-3 py-3 sm:px-5 lg:px-7">
        <header className="sticky top-0 z-20 mb-4 rounded-2xl border border-white/10 bg-slate-950/85 px-4 py-3 shadow-2xl shadow-black/20 backdrop-blur md:px-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              {eyebrow && (
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-300">
                  {eyebrow}
                </p>
              )}
              <h1 className="text-xl font-bold text-white sm:text-2xl">{title}</h1>
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
          </div>
        </header>

        <div className="flex-1">{children}</div>
      </div>
    </main>
  );
}
