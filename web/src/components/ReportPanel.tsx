import type { Decision } from "../api/types";

export default function ReportPanel({ decision: d }: { decision: Decision }) {
  const p = d.battle_plan;
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">{d.name} 研判</h2>
        <span className="rounded bg-gray-100 px-2 py-1 text-sm"><span>{d.signal}</span>（{d.total_score} 分 · 风险{d.risk_level}）</span>
      </div>
      <p className="mt-2 text-sm text-gray-700">{d.one_liner}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
        <Plan label="理想买点" value={p.ideal_buy} />
        <Plan label="加仓位" value={p.secondary_buy} />
        <Plan label="止损" value={p.stop_loss} />
        <Plan label="目标" value={p.take_profit} />
        <Plan label="仓位" value={p.position} />
      </div>
      <ul className="mt-3 list-disc pl-5 text-sm text-gray-600">
        {d.checklist.map((c, i) => <li key={i}>{c}</li>)}
      </ul>
      <div className="mt-2 text-xs text-gray-400">风险：{d.risks.join("；")}</div>
    </section>
  );
}

function Plan({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded bg-gray-50 p-2 text-center">
      <div className="text-gray-500">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
