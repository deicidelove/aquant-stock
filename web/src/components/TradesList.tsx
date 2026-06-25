import type { Trade } from "../api/types";

export default function TradesList({ rows, onDelete }: { rows: Trade[]; onDelete?: (tid: number) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">交易流水</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-400">暂无流水。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-gray-500">
            <tr><th className="text-left">日期</th><th className="text-left">代码</th><th>方向</th><th className="text-right">数量</th><th className="text-right">价格</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.tid} className="border-b">
                <td>{t.date}</td><td>{t.code}</td>
                <td className="text-center">{t.side === "buy" ? "买入" : "卖出"}</td>
                <td className="text-right">{t.shares}</td><td className="text-right">{t.price}</td>
                <td className="text-right"><button onClick={() => onDelete?.(t.tid)} className="text-red-600">删除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
