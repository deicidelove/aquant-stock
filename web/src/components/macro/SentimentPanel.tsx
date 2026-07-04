import type { Sentiment } from "../../api/types";
import { Card, Stat, Badge } from "../../ui/atoms";

export default function SentimentPanel({ data: d }: { data: Sentiment }) {
  const tone = d.score >= 60 ? "red" : d.score >= 40 ? "amber" : "green";
  return (
    <Card title="市场情绪" right={<Badge tone={tone}><span>{d.label}<span> {d.score}</span></span></Badge>}>
      <div className="grid grid-cols-4 gap-2">
        <Stat label="上涨" value={d.up} tone="up" />
        <Stat label="下跌" value={d.down} tone="down" />
        <Stat label="涨停" value={d.limit_up} tone="up" />
        <Stat label="跌停" value={d.limit_down} tone="down" />
      </div>
      <div className="mt-2 text-xs text-slate-400">成交额 {(d.amount / 1e8).toFixed(0)} 亿</div>
    </Card>
  );
}
