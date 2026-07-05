import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LhbSeats from "./LhbSeats";

describe("LhbSeats", () => {
  it("renders seats with type/hotmoney labels", () => {
    render(<LhbSeats
      buy={[
        { rank: 1, seat: "机构专用", buy: 3e7, sell: 0, net: 3e7, seat_type: "inst", hotmoney_name: null },
        { rank: 2, seat: "东北证券佛山分公司", buy: 2e7, sell: 0, net: 2e7, seat_type: "hotmoney", hotmoney_name: "佛山无影脚" },
      ]}
      sell={[
        { rank: 1, seat: "深股通专用", buy: 0, sell: 1e8, net: -1e8, seat_type: "north", hotmoney_name: null },
      ]}
    />);
    expect(screen.getByText("机构")).toBeInTheDocument();
    expect(screen.getByText("佛山无影脚")).toBeInTheDocument();
    expect(screen.getByText("北向")).toBeInTheDocument();
    expect(screen.getByText("买入前五")).toBeInTheDocument();
    expect(screen.getByText("1.00亿")).toBeInTheDocument(); // 卖出 1e8
  });

  it("shows 无 when empty", () => {
    render(<LhbSeats buy={[]} sell={[]} />);
    expect(screen.getAllByText("无")).toHaveLength(2);
  });
});
