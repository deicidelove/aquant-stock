import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LimitLadderPanel from "./LimitLadderPanel";

const data = {
  date: "2026-07-08", limit_up_count: 23, seal_rate: 0.65, break_rate: 0.35, max_boards: 7,
  ladder: [
    { boards: 7, count: 1, names: ["恒尚节能"] },
    { boards: 2, count: 4, names: ["威尔高", "视源股份", "大名城"] },
  ],
  by_industry: [{ industry: "计算机", count: 3 }],
};

describe("LimitLadderPanel", () => {
  it("renders counts, ladder rows, industry", () => {
    render(<LimitLadderPanel data={data} />);
    expect(screen.getByText("23")).toBeInTheDocument();
    expect(screen.getAllByText("7板").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("恒尚节能")).toBeInTheDocument();
    expect(screen.getByText(/封板 65%/)).toBeInTheDocument();
  });

  it("shows empty hint when no ladder", () => {
    render(<LimitLadderPanel data={{ ...data, ladder: [], by_industry: [], limit_up_count: 0 }} />);
    expect(screen.getByText(/暂无涨停数据/)).toBeInTheDocument();
  });
});
