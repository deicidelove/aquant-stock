import type { BoardCard as Card } from "../api/types";
import EChart from "../charts/EChart";
import { buildSparklineOption } from "../charts/options";
import { SignalTag, Badge } from "../ui/atoms";

export default function BoardCard({ card, onOpen, onRemove }: {
  card: Card; onOpen?: (code: string) => void; onRemove?: (code: string) => void;
}) {
  const p = card.battle_plan;
  const up = (card.pct_chg ?? 0) >= 0;
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-3">
      <div className="flex items-start justify-between">
        <button className="text-left" onClick={() => onOpen?.(card.code)}>
          <div className="font-semibold text-slate-100">{card.name}</div>
          <div className="text-xs text-slate-500">{card.code}</div>
        </button>
        <div className="text-right">
          <div className="font-mono text-lg text-slate-100">{card.last_price ?? "—"}</div>
          <div className={"text-sm " + (up ? "text-red-400" : "text-green-400")}>
            {up ? "+" : ""}{card.pct_chg ?? "—"}%
          </div>
        </div>
      </div>
      <div className="my-2 h-10"><EChart option={buildSparklineOption(card.kline)} height={40} /></div>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {card.signal && <SignalTag signal={card.signal} />}
        {card.risk_level && <Badge tone={card.risk_level === "高" ? "red" : card.risk_level === "中" ? "amber" : "gray"}><span>风险{card.risk_level}</span></Badge>}
        {card.alerts.map((a) => <Badge key={a} tone="red"><span>{a}</span></Badge>)}
      </div>
      {card.one_liner && <p className="mt-2 text-xs text-slate-300">{card.one_liner}</p>}
      <div className="mt-2 grid grid-cols-4 gap-1 text-center text-xs">
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">买点</div><div className="text-slate-200">{p.ideal_buy ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">止损</div><div className="text-slate-200">{p.stop_loss ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">目标</div><div className="text-slate-200">{p.take_profit ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">仓位</div><div className="text-slate-200">{p.position ?? "—"}</div></div>
      </div>
      {onRemove && <div className="mt-2 text-right"><button onClick={() => onRemove(card.code)} className="text-xs text-slate-500 hover:text-red-400">移除</button></div>}
    </section>
  );
}
