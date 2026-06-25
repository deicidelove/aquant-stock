import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PicksPanel from "./PicksPanel";
import TopScoresPanel from "./TopScoresPanel";

describe("Picks/TopScores panels", () => {
  it("PicksPanel renders rows and fires onPick on row click", () => {
    const onPick = vi.fn();
    render(<PicksPanel data={{ rows: [{ code: "600000", name: "浦发", score: 1.23 }] }} onPick={onPick} />);
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("TopScoresPanel renders score rows", () => {
    render(<TopScoresPanel data={{ as_of: "2026-06-23", rows: [{ code: "000001", name: "平安", score: 2.5 }] }} />);
    expect(screen.getByText("平安")).toBeInTheDocument();
    expect(screen.getByText(/2.5/)).toBeInTheDocument();
  });
});
