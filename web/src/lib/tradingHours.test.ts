import { describe, it, expect } from "vitest";
import { isTradingHours, refetchIntervalMs } from "./tradingHours";

describe("tradingHours", () => {
  it("true during morning/afternoon sessions on weekday", () => {
    expect(isTradingHours(new Date("2026-06-23T10:00:00"))).toBe(true); // 周二上午
    expect(isTradingHours(new Date("2026-06-23T14:00:00"))).toBe(true); // 周二下午
  });
  it("false at lunch/after-hours/weekend", () => {
    expect(isTradingHours(new Date("2026-06-23T12:00:00"))).toBe(false);
    expect(isTradingHours(new Date("2026-06-23T16:00:00"))).toBe(false);
    expect(isTradingHours(new Date("2026-06-27T10:00:00"))).toBe(false); // 周六
  });
  it("refetchIntervalMs is 60000 in session else false", () => {
    expect(refetchIntervalMs(new Date("2026-06-23T10:00:00"))).toBe(60000);
    expect(refetchIntervalMs(new Date("2026-06-23T16:00:00"))).toBe(false);
  });
});
