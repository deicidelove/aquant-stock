import { useNewsSentiment } from "../hooks/queries";
import type { NewsItem } from "../api/types";

const SENT: Record<number, { dot: string; label: string }> = {
  1: { dot: "bg-red-400", label: "利好" },
  [-1]: { dot: "bg-green-400", label: "利空" },
  0: { dot: "bg-slate-500", label: "" },
};

function scoreColor(s: number): string {
  if (s >= 60) return "text-red-400";
  if (s <= 40) return "text-green-400";
  return "text-slate-300";
}

function NewsRow({ n }: { n: NewsItem }) {
  const st = SENT[n.sent] ?? SENT[0];
  const body = (
    <span className="flex items-start gap-2">
      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${st.dot}`} />
      <span className="min-w-0">
        <span className="text-slate-200">{n.title}</span>
        <span className="ml-2 whitespace-nowrap text-xs text-slate-500">{n.time.slice(5, 16)}</span>
      </span>
    </span>
  );
  return (
    <li className="text-sm leading-snug">
      {n.url ? <a href={n.url} target="_blank" rel="noreferrer" className="hover:underline">{body}</a> : body}
    </li>
  );
}

export default function NewsSentiment({ limit = 30, compact = false }: { limit?: number; compact?: boolean }) {
  const q = useNewsSentiment(limit);
  if (!q.isSuccess) {
    return <div className="text-sm text-slate-400">{q.isLoading ? "消息面加载中…" : "暂无消息面数据"}</div>;
  }
  const d = q.data;
  const show = compact ? d.items.slice(0, 3) : d.items;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold text-slate-100">📰 消息面</h2>
        <div className="text-sm">
          <span className="text-slate-400">情绪 </span>
          <span className={`font-bold ${scoreColor(d.score)}`}>{d.score}</span>
          <span className={`ml-1 ${scoreColor(d.score)}`}>{d.label}</span>
          <span className="ml-2 text-xs text-slate-500">利好{d.pos}·利空{d.neg}·中性{d.neutral}</span>
        </div>
      </div>
      {d.items.length === 0 ? (
        <p className="text-sm text-slate-500">暂无快讯（盘中由后台任务抓取）。</p>
      ) : (
        <ul className={compact ? "space-y-1.5" : "max-h-96 space-y-1.5 overflow-y-auto"}>
          {show.map((n, i) => <NewsRow key={`${n.time}-${i}`} n={n} />)}
        </ul>
      )}
    </div>
  );
}
