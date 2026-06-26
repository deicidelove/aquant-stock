import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BacktestForm from "./BacktestForm";
import MetricsCard from "./MetricsCard";

const presets = { ic: { mom_20: -0.41, volatility_20: 0.47 }, momentum: { mom_20: 1.0 } };

describe("BacktestForm / MetricsCard", () => {
  it("submits weights map + params (preset populated, editable)", () => {
    const onSubmit = vi.fn();
    render(<BacktestForm presets={presets} onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("Top-N"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ top_n: 3, weights: expect.objectContaining({ mom_20: -0.41, volatility_20: 0.47 }) }),
    );
  });
  it("MetricsCard shows annual/sharpe/drawdown/winrate (rendered as %/2dp)", () => {
    render(<MetricsCard metrics={{ annual_return: 0.18, sharpe: 1.4, max_drawdown: -0.22, win_rate: 0.55 }} />);
    expect(screen.getByText("1.40")).toBeInTheDocument();
    expect(screen.getByText("-22.0%")).toBeInTheDocument();
    expect(screen.getByText("18.0%")).toBeInTheDocument();
  });
});
