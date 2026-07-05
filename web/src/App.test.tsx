import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("./charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("./hooks/queries", () => ({
  useBoard: () => ({ isSuccess: false }), useWatchlist: () => ({ isSuccess: false }),
  useAddWatch: () => ({ mutate: vi.fn() }), useRemoveWatch: () => ({ mutate: vi.fn() }),
  useSentiment: () => ({ isSuccess: false }),
}));
import App from "./App";

describe("App nav", () => {
  it("shows 看板 as primary and 高级 group with 量化回测", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "看板" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "我的持仓" })).toBeInTheDocument();
    expect(screen.getByText("高级")).toBeInTheDocument();       // 分组标题
    expect(screen.getByRole("link", { name: "量化回测" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "驾驶舱" })).toBeInTheDocument();
  });
});
