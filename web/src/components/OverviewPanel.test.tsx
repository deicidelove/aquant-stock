import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import OverviewPanel from "./OverviewPanel";

const data = {
  breadth: { total: 5000, up: 3000, down: 1800, limit_up: 40, up_ratio: 60, above_ma20_pct: 55, above_ma60_pct: 48 },
  regime: { state: "进攻", score: 4, suggested_position: "7~8成", note: "宽度强" },
  index: { code: "sh000300", close: 3912.5, above_ma20: true, above_ma60: true, ret_20d: 2.1, ret_60d: 5.5 },
};

describe("OverviewPanel", () => {
  it("renders regime state, breadth numbers and index close", () => {
    render(<OverviewPanel data={data} />);
    expect(screen.getByText("进攻")).toBeInTheDocument();
    expect(screen.getByText(/3000/)).toBeInTheDocument();    // 上涨家数
    expect(screen.getByText(/3912.5/)).toBeInTheDocument();  // 指数收盘
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
