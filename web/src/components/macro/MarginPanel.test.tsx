import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import MarginPanel from "./MarginPanel";

describe("MarginPanel", () => {
  it("renders balance + trend", () => {
    render(<MarginPanel data={{ date: "2026-07-07", total_fin: 14882.3, total_bal: 15026, series: [
      { date: "2026-07-01", total_fin: 14800 }, { date: "2026-07-07", total_fin: 14882.3 },
    ] }} />);
    expect(screen.getByText("14,882.3 亿")).toBeInTheDocument();
    expect(screen.getByText(/\+82亿/)).toBeInTheDocument();
  });

  it("empty hint", () => {
    render(<MarginPanel data={{ date: null, total_fin: null, total_bal: null, series: [] }} />);
    expect(screen.getByText(/暂无融资融券/)).toBeInTheDocument();
  });
});
