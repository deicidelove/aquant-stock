import { useState } from "react";
import type { TradeInput } from "../api/types";

export default function TradeForm({ onSubmit }: { onSubmit: (t: TradeInput) => void }) {
  const [date, setDate] = useState("");
  const [code, setCode] = useState("");
  const [side, setSide] = useState("buy");
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ date, code, side, shares: Number(shares), price: Number(price) });
  };

  return (
    <form onSubmit={submit} className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">录入交易</h2>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
        <label className="flex flex-col">日期<input aria-label="日期" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">代码<input aria-label="代码" value={code} onChange={(e) => setCode(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">方向<select aria-label="方向" value={side} onChange={(e) => setSide(e.target.value)} className="border p-1"><option value="buy">买入</option><option value="sell">卖出</option></select></label>
        <label className="flex flex-col">数量<input aria-label="数量" type="number" value={shares} onChange={(e) => setShares(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">价格<input aria-label="价格" type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} className="border p-1" /></label>
      </div>
      <button type="submit" className="mt-3 rounded bg-blue-600 px-3 py-1 text-white">记一笔</button>
    </form>
  );
}
