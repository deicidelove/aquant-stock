import { useParams, Link } from "react-router-dom";
import { useKline, useReport } from "../hooks/queries";
import EChart from "../charts/EChart";
import { buildKlineOption } from "../charts/options";
import ReportPanel from "../components/ReportPanel";

export default function StockDetail() {
  const { code = "" } = useParams();
  const kline = useKline(code);
  const report = useReport(code);
  return (
    <div className="space-y-4 p-4">
      <Link to="/" className="text-sm text-blue-600">← 返回驾驶舱</Link>
      <section className="rounded-lg border border-gray-200 p-4">
        <h2 className="text-lg font-bold">{code} K线</h2>
        {kline.isSuccess ? <EChart option={buildKlineOption(kline.data.bars)} height={360} />
          : <div className="text-sm text-gray-400">{kline.isError ? "无K线数据" : "加载中…"}</div>}
      </section>
      {report.isSuccess ? <ReportPanel decision={report.data.decision} />
        : <div className="text-sm text-gray-400">{report.isError ? "无研判数据" : "研判加载中…"}</div>}
    </div>
  );
}
