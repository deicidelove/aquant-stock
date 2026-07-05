import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card, Stat, Badge, SignalTag, UpdatedAt } from "./atoms";

describe("ui atoms", () => {
  it("Card renders title and children", () => {
    render(<Card title="大盘指数"><span>hi</span></Card>);
    expect(screen.getByText("大盘指数")).toBeInTheDocument();
    expect(screen.getByText("hi")).toBeInTheDocument();
  });
  it("Stat renders label + value", () => {
    render(<Stat label="上涨" value={1715} />);
    expect(screen.getByText("上涨")).toBeInTheDocument();
    expect(screen.getByText("1715")).toBeInTheDocument();
  });
  it("SignalTag maps 买入", () => {
    render(<SignalTag signal="买入/增持" />);
    expect(screen.getByText(/买入/)).toBeInTheDocument();
  });
  it("UpdatedAt shows time and mode", () => {
    render(<UpdatedAt at="14:32:01" live={true} />);
    expect(screen.getByText(/14:32:01/)).toBeInTheDocument();
    expect(screen.getByText(/盘中实时/)).toBeInTheDocument();
  });
  it("Badge renders", () => {
    render(<Badge tone="red">异常</Badge>);
    expect(screen.getByText("异常")).toBeInTheDocument();
  });
});
