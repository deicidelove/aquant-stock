import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("./charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("./hooks/queries", () => ({
  useOverview: () => ({ isSuccess: false }), useSectors: () => ({ isSuccess: false }),
  usePicks: () => ({ isSuccess: false }), useTopScores: () => ({ isSuccess: false }),
}));
import App from "./App";

describe("App nav", () => {
  it("renders nav links to assist sections", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "选票" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "我的持仓" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "复盘" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "量化回测" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "因子" })).toBeInTheDocument();
  });
});
