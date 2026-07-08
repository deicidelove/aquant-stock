import { useScorecard, useScorecardSummary, usePnl } from "../hooks/queries";
import ScorecardPanel from "../components/ScorecardPanel";
import ScorecardSummary from "../components/ScorecardSummary";
import PnlSummary from "../components/PnlSummary";

export default function AssistReview() {
  const scorecard = useScorecard();
  const summary = useScorecardSummary();
  const pnl = usePnl();
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">复盘</h1>
      {summary.isSuccess && <ScorecardSummary data={summary.data} />}
      {pnl.isSuccess && <PnlSummary pnl={pnl.data} />}
      {scorecard.isSuccess && <ScorecardPanel data={scorecard.data} />}
    </div>
  );
}
