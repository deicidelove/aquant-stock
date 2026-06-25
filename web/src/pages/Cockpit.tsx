import { useNavigate } from "react-router-dom";
import { useOverview, useSectors, usePicks, useTopScores } from "../hooks/queries";
import OverviewPanel from "../components/OverviewPanel";
import SectorPanel from "../components/SectorPanel";
import PicksPanel from "../components/PicksPanel";
import TopScoresPanel from "../components/TopScoresPanel";

export default function Cockpit() {
  const nav = useNavigate();
  const overview = useOverview();
  const sectors = useSectors();
  const picks = usePicks();
  const top = useTopScores();
  const goPick = (code: string) => nav(`/stock/${code}`);
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">🛰 驾驶舱</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        {overview.isSuccess && <OverviewPanel data={overview.data} />}
        {sectors.isSuccess && <SectorPanel data={sectors.data} />}
        {picks.isSuccess && <PicksPanel data={picks.data} onPick={goPick} />}
        {top.isSuccess && <TopScoresPanel data={top.data} onPick={goPick} />}
      </div>
    </div>
  );
}
