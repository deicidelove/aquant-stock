import { useState } from "react";
import { useAiReport, useGenAiReport } from "../hooks/queries";

const ROLE: Record<string, string> = {
  technical: "技术面", capital: "资金面", news: "消息面", fundamental: "基本面",
};

function stanceCls(s: string): string {
  if (s.startsWith("买入")) return "bg-red-500/20 text-red-300";
  if (s.startsWith("回避")) return "bg-green-500/20 text-green-300";
  return "bg-amber-500/20 text-amber-300";
}

export default function AiReport({ code }: { code: string }) {
  const [polling, setPolling] = useState(false);
  const q = useAiReport(code, polling);
  const gen = useGenAiReport(code);
  const report = q.data?.report ?? null;

  // 报告到手后停止轮询
  if (polling && report) setPolling(false);

  const trigger = () => {
    setPolling(true);
    gen.mutate();
  };

  const generating = polling && !report;

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold text-slate-100">🧠 AI 投研报告</h2>
        <button
          onClick={trigger}
          disabled={generating}
          className="rounded bg-sky-600 px-3 py-1 text-sm text-white disabled:opacity-50"
        >
          {generating ? "生成中…" : report ? "重新生成" : "生成报告"}
        </button>
      </div>

      {!report && !generating && (
        <p className="text-sm text-slate-500">点击「生成报告」调用多智能体分析（技术/资金/消息/基本面 + 多空辩论）。</p>
      )}
      {generating && <p className="text-sm text-slate-400">多智能体分析中，约需十几秒到一分钟…</p>}

      {report && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded px-2 py-0.5 text-sm font-bold ${stanceCls(report.verdict.stance)}`}>
              {report.verdict.stance}
            </span>
            {report.verdict.position && (
              <span className="text-sm text-slate-400">建议仓位：{report.verdict.position}</span>
            )}
            <span className="text-xs text-slate-600">{report.as_of} · {report.llm_used ? "LLM" : "规则"}</span>
          </div>
          <p className="text-sm text-slate-200">{report.verdict.reason}</p>

          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(report.analysts).map(([k, v]) => (
              <div key={k} className="rounded border border-slate-700 bg-slate-950/40 p-3">
                <div className="mb-1 text-xs font-bold text-sky-400">{ROLE[k] ?? k}分析师</div>
                <p className="text-sm text-slate-300">{v}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded border border-red-500/30 bg-red-500/5 p-3">
              <div className="mb-1 text-xs font-bold text-red-300">🐂 多头逻辑</div>
              <p className="text-sm text-slate-300">{report.debate.bull}</p>
            </div>
            <div className="rounded border border-green-500/30 bg-green-500/5 p-3">
              <div className="mb-1 text-xs font-bold text-green-300">🐻 空头逻辑</div>
              <p className="text-sm text-slate-300">{report.debate.bear}</p>
            </div>
          </div>

          {report.verdict.risks.length > 0 && (
            <div className="text-xs text-slate-400">风险：{report.verdict.risks.join("；")}</div>
          )}
          <div className="text-xs text-slate-600">仅供研究，不构成投资建议。</div>
        </div>
      )}
    </section>
  );
}
