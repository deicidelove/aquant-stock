import { useState } from "react";
import type { QuantWeights, BacktestParams } from "../api/types";

export default function BacktestForm({ presets, onSubmit }: { presets: QuantWeights; onSubmit: (p: BacktestParams) => void }) {
  const [preset, setPreset] = useState<keyof QuantWeights>("ic");
  const [weights, setWeights] = useState<Record<string, number>>({ ...presets.ic });
  const [capital, setCapital] = useState("1000000");
  const [topN, setTopN] = useState("5");
  const [rebalance, setRebalance] = useState("5");
  const [minHistory, setMinHistory] = useState("250");

  const pickPreset = (name: keyof QuantWeights) => {
    setPreset(name);
    setWeights({ ...presets[name] });
  };
  const setW = (f: string, v: string) => setWeights((w) => ({ ...w, [f]: Number(v) }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      capital: Number(capital), weights, top_n: Number(topN),
      rebalance_every: Number(rebalance), min_history: Number(minHistory),
    });
  };

  return (
    <form onSubmit={submit} className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">回测配置</h2>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <label className="flex flex-col">权重预设
          <select aria-label="权重预设" value={preset} onChange={(e) => pickPreset(e.target.value as keyof QuantWeights)} className="border p-1">
            <option value="ic">IC加权</option><option value="momentum">动量风格</option>
          </select>
        </label>
        <label className="flex flex-col">初始金额<input aria-label="初始金额" type="number" value={capital} onChange={(e) => setCapital(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">Top-N<input aria-label="Top-N" type="number" value={topN} onChange={(e) => setTopN(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">调仓周期<input aria-label="调仓周期" type="number" value={rebalance} onChange={(e) => setRebalance(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">最小历史<input aria-label="最小历史" type="number" value={minHistory} onChange={(e) => setMinHistory(e.target.value)} className="border p-1" /></label>
      </div>
      <div className="mt-3 text-sm">
        <div className="text-gray-500">因子权重（可调）</div>
        <div className="mt-1 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {Object.keys(weights).map((f) => (
            <label key={f} className="flex items-center justify-between gap-1">
              <span className="truncate">{f}</span>
              <input aria-label={f} type="number" step="0.01" value={weights[f]} onChange={(e) => setW(f, e.target.value)} className="w-20 border p-1" />
            </label>
          ))}
        </div>
      </div>
      <button type="submit" className="mt-3 rounded bg-blue-600 px-3 py-1 text-white">运行回测</button>
    </form>
  );
}
