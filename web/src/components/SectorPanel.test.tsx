import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import SectorPanel from "./SectorPanel";

const data = {
  as_of: "2026-06-23T14:30:00",
  rows: [
    { sector: "银行", pct_chg: 2.1, mkt_cap: 5e11 },
    { sector: "煤炭", pct_chg: 1.3, mkt_cap: 2e11 },
    { sector: "地产", pct_chg: -0.5, mkt_cap: 1e11 },
  ],
  rotation: {},
};

describe("SectorPanel", () => {
  it("renders heatmap chart and top sector by name", () => {
    render(<SectorPanel data={data} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    expect(screen.getAllByText("银行").length).toBeGreaterThan(0);
  });
});
