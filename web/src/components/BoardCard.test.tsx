import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import BoardCard from "./BoardCard";

const card = {
  code: "600519", name: "贵州茅台", last_price: 1241.41, pct_chg: 2.17,
  kline: [{ date: "d1", close: 1200 }], signal: "买入/增持", one_liner: "低波反转",
  battle_plan: { ideal_buy: 1200, stop_loss: 1150, take_profit: 1400, position: "3~5成" },
  risk_level: "低", alerts: ["跌破止损"],
};

describe("BoardCard", () => {
  it("renders core fields + fires onOpen", () => {
    const onOpen = vi.fn();
    render(<BoardCard card={card} onOpen={onOpen} />);
    expect(screen.getByText("贵州茅台")).toBeInTheDocument();
    expect(screen.getByText(/1241.41/)).toBeInTheDocument();
    expect(screen.getByText(/买入/)).toBeInTheDocument();
    expect(screen.getByText("跌破止损")).toBeInTheDocument();
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    fireEvent.click(screen.getByText("贵州茅台"));
    expect(onOpen).toHaveBeenCalledWith("600519");
  });
  it("fires onRemove", () => {
    const onRemove = vi.fn();
    render(<BoardCard card={card} onRemove={onRemove} />);
    fireEvent.click(screen.getByRole("button", { name: "移除" }));
    expect(onRemove).toHaveBeenCalledWith("600519");
  });
});
