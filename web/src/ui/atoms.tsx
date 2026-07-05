import type { ReactNode } from "react";

export function Card({ title, right, children }: { title?: string; right?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      {(title || right) && (
        <div className="mb-3 flex items-baseline justify-between">
          {title && <h2 className="text-base font-semibold text-slate-100">{title}</h2>}
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

const TONE: Record<string, string> = {
  up: "text-red-400", down: "text-green-400", neutral: "text-slate-100",
};

export function Stat({ label, value, tone = "neutral" }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="rounded bg-slate-800 p-2 text-center">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={"font-mono text-base font-semibold " + (TONE[tone] ?? TONE.neutral)}><span>{value}</span></div>
    </div>
  );
}

const BADGE: Record<string, string> = {
  red: "bg-red-500/20 text-red-300", green: "bg-green-500/20 text-green-300",
  amber: "bg-amber-500/20 text-amber-300", gray: "bg-slate-600/40 text-slate-300",
};

export function Badge({ children, tone = "gray" }: { children: ReactNode; tone?: string }) {
  return <span className={"rounded px-1.5 py-0.5 text-xs " + (BADGE[tone] ?? BADGE.gray)}>{children}</span>;
}

export function SignalTag({ signal }: { signal: string }) {
  const tone = signal.startsWith("买入") ? "green" : signal.startsWith("回避") ? "red" : "amber";
  const icon = signal.startsWith("买入") ? "🟢" : signal.startsWith("回避") ? "🔴" : "🟡";
  return <Badge tone={tone}><span>{icon}{signal}</span></Badge>;
}

export function UpdatedAt({ at, live }: { at: string; live: boolean }) {
  return (
    <span className="text-xs text-slate-500">
      更新于 {at} · <span className={live ? "text-amber-400" : "text-slate-500"}>{live ? "盘中实时" : "收盘定"}</span>
    </span>
  );
}
