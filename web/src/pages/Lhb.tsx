import { useState } from "react";
import { Link } from "react-router-dom";
import { useLhbToday, useLhbStock } from "../hooks/queries";
import type { LhbRow } from "../api/types";
import LhbSeats from "../components/LhbSeats";

function money(v: number | null): string {
  if (v == null) return "-";
  const yi = v / 1e8;
  return Math.abs(yi) >= 0.01 ? `${yi.toFixed(2)}亿` : `${(v / 1e4).toFixed(0)}万`;
}

const TAG_CLS: Record<string, string> = {
  机构: "bg-blue-500/20 text-blue-300",
  北向: "bg-cyan-500/20 text-cyan-300",
};
function tagCls(t: string): string {
  return TAG_CLS[t] ?? "bg-amber-500/20 text-amber-300"; // 游资别名 → 橙
}

function SeatDrawer({ code }: { code: string }) {
  const q = useLhbStock(code);
  if (q.isLoading) return <div className="p-2 text-xs text-slate-500">加载席位…</div>;
  if (!q.isSuccess) return <div className="p-2 text-xs text-slate-500">无席位数据</div>;
  return (
    <div className="border-t border-slate-800 bg-slate-950/50 p-3">
      {q.data.reason && <div className="mb-2 text-xs text-slate-400">上榜原因：{q.data.reason}</div>}
      <LhbSeats buy={q.data.buy} sell={q.data.sell} />
    </div>
  );
}

function Row({ r }: { r: LhbRow }) {
  const [open, setOpen] = useState(false);
  const net = r.lhb_net_buy ?? 0;
  return (
    <>
      <tr className="cursor-pointer border-b border-slate-800 hover:bg-slate-800/50" onClick={() => setOpen((o) => !o)}>
        <td className="py-2 pl-2">
          <Link to={`/stock/${r.code}`} className="text-sky-400 hover:underline" onClick={(e) => e.stopPropagation()}>
            {r.name}
          </Link>
          <span className="ml-1 text-xs text-slate-500">{r.code}</span>
        </td>
        <td className={`text-right ${(r.pct_chg ?? 0) >= 0 ? "text-red-400" : "text-green-400"}`}>
          {r.pct_chg == null ? "-" : `${r.pct_chg.toFixed(2)}%`}
        </td>
        <td className={`text-right ${net >= 0 ? "text-red-400" : "text-green-400"}`}>{money(r.lhb_net_buy)}</td>
        <td className="hidden pl-3 text-xs text-slate-400 sm:table-cell">{r.reason}</td>
        <td className="py-2 pr-2 text-right">
          <span className="inline-flex flex-wrap justify-end gap-1">
            {r.tags.map((t) => (
              <span key={t} className={`rounded px-1 text-xs ${tagCls(t)}`}>{t}</span>
            ))}
          </span>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={5}><SeatDrawer code={r.code} /></td>
        </tr>
      )}
    </>
  );
}

export default function Lhb() {
  const q = useLhbToday();
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold text-slate-100">🐉 龙虎榜</h1>
        {q.isSuccess && q.data.date && <span className="text-sm text-slate-400">{q.data.date}</span>}
      </div>
      {q.isLoading && <div className="text-sm text-slate-400">加载中…</div>}
      {q.isSuccess && q.data.rows.length === 0 && (
        <p className="text-sm text-slate-500">暂无龙虎榜数据（收盘后由后台任务抓取）。</p>
      )}
      {q.isSuccess && q.data.rows.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-900">
          <table className="w-full text-sm text-slate-100">
            <thead className="text-xs text-slate-500">
              <tr className="border-b border-slate-700">
                <th className="py-2 pl-2 text-left">个股</th>
                <th className="text-right">涨跌</th>
                <th className="text-right">净买额</th>
                <th className="hidden pl-3 text-left sm:table-cell">上榜原因</th>
                <th className="py-2 pr-2 text-right">席位</th>
              </tr>
            </thead>
            <tbody>
              {q.data.rows.map((r) => <Row key={r.code} r={r} />)}
            </tbody>
          </table>
          <div className="p-2 text-xs text-slate-600">点击行展开买卖席位；净买额红=净买入。</div>
        </div>
      )}
    </div>
  );
}
