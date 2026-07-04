import { useNavigate } from "react-router-dom";
import { usePicks, useBriefing, useTopScores } from "../hooks/queries";
import PicksPanel from "../components/PicksPanel";
import BriefingPanel from "../components/BriefingPanel";
import TopScoresPanel from "../components/TopScoresPanel";

export default function AssistPicks() {
  const nav = useNavigate();
  const picks = usePicks();
  const briefing = useBriefing();
  const top = useTopScores();
  const go = (c: string) => nav(`/stock/${c}`);
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold text-slate-100">选票</h1>
      {picks.isSuccess && <PicksPanel data={picks.data} onPick={go} />}
      {top.isSuccess && <TopScoresPanel data={top.data} onPick={go} />}
      {briefing.isSuccess && <BriefingPanel rows={briefing.data.rows} onPick={go} />}
    </div>
  );
}
