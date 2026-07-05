import type { FactorIcRow } from "../api/types";
import EChart from "../charts/EChart";
import { buildFactorIcBarOption } from "../charts/options";

export default function FactorIcPanel({ rows }: { rows: FactorIcRow[] }) {
  if (rows.length === 0) {
    return (
      <section className="rounded-lg border border-slate-700 p-4">
        <h2 className="text-lg font-bold">因子 IC / IR</h2>
        <p className="mt-2 text-sm text-slate-500">暂无因子数据。</p>
      </section>
    );
  }
  return (
    <section className="rounded-lg border border-slate-700 p-4">
      <h2 className="text-lg font-bold">因子 IC / IR</h2>
      <EChart option={buildFactorIcBarOption(rows)} height={Math.max(160, rows.length * 28)} />
      <table className="mt-2 w-full text-sm">
        <thead className="text-slate-400"><tr><th className="text-left">因子</th><th className="text-right">IC均值</th><th className="text-right">IR</th><th className="text-right">IC胜率</th><th className="text-right">N</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.factor} className="border-b border-slate-800">
              <td>{r.factor}</td><td className="text-right">{r.ic_mean}</td><td className="text-right">{r.ir}</td><td className="text-right">{r.ic_win}</td><td className="text-right">{r.n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
