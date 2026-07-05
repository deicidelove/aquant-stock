import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useBoard, useAddWatch, useRemoveWatch, useSentiment } from "../hooks/queries";
import BoardCard from "../components/BoardCard";

export default function Board() {
  const nav = useNavigate();
  const board = useBoard();
  const add = useAddWatch();
  const remove = useRemoveWatch();
  const sentiment = useSentiment();
  const [code, setCode] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) { add.mutate(code.trim()); setCode(""); }
  };
  const s = sentiment.data;
  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold text-slate-100">📋 我的看板</h1>
        {sentiment.isSuccess && s && (
          <div className="text-sm text-slate-400">
            大盘 <span className={s.score >= 50 ? "text-red-400" : "text-green-400"}>{s.label}</span>
            {" "}· 涨 {s.up}/跌 {s.down} · 涨停 {s.limit_up}
          </div>
        )}
      </div>
      <form onSubmit={submit} className="flex gap-2">
        <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="输入代码加自选(如 600519)"
               className="flex-1 rounded border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100" />
        <button type="submit" className="rounded bg-sky-600 px-3 py-1 text-sm text-white">加自选</button>
      </form>
      {board.isSuccess && board.data.rows.length === 0 && (
        <p className="text-sm text-slate-500">还没有自选/持仓。上方输入代码加自选，或去「我的持仓」录入交易。</p>
      )}
      {board.isSuccess && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {board.data.rows.map((c) => (
            <BoardCard key={c.code} card={c} onOpen={(x) => nav(`/stock/${x}`)} onRemove={(x) => remove.mutate(x)} />
          ))}
        </div>
      )}
    </div>
  );
}
