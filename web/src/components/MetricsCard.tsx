const FMT: [string, string, (v: number) => string][] = [
  ["annual_return", "年化", (v) => (v * 100).toFixed(1) + "%"],
  ["sharpe", "夏普", (v) => v.toFixed(2)],
  ["max_drawdown", "最大回撤", (v) => (v * 100).toFixed(1) + "%"],
  ["win_rate", "胜率", (v) => (v * 100).toFixed(1) + "%"],
];

export default function MetricsCard({ metrics }: { metrics: Record<string, number> }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">绩效</h2>
      <div className="mt-2 grid grid-cols-2 gap-3 text-center sm:grid-cols-4">
        {FMT.map(([k, label, fmt]) => (
          <div key={k} className="rounded bg-gray-50 p-2">
            <div className="text-gray-500 text-sm">{label}</div>
            <div className="text-base font-semibold"><span>{k in metrics ? fmt(metrics[k]) : "—"}</span></div>
          </div>
        ))}
      </div>
    </section>
  );
}
