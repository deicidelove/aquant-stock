import { Link } from "react-router-dom";

const LINKS: [string, string][] = [
  ["/", "驾驶舱"], ["/assist/picks", "选票"], ["/assist/holdings", "我的持仓"], ["/assist/review", "复盘"],
  ["/quant/backtest", "量化回测"], ["/quant/factors", "因子"],
];

export default function Nav() {
  return (
    <nav className="flex gap-4 border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm">
      {LINKS.map(([to, label]) => (
        <Link key={to} to={to} className="text-blue-700 hover:underline">{label}</Link>
      ))}
    </nav>
  );
}
