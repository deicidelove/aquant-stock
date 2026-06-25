import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import TradeForm from "./TradeForm";
import TradesList from "./TradesList";

describe("TradeForm / TradesList", () => {
  it("TradeForm submits entered values", () => {
    const onSubmit = vi.fn();
    render(<TradeForm onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("代码"), { target: { value: "600000" } });
    fireEvent.change(screen.getByLabelText("数量"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("价格"), { target: { value: "10.5" } });
    fireEvent.change(screen.getByLabelText("日期"), { target: { value: "2026-02-02" } });
    fireEvent.click(screen.getByRole("button", { name: "记一笔" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ code: "600000", shares: 1000, price: 10.5, side: "buy", date: "2026-02-02" }),
    );
  });
  it("TradesList delete fires onDelete with tid", () => {
    const onDelete = vi.fn();
    render(<TradesList rows={[{ tid: 2, date: "2026-02-03", code: "600000", side: "buy", shares: 1000, price: 12, note: "" }]} onDelete={onDelete} />);
    fireEvent.click(screen.getByRole("button", { name: "删除" }));
    expect(onDelete).toHaveBeenCalledWith(2);
  });
});
