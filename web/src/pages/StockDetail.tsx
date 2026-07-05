import { useParams, Link } from "react-router-dom";
import { useStockChart, useReport } from "../hooks/queries";
import ProKlineChart from "../components/ProKlineChart";
import ReportPanel from "../components/ReportPanel";

export default function StockDetail() {
  const { code = "" } = useParams();
  const chart = useStockChart(code);
  const report = useReport(code);
  const plan = report.isSuccess ? report.data.decision.battle_plan : undefined;
  return (
    <div className="space-y-4 p-4">
      <Link to="/" className="text-sm text-sky-400">← 返回</Link>
      <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <h2 className="text-lg font-bold text-slate-100">{code} K线</h2>
        {chart.isSuccess ? <ProKlineChart chart={chart.data} plan={plan} />
          : <div className="text-sm text-slate-400">{chart.isError ? "无K线数据" : "加载中…"}</div>}
      </section>
      {report.isSuccess ? <ReportPanel decision={report.data.decision} />
        : <div className="text-sm text-slate-400">{report.isError ? "无研判数据" : "研判加载中…"}</div>}
    </div>
  );
}
