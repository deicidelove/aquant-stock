import { useNavigate } from "react-router-dom";
import { useHoldings, useTrades, usePnl, useAddTrade, useDeleteTrade } from "../hooks/queries";
import HoldingsPanel from "../components/HoldingsPanel";
import PnlSummary from "../components/PnlSummary";
import TradeForm from "../components/TradeForm";
import TradesList from "../components/TradesList";

export default function AssistHoldings() {
  const nav = useNavigate();
  const holdings = useHoldings();
  const trades = useTrades();
  const pnl = usePnl();
  const add = useAddTrade();
  const del = useDeleteTrade();
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">持仓管理</h1>
      {pnl.isSuccess && <PnlSummary pnl={pnl.data} />}
      {holdings.isSuccess && <HoldingsPanel rows={holdings.data.rows} onPick={(c) => nav(`/stock/${c}`)} />}
      <TradeForm onSubmit={(t) => add.mutate(t)} />
      {trades.isSuccess && <TradesList rows={trades.data.rows} onDelete={(tid) => del.mutate(tid)} />}
    </div>
  );
}
