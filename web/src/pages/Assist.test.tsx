import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../hooks/queries", () => ({
  usePicks: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", score: 1.2 }] } }),
  useTopScores: () => ({ isSuccess: true, data: { as_of: "2026-06-23", rows: [{ code: "000001", name: "平安", score: 2.5 }] } }),
  useBriefing: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", 综合分: 1.2, 信号: "买入/增持" }] } }),
  useScorecard: () => ({ isSuccess: true, data: { as_of: "2026-06-01", rows: [{ as_of: "2026-06-01", code: "600000", rank: 1 }] } }),
  useScorecardSummary: () => ({ isSuccess: true, data: { sample: { picks: 0, snapshots: 0, start: null, end: null, live: 0, replay: 0 }, horizons: [], rank_ic: [], delisted: 0 } }),
  usePnl: () => ({ isSuccess: true, data: { realized: 0, unrealized: 100, total: 100 } }),
}));
import AssistPicks from "./AssistPicks";
import AssistReview from "./AssistReview";

describe("AssistPicks / AssistReview", () => {
  it("AssistPicks renders picks + briefing", () => {
    render(<MemoryRouter><AssistPicks /></MemoryRouter>);
    expect(screen.getByText("每日建仓名单")).toBeInTheDocument();
    expect(screen.getByText("综合分高分股")).toBeInTheDocument();
    expect(screen.getByText("研报速览")).toBeInTheDocument();
  });
  it("AssistReview renders scorecard + pnl", () => {
    render(<MemoryRouter><AssistReview /></MemoryRouter>);
    expect(screen.getByText("推荐记分卡")).toBeInTheDocument();
    expect(screen.getByText("盈亏汇总")).toBeInTheDocument();
  });
});
