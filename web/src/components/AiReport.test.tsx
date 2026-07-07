import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const genMutate = vi.fn();
let reportData: unknown = null;
vi.mock("../hooks/queries", () => ({
  useAiReport: () => ({ data: { report: reportData } }),
  useGenAiReport: () => ({ mutate: genMutate }),
}));
import AiReport from "./AiReport";

describe("AiReport", () => {
  it("shows generate button when no report", () => {
    reportData = null;
    render(<AiReport code="600000" />);
    expect(screen.getByRole("button", { name: "生成报告" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "生成报告" }));
    expect(genMutate).toHaveBeenCalled();
  });

  it("renders analysts + debate + verdict when report present", () => {
    reportData = {
      code: "600000", name: "浦发银行", as_of: "2026-07-06",
      analysts: { technical: "多头排列", capital: "机构进场", news: "利好", fundamental: "估值合理" },
      debate: { bull: "看多逻辑", bear: "看空逻辑" },
      verdict: { stance: "买入/增持", reason: "综合看好", position: "5成", risks: ["估值偏高"] },
      llm_used: true,
    };
    render(<AiReport code="600000" />);
    expect(screen.getByText("买入/增持")).toBeInTheDocument();
    expect(screen.getByText("多头排列")).toBeInTheDocument();
    expect(screen.getByText("看多逻辑")).toBeInTheDocument();
    expect(screen.getByText("看空逻辑")).toBeInTheDocument();
    expect(screen.getByText(/估值偏高/)).toBeInTheDocument();
    expect(screen.getByText(/不构成投资建议/)).toBeInTheDocument();
  });
});
