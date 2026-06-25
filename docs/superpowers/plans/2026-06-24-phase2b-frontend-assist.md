# Phase 2B — 辅助股民前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Phase 1B 前端基础上新增"辅助股民"板块（选票 / 我的持仓 / 复盘 + 顶部导航），消费 Phase 2A 的 holdings/assist 端点，形成选票→时机→持仓→复盘闭环。

**Architecture:** 沿用 1B 三层：纯展示组件（props in）/ TanStack Query hooks（读用 useQuery，写用 useMutation + invalidate）/ pages 装配。client 扩展 POST/DELETE。个股决策复用既有 `/stock/:code`（StockDetail）。新增顶部 Nav 串联板块。

**Tech Stack:** React 18 + TS + Vite · TanStack Query 5 · Tailwind · Vitest + @testing-library/react（沿用 1B 配置）。

## Global Constraints

- 全部前端代码在 `web/` 下；不动后端 `aquant/`、`server/`、Python `tests/`。
- 表现组件纯（props in → JSX），数据/写操作只在 `hooks/queries.ts` 与 pages；组件测试 mock `../charts/EChart` 与 `../hooks/queries`。
- 写操作（建/删交易）用 TanStack `useMutation`，成功后 `invalidateQueries` 刷新 holdings/trades/pnl。
- API 经 Vite 代理 `/api`；client 用相对路径。
- 复用既有：个股决策页 = 现有 `/stock/:code`（`StockDetail`）；不复制其逻辑。
- RTL 精确匹配：若插值文本与字面量同元素合并导致 `getByText` 失配，把值额外套一层元素（仅加 DOM、不改数据）——与 1B 一致。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `phase2b-frontend` 上开发；每个 Task 末尾提交。从 `web/` 目录跑 `npx vitest run` / `npm test` / `npm run build`。
- 后端端点契约（Phase 2A 已上线）：
  - `GET /api/holdings` → `{rows:[{code,name,shares,avg_cost,last_price,market_value,unrealized,unrealized_pct,alerts:string[]}]}`
  - `GET /api/holdings/trades` → `{rows:[{tid,date,code,side,shares,price,note}]}`
  - `GET /api/holdings/pnl` → `{realized,unrealized,total}`
  - `POST /api/holdings/trade` body `{date,code,side,shares,price,note?}` → `{tid}`
  - `DELETE /api/holdings/trade/{tid}` → `{deleted}`
  - `GET /api/assist/briefing?top=N` → `{rows:[{code,name,综合分,信号,风险,现价,买点,止损,目标,利好,利空}]}`
  - `GET /api/assist/scorecard` → `{as_of:string|null, rows:[{as_of,code,rank,fwd_5?,exc_5?,fwd_20?,exc_20?,fwd_60?,exc_60?,...}]}`

---

### Task 1: API 类型 + client（含 POST/DELETE）

**Files:**
- Modify: `web/src/api/types.ts`, `web/src/api/client.ts`
- Test: `web/src/api/client.assist.test.ts`

**Interfaces:**
- Produces（types.ts 追加）：`Holding`, `HoldingsResp`, `Trade`, `TradesResp`, `Pnl`, `TradeInput`, `BriefingRow`, `BriefingResp`, `ScorecardResp`
- Produces（client.ts 追加）：
  - 内部 `apiSend<T>(path: string, method: "POST" | "DELETE", body?: unknown): Promise<T>`
  - `getHoldings(): Promise<HoldingsResp>`、`getTrades(): Promise<TradesResp>`、`getPnl(): Promise<Pnl>`
  - `addTrade(input: TradeInput): Promise<{tid:number}>`、`deleteTrade(tid:number): Promise<{deleted:number}>`
  - `getBriefing(top=12): Promise<BriefingResp>`、`getScorecard(): Promise<ScorecardResp>`

- [ ] **Step 1: 写失败测试**

`web/src/api/client.assist.test.ts`：
```typescript
import { describe, it, expect, vi, afterEach } from "vitest";
import { getHoldings, addTrade, deleteTrade, getBriefing } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok, status, json: async () => body } as Response);
}

describe("assist/holdings client", () => {
  it("getHoldings GETs /api/holdings", async () => {
    const f = mockFetch({ rows: [] });
    await getHoldings();
    expect(f).toHaveBeenCalledWith("/api/holdings");
  });
  it("addTrade POSTs with JSON body", async () => {
    const f = mockFetch({ tid: 1 });
    const r = await addTrade({ date: "2026-02-02", code: "600000", side: "buy", shares: 100, price: 10 });
    expect(r.tid).toBe(1);
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/holdings/trade");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body as string).code).toBe("600000");
  });
  it("deleteTrade DELETEs by tid", async () => {
    const f = mockFetch({ deleted: 1 });
    await deleteTrade(3);
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/holdings/trade/3");
    expect(opts.method).toBe("DELETE");
  });
  it("getBriefing passes top", async () => {
    const f = mockFetch({ rows: [] });
    await getBriefing(5);
    expect(f).toHaveBeenCalledWith("/api/assist/briefing?top=5");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/api/client.assist.test.ts`
Expected: FAIL（`getHoldings` 等未导出）

- [ ] **Step 3: 追加 types.ts**

`web/src/api/types.ts` 末尾追加：
```typescript
export interface Holding {
  code: string; name: string; shares: number; avg_cost: number;
  last_price: number | null; market_value: number; unrealized: number;
  unrealized_pct: number; alerts: string[];
}
export interface HoldingsResp { rows: Holding[] }

export interface Trade { tid: number; date: string; code: string; side: string; shares: number; price: number; note: string }
export interface TradesResp { rows: Trade[] }

export interface Pnl { realized: number; unrealized: number; total: number }

export interface TradeInput { date: string; code: string; side: string; shares: number; price: number; note?: string }

export interface BriefingRow { code: string; name: string; [k: string]: unknown }
export interface BriefingResp { rows: BriefingRow[] }

export interface ScorecardResp { as_of: string | null; rows: Record<string, unknown>[] }
```

- [ ] **Step 4: 追加 client.ts**

`web/src/api/client.ts`：在 import 行补充新类型，并追加 `apiSend` 与函数：
```typescript
import type {
  Overview, Sectors, TopScores, Picks, Kline, Report,
  HoldingsResp, TradesResp, Pnl, TradeInput, BriefingResp, ScorecardResp,
} from "./types";

async function apiSend<T>(path: string, method: "POST" | "DELETE", body?: unknown): Promise<T> {
  const res = await fetch("/api" + path, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export const getHoldings = () => apiGet<HoldingsResp>("/holdings");
export const getTrades = () => apiGet<TradesResp>("/holdings/trades");
export const getPnl = () => apiGet<Pnl>("/holdings/pnl");
export const addTrade = (input: TradeInput) => apiSend<{ tid: number }>("/holdings/trade", "POST", input);
export const deleteTrade = (tid: number) => apiSend<{ deleted: number }>(`/holdings/trade/${tid}`, "DELETE");
export const getBriefing = (top = 12) => apiGet<BriefingResp>(`/assist/briefing?top=${top}`);
export const getScorecard = () => apiGet<ScorecardResp>("/assist/scorecard");
```
（保留原有 6 个 get 函数不动；只补 import 与新增导出。）

- [ ] **Step 5: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/api/client.assist.test.ts`
Expected: PASS（4 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/api
git commit -m "feat(web): assist/holdings API 类型 + client (GET/POST/DELETE)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Query hooks + 交易 mutations

**Files:**
- Modify: `web/src/hooks/queries.ts`
- Test: `web/src/hooks/queries.assist.test.tsx`

**Interfaces:**
- Consumes: Task 1 client 函数
- Produces：
  - 读：`useHoldings()`、`useTrades()`、`usePnl()`、`useBriefing(top?)`、`useScorecard()`
  - 写：`useAddTrade()`、`useDeleteTrade()`（`useMutation`；`onSuccess` 调 `queryClient.invalidateQueries` 刷新 `["holdings"]`/`["trades"]`/`["pnl"]`）

- [ ] **Step 1: 写失败测试（mock client）**

`web/src/hooks/queries.assist.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const addTrade = vi.fn(async () => ({ tid: 1 }));
vi.mock("../api/client", () => ({
  getHoldings: vi.fn(async () => ({ rows: [{ code: "600000", name: "浦发", shares: 100, avg_cost: 10, last_price: 11, market_value: 1100, unrealized: 100, unrealized_pct: 10, alerts: [] }] })),
  getPnl: vi.fn(async () => ({ realized: 0, unrealized: 100, total: 100 })),
  addTrade,
}));

import { useHoldings, usePnl, useAddTrade } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("assist hooks", () => {
  it("useHoldings returns rows", async () => {
    const { result } = renderHook(() => useHoldings(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
  it("usePnl returns totals", async () => {
    const { result } = renderHook(() => usePnl(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.total).toBe(100);
  });
  it("useAddTrade mutation calls client.addTrade", async () => {
    const { result } = renderHook(() => useAddTrade(), { wrapper });
    await act(async () => { await result.current.mutateAsync({ date: "2026-02-02", code: "600000", side: "buy", shares: 100, price: 10 }); });
    expect(addTrade).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/hooks/queries.assist.test.tsx`
Expected: FAIL（`useHoldings` 等未导出）

- [ ] **Step 3: 追加 hooks**

`web/src/hooks/queries.ts` 末尾追加（顶部已 `import * as api from "../api/client"`；新增 `useQueryClient`、`useMutation` 引入）：
```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";

export const useHoldings = () =>
  useQuery({ queryKey: ["holdings"], queryFn: api.getHoldings, refetchInterval: live });

export const useTrades = () =>
  useQuery({ queryKey: ["trades"], queryFn: api.getTrades });

export const usePnl = () =>
  useQuery({ queryKey: ["pnl"], queryFn: api.getPnl, refetchInterval: live });

export const useBriefing = (top = 12) =>
  useQuery({ queryKey: ["briefing", top], queryFn: () => api.getBriefing(top) });

export const useScorecard = () =>
  useQuery({ queryKey: ["scorecard"], queryFn: api.getScorecard });

function useInvalidateHoldings() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["holdings"] });
    qc.invalidateQueries({ queryKey: ["trades"] });
    qc.invalidateQueries({ queryKey: ["pnl"] });
  };
}

export const useAddTrade = () => {
  const invalidate = useInvalidateHoldings();
  return useMutation({ mutationFn: api.addTrade, onSuccess: invalidate });
};

export const useDeleteTrade = () => {
  const invalidate = useInvalidateHoldings();
  return useMutation({ mutationFn: api.deleteTrade, onSuccess: invalidate });
};
```
注意：`useQuery` 与 `live` 已在文件顶部存在（1B），无需重复定义；只新增 `useMutation`/`useQueryClient` 的 import。

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/hooks/queries.assist.test.tsx`
Expected: PASS（3 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/hooks
git commit -m "feat(web): 持仓/复盘 hooks + 交易 mutations

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 持仓展示组件 HoldingsPanel + PnlSummary

**Files:**
- Create: `web/src/components/HoldingsPanel.tsx`, `web/src/components/PnlSummary.tsx`, `web/src/components/Holdings.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Holding`、`Pnl`
- Produces：
  - `HoldingsPanel({ rows, onPick }: { rows: Holding[]; onPick?: (code:string)=>void })` —— 持仓表（代码/名称/持股/成本/现价/浮盈亏%/卖出提醒），行点击 onPick(code)；提醒非空标红
  - `PnlSummary({ pnl }: { pnl: Pnl })` —— 已实现/未实现/合计三数字

- [ ] **Step 1: 写失败测试**

`web/src/components/Holdings.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import HoldingsPanel from "./HoldingsPanel";
import PnlSummary from "./PnlSummary";

const rows = [
  { code: "600000", name: "浦发", shares: 1000, avg_cost: 11, last_price: 13.95, market_value: 13950, unrealized: 2950, unrealized_pct: 26.8, alerts: ["跌破止损"] },
];

describe("HoldingsPanel / PnlSummary", () => {
  it("renders holding row and fires onPick", () => {
    const onPick = vi.fn();
    render(<HoldingsPanel rows={rows} onPick={onPick} />);
    expect(screen.getByText("浦发")).toBeInTheDocument();
    expect(screen.getByText("跌破止损")).toBeInTheDocument();
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("PnlSummary shows totals", () => {
    render(<PnlSummary pnl={{ realized: 1000, unrealized: 2950, total: 3950 }} />);
    expect(screen.getByText(/3950/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/components/Holdings.test.tsx`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 写组件**

`web/src/components/HoldingsPanel.tsx`：
```tsx
import type { Holding } from "../api/types";

export default function HoldingsPanel({ rows, onPick }: { rows: Holding[]; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">我的持仓</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-400">暂无持仓，去"选票"建仓或在下方录入交易。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-gray-500">
            <tr>
              <th className="text-left">代码</th><th className="text-left">名称</th>
              <th className="text-right">持股</th><th className="text-right">成本</th>
              <th className="text-right">现价</th><th className="text-right">浮盈亏%</th>
              <th className="text-left">提醒</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
                <td>{r.code}</td><td>{r.name}</td>
                <td className="text-right">{r.shares}</td><td className="text-right">{r.avg_cost}</td>
                <td className="text-right">{r.last_price ?? "—"}</td>
                <td className={"text-right " + (r.unrealized_pct >= 0 ? "text-red-500" : "text-green-600")}>
                  {r.unrealized_pct >= 0 ? "+" : ""}{r.unrealized_pct}%
                </td>
                <td className="text-red-600">{r.alerts.map((a) => <span key={a} className="mr-1">{a}</span>)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

`web/src/components/PnlSummary.tsx`：
```tsx
import type { Pnl } from "../api/types";

export default function PnlSummary({ pnl }: { pnl: Pnl }) {
  const items = [
    { label: "已实现", value: pnl.realized },
    { label: "未实现", value: pnl.unrealized },
    { label: "合计", value: pnl.total },
  ];
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">盈亏汇总</h2>
      <div className="mt-2 grid grid-cols-3 gap-3 text-center">
        {items.map((it) => (
          <div key={it.label} className="rounded bg-gray-50 p-2">
            <div className="text-gray-500 text-sm">{it.label}</div>
            <div className={"text-base font-semibold " + (it.value >= 0 ? "text-red-500" : "text-green-600")}>
              <span>{it.value}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/components/Holdings.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/HoldingsPanel.tsx web/src/components/PnlSummary.tsx web/src/components/Holdings.test.tsx
git commit -m "feat(web): 持仓表 + 盈亏汇总组件

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 交易录入 TradeForm + 流水 TradesList

**Files:**
- Create: `web/src/components/TradeForm.tsx`, `web/src/components/TradesList.tsx`, `web/src/components/TradeForm.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Trade`、`TradeInput`
- Produces：
  - `TradeForm({ onSubmit }: { onSubmit: (t: TradeInput) => void })` —— 受控表单（日期/代码/方向/数量/价格），提交时调 `onSubmit`
  - `TradesList({ rows, onDelete }: { rows: Trade[]; onDelete?: (tid:number)=>void })` —— 流水表，每行删除按钮调 `onDelete(tid)`

- [ ] **Step 1: 写失败测试**

`web/src/components/TradeForm.test.tsx`：
```tsx
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/components/TradeForm.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件**

`web/src/components/TradeForm.tsx`：
```tsx
import { useState } from "react";
import type { TradeInput } from "../api/types";

export default function TradeForm({ onSubmit }: { onSubmit: (t: TradeInput) => void }) {
  const [date, setDate] = useState("");
  const [code, setCode] = useState("");
  const [side, setSide] = useState("buy");
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ date, code, side, shares: Number(shares), price: Number(price) });
  };

  return (
    <form onSubmit={submit} className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">录入交易</h2>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
        <label className="flex flex-col">日期<input aria-label="日期" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">代码<input aria-label="代码" value={code} onChange={(e) => setCode(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">方向<select aria-label="方向" value={side} onChange={(e) => setSide(e.target.value)} className="border p-1"><option value="buy">买入</option><option value="sell">卖出</option></select></label>
        <label className="flex flex-col">数量<input aria-label="数量" type="number" value={shares} onChange={(e) => setShares(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">价格<input aria-label="价格" type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} className="border p-1" /></label>
      </div>
      <button type="submit" className="mt-3 rounded bg-blue-600 px-3 py-1 text-white">记一笔</button>
    </form>
  );
}
```

`web/src/components/TradesList.tsx`：
```tsx
import type { Trade } from "../api/types";

export default function TradesList({ rows, onDelete }: { rows: Trade[]; onDelete?: (tid: number) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">交易流水</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-400">暂无流水。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-gray-500">
            <tr><th className="text-left">日期</th><th className="text-left">代码</th><th>方向</th><th className="text-right">数量</th><th className="text-right">价格</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.tid} className="border-b">
                <td>{t.date}</td><td>{t.code}</td>
                <td className="text-center">{t.side === "buy" ? "买入" : "卖出"}</td>
                <td className="text-right">{t.shares}</td><td className="text-right">{t.price}</td>
                <td className="text-right"><button onClick={() => onDelete?.(t.tid)} className="text-red-600">删除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/components/TradeForm.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/TradeForm.tsx web/src/components/TradesList.tsx web/src/components/TradeForm.test.tsx
git commit -m "feat(web): 交易录入表单 + 流水列表组件

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 复盘组件 BriefingPanel + ScorecardPanel

**Files:**
- Create: `web/src/components/BriefingPanel.tsx`, `web/src/components/ScorecardPanel.tsx`, `web/src/components/Review.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `BriefingRow`、`ScorecardResp`
- Produces：
  - `BriefingPanel({ rows, onPick }: { rows: BriefingRow[]; onPick?: (code:string)=>void })` —— 研报速览表（代码/名称/综合分/信号/买点/止损/目标），行点击下钻
  - `ScorecardPanel({ data }: { data: ScorecardResp })` —— 记分卡明细表（动态列：as_of/code/rank + 出现的 fwd_*/exc_* 列）

- [ ] **Step 1: 写失败测试**

`web/src/components/Review.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BriefingPanel from "./BriefingPanel";
import ScorecardPanel from "./ScorecardPanel";

describe("BriefingPanel / ScorecardPanel", () => {
  it("BriefingPanel renders row and fires onPick", () => {
    const onPick = vi.fn();
    render(<BriefingPanel rows={[{ code: "600000", name: "浦发", 综合分: 1.2, 信号: "买入/增持", 买点: 10.1, 止损: 9.5, 目标: 12 }]} onPick={onPick} />);
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("ScorecardPanel renders rows or empty hint", () => {
    render(<ScorecardPanel data={{ as_of: "2026-06-01", rows: [{ as_of: "2026-06-01", code: "600000", rank: 1, exc_20: 0.01 }] }} />);
    expect(screen.getByText("600000")).toBeInTheDocument();
    render(<ScorecardPanel data={{ as_of: null, rows: [] }} />);
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/components/Review.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件**

`web/src/components/BriefingPanel.tsx`：
```tsx
import type { BriefingRow } from "../api/types";

const COLS: [string, string][] = [
  ["综合分", "综合分"], ["信号", "信号"], ["买点", "买点"], ["止损", "止损"], ["目标", "目标"],
];

export default function BriefingPanel({ rows, onPick }: { rows: BriefingRow[]; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">研报速览</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-400">暂无候选。</p>
      ) : (
        <table className="mt-2 w-full text-sm">
          <thead className="text-gray-500">
            <tr><th className="text-left">代码</th><th className="text-left">名称</th>{COLS.map(([, h]) => <th key={h} className="text-right">{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
                <td>{r.code}</td><td>{String(r.name)}</td>
                {COLS.map(([k]) => <td key={k} className="text-right">{String(r[k] ?? "—")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

`web/src/components/ScorecardPanel.tsx`：
```tsx
import type { ScorecardResp } from "../api/types";

export default function ScorecardPanel({ data }: { data: ScorecardResp }) {
  if (data.rows.length === 0) {
    return (
      <section className="rounded-lg border border-gray-200 p-4">
        <h2 className="text-lg font-bold">推荐记分卡</h2>
        <p className="mt-2 text-sm text-gray-400">暂无台账数据（需积累每日推荐快照或跑回放）。</p>
      </section>
    );
  }
  const cols = Object.keys(data.rows[0]);
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">推荐记分卡</h2>
        <span className="text-xs text-gray-400">{data.as_of ?? "—"}</span>
      </div>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-gray-500"><tr>{cols.map((c) => <th key={c} className="text-left">{c}</th>)}</tr></thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i} className="border-b">{cols.map((c) => <td key={c}>{String(row[c] ?? "—")}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/components/Review.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/BriefingPanel.tsx web/src/components/ScorecardPanel.tsx web/src/components/Review.test.tsx
git commit -m "feat(web): 研报速览 + 推荐记分卡组件

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 我的持仓页 AssistHoldings

**Files:**
- Create: `web/src/pages/AssistHoldings.tsx`, `web/src/pages/AssistHoldings.test.tsx`

**Interfaces:**
- Consumes: hooks `useHoldings/useTrades/usePnl/useAddTrade/useDeleteTrade`（Task 2）；组件 `HoldingsPanel/PnlSummary/TradeForm/TradesList`；`useNavigate`
- Produces: `AssistHoldings()` —— 装配：持仓表（点击→`/stock/:code`）+ 盈亏汇总 + 录入表单（提交→useAddTrade.mutate）+ 流水（删除→useDeleteTrade.mutate）

- [ ] **Step 1: 写失败测试（mock hooks）**

`web/src/pages/AssistHoldings.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const mutate = vi.fn();
vi.mock("../hooks/queries", () => ({
  useHoldings: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", shares: 1000, avg_cost: 11, last_price: 13.95, market_value: 13950, unrealized: 2950, unrealized_pct: 26.8, alerts: [] }] } }),
  useTrades: () => ({ isSuccess: true, data: { rows: [] } }),
  usePnl: () => ({ isSuccess: true, data: { realized: 0, unrealized: 2950, total: 2950 } }),
  useAddTrade: () => ({ mutate }),
  useDeleteTrade: () => ({ mutate }),
}));
import AssistHoldings from "./AssistHoldings";

describe("AssistHoldings", () => {
  it("renders holdings, pnl and trade form", () => {
    render(<MemoryRouter><AssistHoldings /></MemoryRouter>);
    expect(screen.getByText("我的持仓")).toBeInTheDocument();
    expect(screen.getByText("盈亏汇总")).toBeInTheDocument();
    expect(screen.getByText("录入交易")).toBeInTheDocument();
    expect(screen.getByText("浦发")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/pages/AssistHoldings.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写页面**

`web/src/pages/AssistHoldings.tsx`：
```tsx
import { useNavigate } from "react-router-dom";
import { useHoldings, useTrades, usePnl, useAddTrade, useDeleteTrade } from "../hooks/queries";
import HoldingsPanel from "../components/HoldingsPanel";
import PnlSummary from "../components/PnlSummary";
import TradeForm from "../components/TradeForm";
import TradesList from "../components/TradesList";

export default function AssistHoldings() {
  const nav = useNavigate();
  const holdings = useHoldings();
  const trades = useTrades();
  const pnl = usePnl();
  const add = useAddTrade();
  const del = useDeleteTrade();
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">我的持仓</h1>
      {pnl.isSuccess && <PnlSummary pnl={pnl.data} />}
      {holdings.isSuccess && <HoldingsPanel rows={holdings.data.rows} onPick={(c) => nav(`/stock/${c}`)} />}
      <TradeForm onSubmit={(t) => add.mutate(t)} />
      {trades.isSuccess && <TradesList rows={trades.data.rows} onDelete={(tid) => del.mutate(tid)} />}
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/pages/AssistHoldings.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/AssistHoldings.tsx web/src/pages/AssistHoldings.test.tsx
git commit -m "feat(web): 我的持仓页 AssistHoldings

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: 选票页 AssistPicks + 复盘页 AssistReview

**Files:**
- Create: `web/src/pages/AssistPicks.tsx`, `web/src/pages/AssistReview.tsx`, `web/src/pages/Assist.test.tsx`

**Interfaces:**
- Consumes: hooks `usePicks/useBriefing`（选票）、`useScorecard/usePnl`（复盘）；组件 `PicksPanel`（1B 既有）、`BriefingPanel`、`ScorecardPanel`、`PnlSummary`；`useNavigate`
- Produces：
  - `AssistPicks()` —— 每日建仓名单（`usePicks`→`PicksPanel`）+ 研报速览（`useBriefing`→`BriefingPanel`），行点击 `/stock/:code`
  - `AssistReview()` —— 推荐记分卡（`useScorecard`→`ScorecardPanel`）+ 盈亏汇总（`usePnl`→`PnlSummary`）

- [ ] **Step 1: 写失败测试（mock hooks）**

`web/src/pages/Assist.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../hooks/queries", () => ({
  usePicks: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", score: 1.2 }] } }),
  useBriefing: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", 综合分: 1.2, 信号: "买入/增持" }] } }),
  useScorecard: () => ({ isSuccess: true, data: { as_of: "2026-06-01", rows: [{ as_of: "2026-06-01", code: "600000", rank: 1 }] } }),
  usePnl: () => ({ isSuccess: true, data: { realized: 0, unrealized: 100, total: 100 } }),
}));
import AssistPicks from "./AssistPicks";
import AssistReview from "./AssistReview";

describe("AssistPicks / AssistReview", () => {
  it("AssistPicks renders picks + briefing", () => {
    render(<MemoryRouter><AssistPicks /></MemoryRouter>);
    expect(screen.getByText("每日建仓名单")).toBeInTheDocument();
    expect(screen.getByText("研报速览")).toBeInTheDocument();
  });
  it("AssistReview renders scorecard + pnl", () => {
    render(<MemoryRouter><AssistReview /></MemoryRouter>);
    expect(screen.getByText("推荐记分卡")).toBeInTheDocument();
    expect(screen.getByText("盈亏汇总")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/pages/Assist.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写页面**

`web/src/pages/AssistPicks.tsx`：
```tsx
import { useNavigate } from "react-router-dom";
import { usePicks, useBriefing } from "../hooks/queries";
import PicksPanel from "../components/PicksPanel";
import BriefingPanel from "../components/BriefingPanel";

export default function AssistPicks() {
  const nav = useNavigate();
  const picks = usePicks();
  const briefing = useBriefing();
  const go = (c: string) => nav(`/stock/${c}`);
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">选票</h1>
      {picks.isSuccess && <PicksPanel data={picks.data} onPick={go} />}
      {briefing.isSuccess && <BriefingPanel rows={briefing.data.rows} onPick={go} />}
    </div>
  );
}
```

`web/src/pages/AssistReview.tsx`：
```tsx
import { useScorecard, usePnl } from "../hooks/queries";
import ScorecardPanel from "../components/ScorecardPanel";
import PnlSummary from "../components/PnlSummary";

export default function AssistReview() {
  const scorecard = useScorecard();
  const pnl = usePnl();
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">复盘</h1>
      {pnl.isSuccess && <PnlSummary pnl={pnl.data} />}
      {scorecard.isSuccess && <ScorecardPanel data={scorecard.data} />}
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/pages/Assist.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/AssistPicks.tsx web/src/pages/AssistReview.tsx web/src/pages/Assist.test.tsx
git commit -m "feat(web): 选票页 + 复盘页

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: 顶部导航 + 路由装配 + 构建

**Files:**
- Create: `web/src/components/Nav.tsx`
- Modify: `web/src/App.tsx`
- Create: `web/src/App.test.tsx`
- Modify: `README.md`

**Interfaces:**
- Consumes: 全部 pages
- Produces: `Nav`（链接：驾驶舱 `/`、选票 `/assist/picks`、我的持仓 `/assist/holdings`、复盘 `/assist/review`）；`App` 在 Nav 下渲染路由（新增 3 条 assist 路由）

- [ ] **Step 1: 写失败测试**

`web/src/App.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("./charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("./hooks/queries", () => ({
  useOverview: () => ({ isSuccess: false }), useSectors: () => ({ isSuccess: false }),
  usePicks: () => ({ isSuccess: false }), useTopScores: () => ({ isSuccess: false }),
}));
import App from "./App";

describe("App nav", () => {
  it("renders nav links to assist sections", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "选票" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "我的持仓" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "复盘" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/App.test.tsx`
Expected: FAIL（无 nav 链接）

- [ ] **Step 3: 写 Nav + 改 App**

`web/src/components/Nav.tsx`：
```tsx
import { Link } from "react-router-dom";

const LINKS: [string, string][] = [
  ["/", "驾驶舱"], ["/assist/picks", "选票"], ["/assist/holdings", "我的持仓"], ["/assist/review", "复盘"],
];

export default function Nav() {
  return (
    <nav className="flex gap-4 border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm">
      {LINKS.map(([to, label]) => (
        <Link key={to} to={to} className="text-blue-700 hover:underline">{label}</Link>
      ))}
    </nav>
  );
}
```

`web/src/App.tsx`：
```tsx
import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Cockpit from "./pages/Cockpit";
import StockDetail from "./pages/StockDetail";
import AssistPicks from "./pages/AssistPicks";
import AssistHoldings from "./pages/AssistHoldings";
import AssistReview from "./pages/AssistReview";

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<Cockpit />} />
        <Route path="/stock/:code" element={<StockDetail />} />
        <Route path="/assist/picks" element={<AssistPicks />} />
        <Route path="/assist/holdings" element={<AssistHoldings />} />
        <Route path="/assist/review" element={<AssistReview />} />
      </Routes>
    </>
  );
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd web && npx vitest run src/App.test.tsx`
Expected: PASS

- [ ] **Step 5: 全套测试 + 构建**

Run: `cd web && npm test && npm run build`
Expected: 全部 Vitest 用例通过；`tsc -b` 无错误，`vite build` 产出 dist/。

- [ ] **Step 6: README 追加辅助股民说明 + 提交**

`README.md` 的"v2 前端"段落末尾追加一行：
```markdown
辅助股民板块：选票 `/assist/picks` · 我的持仓 `/assist/holdings`（手动记账+卖出提醒）· 复盘 `/assist/review`。
```

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/Nav.tsx web/src/App.tsx web/src/App.test.tsx README.md
git commit -m "feat(web): 顶部导航 + 辅助股民路由装配

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 Phase 2 设计第 2 节前端 4 页面）：
- 选票（建仓名单 + 研报速览）→ Task 5(BriefingPanel) + Task 7(AssistPicks，复用 1B PicksPanel)。✅
- 个股决策（买卖时机/关键价位）→ 复用既有 `/stock/:code` StockDetail，选票/持仓行点击下钻（Task 6/7 onPick→nav）。✅
- 我的持仓（录入 + 持仓表 + 浮盈亏 + 卖出提醒 + 流水）→ Task 3/4/6。✅
- 复盘（记分卡 + 盈亏汇总）→ Task 5(ScorecardPanel) + Task 7(AssistReview)。✅
- 顶部导航串联板块 → Task 8。✅
- 写操作 mutation + invalidate 刷新 → Task 2。✅

**占位符扫描**：无 TBD/TODO；每步含完整可运行代码。✅

**类型一致性**：`Holding/HoldingsResp/Trade/TradesResp/Pnl/TradeInput/BriefingRow/BriefingResp/ScorecardResp` 在 types/client/hooks/组件/页面间一致；hooks 名（useHoldings/useTrades/usePnl/useBriefing/useScorecard/useAddTrade/useDeleteTrade）在页面与测试一致；组件 props（rows/onPick/onDelete/onSubmit/pnl/data/decision）一致；下钻统一走 `/stock/:code`。✅

**范围**：单一可测前端子系统（Vitest 全绿 + build），消费已上线 Phase 2A API。✅

**已知前提**：依赖 1B 既有 `apiGet`、`useQuery`、`live`（refetchInterval 门控）、`PicksPanel`；Task 2 仅新增 `useMutation/useQueryClient` import，不重复定义 1B 既有符号。
