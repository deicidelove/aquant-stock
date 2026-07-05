import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import ProKlineChart from "./ProKlineChart";

describe("ProKlineChart", () => {
  it("renders chart", () => {
    render(<ProKlineChart chart={{ code: "600000", bars: [], ma: {}, macd: {} }} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
