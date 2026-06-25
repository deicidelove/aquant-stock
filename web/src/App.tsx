import { Routes, Route } from "react-router-dom";
import Cockpit from "./pages/Cockpit";
import StockDetail from "./pages/StockDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Cockpit />} />
      <Route path="/stock/:code" element={<StockDetail />} />
    </Routes>
  );
}
