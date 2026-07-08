import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import NorthFlowPanel from "./NorthFlowPanel";

describe("NorthFlowPanel", () => {
  it("renders channels with signed values", () => {
    render(<NorthFlowPanel data={{ date: "2026-07-08", rows: [
      { market: "沪股通", net: 12.3 }, { market: "深股通", net: -4.5 },
    ] }} />);
    expect(screen.getByText("沪股通")).toBeInTheDocument();
    expect(screen.getByText("+12.3 亿")).toBeInTheDocument();
    expect(screen.getByText("-4.5 亿")).toBeInTheDocument();
  });

  it("shows empty hint", () => {
    render(<NorthFlowPanel data={{ date: null, rows: [] }} />);
    expect(screen.getByText(/暂无北向数据/)).toBeInTheDocument();
  });
});
