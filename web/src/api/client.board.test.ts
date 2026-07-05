import { describe, it, expect, vi, afterEach } from "vitest";
import { getBoard, addWatch, removeWatch } from "./client";

afterEach(() => vi.restoreAllMocks());
function mockFetch(body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, status: 200, json: async () => body } as Response);
}

describe("board client", () => {
  it("getBoard GETs /api/board", async () => {
    const f = mockFetch({ rows: [] });
    await getBoard();
    expect(f).toHaveBeenCalledWith("/api/board");
  });
  it("addWatch POSTs code", async () => {
    const f = mockFetch({ codes: ["600000"] });
    const r = await addWatch("600000");
    expect(r.codes).toEqual(["600000"]);
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/watchlist");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body as string).code).toBe("600000");
  });
  it("removeWatch DELETEs by code", async () => {
    const f = mockFetch({ codes: [] });
    await removeWatch("600000");
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/watchlist/600000");
    expect(opts.method).toBe("DELETE");
  });
});
