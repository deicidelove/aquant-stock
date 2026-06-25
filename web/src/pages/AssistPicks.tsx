import { useNavigate } from "react-router-dom";
import { usePicks, useBriefing } from "../hooks/queries";
import PicksPanel from "../components/PicksPanel";
import BriefingPanel from "../components/BriefingPanel";

export default function AssistPicks() {
  const nav = useNavigate();
  const picks = usePicks();
  const briefing = useBriefing();
  const go = (c: string) => nav(`/stock/${c}`);
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">选票</h1>
      {picks.isSuccess && <PicksPanel data={picks.data} onPick={go} />}
      {briefing.isSuccess && <BriefingPanel rows={briefing.data.rows} onPick={go} />}
    </div>
  );
}
