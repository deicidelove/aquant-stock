import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import RegimePanel from "./RegimePanel";
import IndexTrendPanel from "./IndexTrendPanel";
import AmountPanel from "./AmountPanel";

describe("kandapan panels", () => {
  it("RegimePanel shows state + position", () => {
    render(<RegimePanel data={{ state: "防守", score: 1, suggested_position: "1~3成", note: "宽度走弱" }} />);
    expect(screen.getByText("防守")).toBeInTheDocument();
    expect(screen.getByText(/1~3成/)).toBeInTheDocument();
  });
  it("IndexTrendPanel renders chart", () => {
    render(<IndexTrendPanel data={{ code: "sh000300", points: [{ date: "d", close: 3900, ma20: 3890, ma60: 3850 }] }} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
  it("AmountPanel renders chart", () => {
    render(<AmountPanel data={{ series: [{ date: "d", amount: 9000 }] }} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
