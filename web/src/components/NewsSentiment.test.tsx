import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const data = {
  score: 67, label: "乐观", pos: 4, neg: 1, neutral: 2,
  items: [
    { time: "2026-07-05 09:00", title: "央行降准释放流动性", summary: "", url: "http://a", sent: 1 },
    { time: "2026-07-05 08:30", title: "某股被立案调查", summary: "", url: "http://b", sent: -1 },
    { time: "2026-07-05 08:00", title: "行情播报", summary: "", url: "", sent: 0 },
    { time: "2026-07-05 07:30", title: "第四条", summary: "", url: "", sent: 0 },
  ],
};
vi.mock("../hooks/queries", () => ({ useNewsSentiment: () => ({ isSuccess: true, data }) }));
import NewsSentiment from "./NewsSentiment";

describe("NewsSentiment", () => {
  it("renders score/label/counts + headlines", () => {
    render(<NewsSentiment />);
    expect(screen.getByText("67")).toBeInTheDocument();
    expect(screen.getByText("乐观")).toBeInTheDocument();
    expect(screen.getByText("央行降准释放流动性")).toBeInTheDocument();
    expect(screen.getByText(/利好4/)).toBeInTheDocument();
  });

  it("compact shows only 3", () => {
    render(<NewsSentiment compact />);
    expect(screen.getByText("央行降准释放流动性")).toBeInTheDocument();
    expect(screen.queryByText("第四条")).not.toBeInTheDocument();
  });
});
