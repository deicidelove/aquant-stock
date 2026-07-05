import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
const addMutate = vi.fn();
vi.mock("../hooks/queries", () => ({
  useBoard: () => ({ isSuccess: true, data: { rows: [{ code: "600519", name: "贵州茅台", last_price: 1241, pct_chg: 2.1, kline: [], signal: "买入/增持", one_liner: "x", battle_plan: {}, risk_level: "低", alerts: [] }] } }),
  useWatchlist: () => ({ isSuccess: true, data: { codes: ["600519"] } }),
  useAddWatch: () => ({ mutate: addMutate }),
  useRemoveWatch: () => ({ mutate: vi.fn() }),
  useSentiment: () => ({ isSuccess: true, data: { up: 1715, down: 1618, limit_up: 40, limit_down: 5, amount: 9e11, score: 37, label: "偏冷" } }),
}));
import Board from "./Board";

describe("Board", () => {
  it("renders market strip + card + add input", () => {
    render(<MemoryRouter><Board /></MemoryRouter>);
    expect(screen.getByText("贵州茅台")).toBeInTheDocument();
    expect(screen.getByText(/偏冷/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/代码/)).toBeInTheDocument();
  });
  it("add input submits code", () => {
    render(<MemoryRouter><Board /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText(/代码/), { target: { value: "000001" } });
    fireEvent.click(screen.getByRole("button", { name: "加自选" }));
    expect(addMutate).toHaveBeenCalledWith("000001");
  });
});
