import type { LhbSeat } from "../api/types";

const TYPE_STYLE: Record<string, { label: string; cls: string }> = {
  inst: { label: "机构", cls: "bg-blue-500/20 text-blue-300" },
  north: { label: "北向", cls: "bg-cyan-500/20 text-cyan-300" },
  hotmoney: { label: "游资", cls: "bg-amber-500/20 text-amber-300" },
  normal: { label: "普通", cls: "bg-slate-600/40 text-slate-300" },
};

function money(v: number | null): string {
  if (v == null) return "-";
  const yi = v / 1e8;
  if (Math.abs(yi) >= 0.01) return `${yi.toFixed(2)}亿`;
  return `${(v / 1e4).toFixed(0)}万`;
}

function SeatCol({ title, seats, kind }: { title: string; seats: LhbSeat[]; kind: "buy" | "sell" }) {
  const amtCls = kind === "buy" ? "text-red-400" : "text-green-400";
  return (
    <div className="flex-1">
      <div className={`mb-1 text-xs font-bold ${amtCls}`}>{title}</div>
      {seats.length === 0 && <div className="text-xs text-slate-500">无</div>}
      <ul className="space-y-1">
        {seats.map((s) => {
          const t = TYPE_STYLE[s.seat_type] ?? TYPE_STYLE.normal;
          return (
            <li key={`${kind}-${s.rank}`} className="flex items-center justify-between gap-2 text-xs">
              <span className="flex min-w-0 items-center gap-1">
                <span className={`shrink-0 rounded px-1 ${t.cls}`}>{s.hotmoney_name ?? t.label}</span>
                <span className="truncate text-slate-300" title={s.seat}>{s.seat}</span>
              </span>
              <span className={`shrink-0 ${amtCls}`}>{money(kind === "buy" ? s.buy : s.sell)}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function LhbSeats({ buy, sell }: { buy: LhbSeat[]; sell: LhbSeat[] }) {
  return (
    <div className="flex gap-4">
      <SeatCol title="买入前五" seats={buy} kind="buy" />
      <SeatCol title="卖出前五" seats={sell} kind="sell" />
    </div>
  );
}
