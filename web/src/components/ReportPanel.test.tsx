import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ReportPanel from "./ReportPanel";

const decision = {
  code: "600000", name: "浦发银行", date: "2026-06-23", close: 10.5,
  total_score: 72, signal: "买入/增持", one_liner: "策略契合强",
  risk_level: "低", risks: ["无显著风险信号"],
  battle_plan: { ideal_buy: 10.2, secondary_buy: 9.8, stop_loss: 9.5, take_profit: 12.0, position: "3~5成分批" },
  checklist: ["季度持有", "跌破止损减仓"],
};

describe("ReportPanel", () => {
  it("renders signal, score, battle plan and checklist", () => {
    render(<ReportPanel decision={decision} />);
    expect(screen.getByText("买入/增持")).toBeInTheDocument();
    expect(screen.getByText(/72/)).toBeInTheDocument();
    expect(screen.getByText(/9.5/)).toBeInTheDocument();     // 止损
    expect(screen.getByText(/季度持有/)).toBeInTheDocument();
  });
});
