import { useParams, Link } from "react-router-dom";
import { useStockChart, useReport, useLhbStock } from "../hooks/queries";
import ProKlineChart from "../components/ProKlineChart";
import ReportPanel from "../components/ReportPanel";
import LhbSeats from "../components/LhbSeats";
import AiReport from "../components/AiReport";

export default function StockDetail() {
  const { code = "" } = useParams();
  const chart = useStockChart(code);
  const report = useReport(code);
  const lhb = useLhbStock(code);
  const plan = report.isSuccess ? report.data.decision.battle_plan : undefined;
  const hasLhb = lhb.isSuccess && (lhb.data.buy.length > 0 || lhb.data.sell.length > 0);
  return (
    <div className="space-y-4 p-4">
      <Link to="/" className="text-sm text-sky-400">← 返回</Link>
      <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <h2 className="text-lg font-bold text-slate-100">{code} K线</h2>
        {chart.isSuccess ? <ProKlineChart chart={chart.data} plan={plan} />
          : <div className="text-sm text-slate-400">{chart.isError ? "无K线数据" : "加载中…"}</div>}
      </section>
      <AiReport code={code} />
      {report.isSuccess ? <ReportPanel decision={report.data.decision} />
        : <div className="text-sm text-slate-400">{report.isError ? "无研判数据" : "研判加载中…"}</div>}
      {hasLhb && (
        <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
          <h2 className="mb-2 text-lg font-bold text-slate-100">
            🐉 龙虎榜席位 <span className="text-sm font-normal text-slate-500">{lhb.data.date}</span>
          </h2>
          {lhb.data.reason && <div className="mb-2 text-xs text-slate-400">上榜原因：{lhb.data.reason}</div>}
          <LhbSeats buy={lhb.data.buy} sell={lhb.data.sell} />
        </section>
      )}
    </div>
  );
}
