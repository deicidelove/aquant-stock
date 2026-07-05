import { Link } from "react-router-dom";

const PRIMARY: [string, string][] = [["/", "看板"], ["/assist/holdings", "我的持仓"]];
const ADVANCED: [string, string][] = [
  ["/macro", "驾驶舱"], ["/assist/picks", "选票"], ["/assist/review", "复盘"],
  ["/quant/backtest", "量化回测"], ["/quant/factors", "因子"],
];

export default function Nav() {
  return (
    <nav className="flex items-center gap-4 border-b border-slate-700 bg-slate-800 px-4 py-2 text-sm">
      {PRIMARY.map(([to, label]) => (
        <Link key={to} to={to} className="text-sky-400 hover:underline">{label}</Link>
      ))}
      <details className="relative">
        <summary className="cursor-pointer list-none text-slate-400"><span>高级</span> ▾</summary>
        <div className="absolute z-10 mt-1 flex flex-col gap-1 rounded border border-slate-700 bg-slate-900 p-2">
          {ADVANCED.map(([to, label]) => (
            <Link key={to} to={to} className="whitespace-nowrap text-sky-400 hover:underline">{label}</Link>
          ))}
        </div>
      </details>
    </nav>
  );
}
