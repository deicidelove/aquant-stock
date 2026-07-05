import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Board from "./pages/Board";
import Cockpit from "./pages/Cockpit";
import StockDetail from "./pages/StockDetail";
import AssistPicks from "./pages/AssistPicks";
import AssistHoldings from "./pages/AssistHoldings";
import AssistReview from "./pages/AssistReview";
import QuantBacktest from "./pages/QuantBacktest";
import QuantFactors from "./pages/QuantFactors";

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<Board />} />
        <Route path="/macro" element={<Cockpit />} />
        <Route path="/stock/:code" element={<StockDetail />} />
        <Route path="/assist/picks" element={<AssistPicks />} />
        <Route path="/assist/holdings" element={<AssistHoldings />} />
        <Route path="/assist/review" element={<AssistReview />} />
        <Route path="/quant/backtest" element={<QuantBacktest />} />
        <Route path="/quant/factors" element={<QuantFactors />} />
      </Routes>
    </>
  );
}
