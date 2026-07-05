# v3B — 自选股看板前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 前端落地「自选股看板」为新首页：自选/持仓卡片（现价涨跌+迷你走势+一句话信号+买点止损+提醒）+ 顶部大盘脸色条 + 加自选输入；导航把量化/驾驶舱(宏观)/复盘降级到"高级"，把首屏让给看板。

**Architecture:** 沿用既有前端栈：纯展示组件（props in）+ TanStack Query hooks（board 盘中轮询、加删自选 mutation+invalidate）+ ECharts 薄壳（迷你走势）+ 深色 UI 原子。新首页 `/` = 看板；现宏观驾驶舱移到 `/macro`；导航重构。

**Tech Stack:** React 18 + TS + Vite · TanStack Query 5 · ECharts 5 · Tailwind · Vitest + @testing-library/react。

## Global Constraints

- 全部前端代码在 `web/` 下；不动后端。
- 表现组件纯（props in → JSX），取数只在 `hooks/queries.ts` 与 pages；组件测试 mock `../charts/EChart` 与 `../hooks/queries`。
- 加/删自选用 `useMutation`，成功后 `invalidateQueries(["board"])` + `(["watchlist"])`。
- board 盘中轮询用既有 `live`（`refetchIntervalMs`）。
- 深色主题沿用 v2.1 原子（Card/Badge/SignalTag/Stat 等）；红涨绿跌。
- RTL 精确匹配冲突时把插值值额外套元素（仅加 DOM、不改数据）。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `v3b-frontend` 上开发；每 Task 末尾提交。从 `web/` 跑 `npx vitest run` / `npm test` / `npm run build`。
- 后端契约（v3A 已上线）：
  - `GET /api/board` → `{rows:[{code,name,last_price,pct_chg,kline:[{date,close}],signal,one_liner,battle_plan:{ideal_buy,secondary_buy,stop_loss,take_profit,position},risk_level,alerts:string[]}]}`
  - `GET /api/watchlist` → `{codes:[...]}`；`POST /api/watchlist {code}` → `{codes}`；`DELETE /api/watchlist/{code}` → `{codes}`
  - 既有：`GET /api/cockpit/sentiment`（大盘脸色条复用）。

## 复用既有资产
- UI 原子 `web/src/ui/atoms.tsx`：`Card/Badge/SignalTag/Stat/UpdatedAt`。
- `web/src/charts/EChart.tsx`（薄壳）；`web/src/hooks/queries.ts` 的 `live`、`useSentiment`。
- `web/src/api/client.ts` 的 `apiGet`/`apiSend`。

---

### Task 1: 看板 API 类型 + client

**Files:**
- Modify: `web/src/api/types.ts`, `web/src/api/client.ts`
- Test: `web/src/api/client.board.test.ts`

**Interfaces:**
- Produces（types.ts）：`BoardCard`（字段见契约）、`BoardResp{rows:BoardCard[]}`、`WatchlistResp{codes:string[]}`
- Produces（client.ts）：`getBoard()`、`getWatchlist()`、`addWatch(code)`、`removeWatch(code)`

- [ ] **Step 1: 写失败测试**

`web/src/api/client.board.test.ts`：
```typescript
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/api/client.board.test.ts`
Expected: FAIL

- [ ] **Step 3: 追加 types.ts**

`web/src/api/types.ts` 末尾追加：
```typescript
export interface BoardCard {
  code: string; name: string; last_price: number | null; pct_chg: number | null;
  kline: { date: string; close: number }[];
  signal: string; one_liner: string;
  battle_plan: { ideal_buy?: number; secondary_buy?: number; stop_loss?: number; take_profit?: number; position?: string };
  risk_level: string; alerts: string[];
}
export interface BoardResp { rows: BoardCard[] }
export interface WatchlistResp { codes: string[] }
```

- [ ] **Step 4: 追加 client.ts**

import 行补充 `BoardResp, WatchlistResp`；末尾追加：
```typescript
export const getBoard = () => apiGet<BoardResp>("/board");
export const getWatchlist = () => apiGet<WatchlistResp>("/watchlist");
export const addWatch = (code: string) => apiSend<WatchlistResp>("/watchlist", "POST", { code });
export const removeWatch = (code: string) => apiSend<WatchlistResp>(`/watchlist/${code}`, "DELETE");
```

- [ ] **Step 5: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/api/client.board.test.ts`
Expected: PASS（3 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/api
git commit -m "feat(web): 看板 API 类型 + client(board/watchlist)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 看板 hooks + 加删自选 mutation

**Files:**
- Modify: `web/src/hooks/queries.ts`
- Test: `web/src/hooks/queries.board.test.tsx`

**Interfaces:**
- Produces：`useBoard()`（`refetchInterval: live`）、`useWatchlist()`、`useAddWatch()`、`useRemoveWatch()`（mutation，`onSuccess` invalidate `["board"]`+`["watchlist"]`）

- [ ] **Step 1: 写失败测试**

`web/src/hooks/queries.board.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const addWatch = vi.fn(async () => ({ codes: ["600000"] }));
vi.mock("../api/client", () => ({
  getBoard: vi.fn(async () => ({ rows: [{ code: "600000", name: "浦发", last_price: 10, pct_chg: 1, kline: [], signal: "买入/增持", one_liner: "x", battle_plan: {}, risk_level: "低", alerts: [] }] })),
  addWatch,
}));
import { useBoard, useAddWatch } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("board hooks", () => {
  it("useBoard returns rows", async () => {
    const { result } = renderHook(() => useBoard(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
  it("useAddWatch mutation calls client.addWatch", async () => {
    const { result } = renderHook(() => useAddWatch(), { wrapper });
    await act(async () => { await result.current.mutateAsync("600000"); });
    expect(addWatch).toHaveBeenCalledWith("600000");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/hooks/queries.board.test.tsx`
Expected: FAIL

- [ ] **Step 3: 追加 hooks**

`web/src/hooks/queries.ts` 末尾追加（`useMutation`/`useQueryClient` 已 import；`live`/`api` 已在顶部）：
```typescript
export const useBoard = () =>
  useQuery({ queryKey: ["board"], queryFn: api.getBoard, refetchInterval: live });

export const useWatchlist = () =>
  useQuery({ queryKey: ["watchlist"], queryFn: api.getWatchlist });

function useInvalidateBoard() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["board"] });
    qc.invalidateQueries({ queryKey: ["watchlist"] });
  };
}

export const useAddWatch = () => {
  const invalidate = useInvalidateBoard();
  return useMutation({ mutationFn: api.addWatch, onSuccess: invalidate });
};

export const useRemoveWatch = () => {
  const invalidate = useInvalidateBoard();
  return useMutation({ mutationFn: api.removeWatch, onSuccess: invalidate });
};
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/hooks/queries.board.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/hooks
git commit -m "feat(web): 看板 hooks + 加删自选 mutation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 迷你走势 option + 看板卡片 BoardCard

**Files:**
- Modify: `web/src/charts/options.ts`
- Create: `web/src/components/BoardCard.tsx`, `web/src/components/BoardCard.test.tsx`
- Test: `web/src/charts/options.spark.test.ts`

**Interfaces:**
- Produces：
  - `buildSparklineOption(kline: {date:string;close:number}[]): object`（极简折线：无轴无网格，颜色按首尾涨跌红/绿）
  - `BoardCard({ card, onOpen?, onRemove? }: { card: BoardCard; onOpen?:(code:string)=>void; onRemove?:(code:string)=>void })` —— 一张卡：名称+代码、现价+涨跌%、迷你走势(EChart)、信号徽章+一句话、买点/止损/目标、⚠️提醒、移除按钮

- [ ] **Step 1: 写失败测试**

`web/src/charts/options.spark.test.ts`：
```typescript
import { describe, it, expect } from "vitest";
import { buildSparklineOption } from "./options";
describe("sparkline option", () => {
  it("maps closes to a line series, up=red", () => {
    const opt = buildSparklineOption([{ date: "d1", close: 10 }, { date: "d2", close: 11 }]) as any;
    expect(opt.series[0].type).toBe("line");
    expect(opt.series[0].data).toEqual([10, 11]);
    expect(opt.series[0].lineStyle.color).toBe("#ef4444"); // 涨=红
  });
});
```

`web/src/components/BoardCard.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import BoardCard from "./BoardCard";

const card = {
  code: "600519", name: "贵州茅台", last_price: 1241.41, pct_chg: 2.17,
  kline: [{ date: "d1", close: 1200 }], signal: "买入/增持", one_liner: "低波反转",
  battle_plan: { ideal_buy: 1200, stop_loss: 1150, take_profit: 1400, position: "3~5成" },
  risk_level: "低", alerts: ["跌破止损"],
};

describe("BoardCard", () => {
  it("renders core fields + fires onOpen", () => {
    const onOpen = vi.fn();
    render(<BoardCard card={card} onOpen={onOpen} />);
    expect(screen.getByText("贵州茅台")).toBeInTheDocument();
    expect(screen.getByText(/1241.41/)).toBeInTheDocument();
    expect(screen.getByText(/买入/)).toBeInTheDocument();
    expect(screen.getByText("跌破止损")).toBeInTheDocument();
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    fireEvent.click(screen.getByText("贵州茅台"));
    expect(onOpen).toHaveBeenCalledWith("600519");
  });
  it("fires onRemove", () => {
    const onRemove = vi.fn();
    render(<BoardCard card={card} onRemove={onRemove} />);
    fireEvent.click(screen.getByRole("button", { name: "移除" }));
    expect(onRemove).toHaveBeenCalledWith("600519");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/charts/options.spark.test.ts src/components/BoardCard.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写 option + 组件**

`web/src/charts/options.ts` 末尾追加：
```typescript
export function buildSparklineOption(kline: { date: string; close: number }[]): object {
  const closes = kline.map((k) => k.close);
  const up = closes.length > 1 ? closes[closes.length - 1] >= closes[0] : true;
  return {
    grid: { left: 0, right: 0, top: 4, bottom: 4 },
    xAxis: { type: "category", show: false, data: kline.map((k) => k.date) },
    yAxis: { type: "value", show: false, scale: true },
    series: [{ type: "line", showSymbol: false, data: closes, lineStyle: { color: up ? "#ef4444" : "#22c55e", width: 1.5 }, areaStyle: { opacity: 0.08, color: up ? "#ef4444" : "#22c55e" } }],
  };
}
```

`web/src/components/BoardCard.tsx`：
```tsx
import type { BoardCard as Card } from "../api/types";
import EChart from "../charts/EChart";
import { buildSparklineOption } from "../charts/options";
import { SignalTag, Badge } from "../ui/atoms";

export default function BoardCard({ card, onOpen, onRemove }: {
  card: Card; onOpen?: (code: string) => void; onRemove?: (code: string) => void;
}) {
  const p = card.battle_plan;
  const up = (card.pct_chg ?? 0) >= 0;
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-3">
      <div className="flex items-start justify-between">
        <button className="text-left" onClick={() => onOpen?.(card.code)}>
          <div className="font-semibold text-slate-100">{card.name}</div>
          <div className="text-xs text-slate-500">{card.code}</div>
        </button>
        <div className="text-right">
          <div className="font-mono text-lg text-slate-100">{card.last_price ?? "—"}</div>
          <div className={"text-sm " + (up ? "text-red-400" : "text-green-400")}>
            {up ? "+" : ""}{card.pct_chg ?? "—"}%
          </div>
        </div>
      </div>
      <div className="my-2 h-10"><EChart option={buildSparklineOption(card.kline)} height={40} /></div>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {card.signal && <SignalTag signal={card.signal} />}
        {card.risk_level && <Badge tone={card.risk_level === "高" ? "red" : card.risk_level === "中" ? "amber" : "gray"}><span>风险{card.risk_level}</span></Badge>}
        {card.alerts.map((a) => <Badge key={a} tone="red"><span>{a}</span></Badge>)}
      </div>
      {card.one_liner && <p className="mt-2 text-xs text-slate-300">{card.one_liner}</p>}
      <div className="mt-2 grid grid-cols-4 gap-1 text-center text-xs">
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">买点</div><div className="text-slate-200">{p.ideal_buy ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">止损</div><div className="text-slate-200">{p.stop_loss ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">目标</div><div className="text-slate-200">{p.take_profit ?? "—"}</div></div>
        <div className="rounded bg-slate-800 p-1"><div className="text-slate-500">仓位</div><div className="text-slate-200">{p.position ?? "—"}</div></div>
      </div>
      {onRemove && <div className="mt-2 text-right"><button onClick={() => onRemove(card.code)} className="text-xs text-slate-500 hover:text-red-400">移除</button></div>}
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/charts/options.spark.test.ts src/components/BoardCard.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/charts/options.ts web/src/components/BoardCard.tsx web/src/components/BoardCard.test.tsx web/src/charts/options.spark.test.ts
git commit -m "feat(web): 迷你走势 option + 看板卡片 BoardCard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 看板首页 Board（大盘条 + 加自选 + 卡片列表）

**Files:**
- Create: `web/src/pages/Board.tsx`, `web/src/pages/Board.test.tsx`

**Interfaces:**
- Consumes: `useBoard/useWatchlist/useAddWatch/useRemoveWatch`（Task 2）、`useSentiment`（既有）、`BoardCard`（Task 3）、`useNavigate`
- Produces: `Board()` —— 顶部大盘脸色条（sentiment 一句话：温度+涨跌家数）；加自选输入框（回车/按钮 → useAddWatch.mutate）；卡片网格（board.rows → BoardCard，onOpen→`/stock/:code`，onRemove→useRemoveWatch.mutate）；空态提示

- [ ] **Step 1: 写失败测试（mock hooks + EChart）**

`web/src/pages/Board.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
const addMutate = vi.fn();
vi.mock("../hooks/queries", () => ({
  useBoard: () => ({ isSuccess: true, data: { rows: [{ code: "600519", name: "贵州茅台", last_price: 1241, pct_chg: 2.1, kline: [], signal: "买入/增持", one_liner: "x", battle_plan: {}, risk_level: "低", alerts: [] }] } }),
  useWatchlist: () => ({ isSuccess: true, data: { codes: ["600519"] } }),
  useAddWatch: () => ({ mutate: addMutate }),
  useRemoveWatch: () => ({ mutate: vi.fn() }),
  useSentiment: () => ({ isSuccess: true, data: { up: 1715, down: 1618, limit_up: 40, limit_down: 5, amount: 9e11, score: 37, label: "偏冷" } }),
}));
import Board from "./Board";

describe("Board", () => {
  it("renders market strip + card + add input", () => {
    render(<MemoryRouter><Board /></MemoryRouter>);
    expect(screen.getByText("贵州茅台")).toBeInTheDocument();
    expect(screen.getByText(/偏冷/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/代码/)).toBeInTheDocument();
  });
  it("add input submits code", () => {
    render(<MemoryRouter><Board /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText(/代码/), { target: { value: "000001" } });
    fireEvent.click(screen.getByRole("button", { name: "加自选" }));
    expect(addMutate).toHaveBeenCalledWith("000001");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/pages/Board.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写 Board.tsx**

`web/src/pages/Board.tsx`：
```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useBoard, useAddWatch, useRemoveWatch, useSentiment } from "../hooks/queries";
import BoardCard from "../components/BoardCard";

export default function Board() {
  const nav = useNavigate();
  const board = useBoard();
  const add = useAddWatch();
  const remove = useRemoveWatch();
  const sentiment = useSentiment();
  const [code, setCode] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) { add.mutate(code.trim()); setCode(""); }
  };
  const s = sentiment.data;
  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold text-slate-100">📋 我的看板</h1>
        {sentiment.isSuccess && s && (
          <div className="text-sm text-slate-400">
            大盘 <span className={s.score >= 50 ? "text-red-400" : "text-green-400"}>{s.label}</span>
            {" "}· 涨 {s.up}/跌 {s.down} · 涨停 {s.limit_up}
          </div>
        )}
      </div>
      <form onSubmit={submit} className="flex gap-2">
        <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="输入代码加自选(如 600519)"
               className="flex-1 rounded border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100" />
        <button type="submit" className="rounded bg-sky-600 px-3 py-1 text-sm text-white">加自选</button>
      </form>
      {board.isSuccess && board.data.rows.length === 0 && (
        <p className="text-sm text-slate-500">还没有自选/持仓。上方输入代码加自选，或去「我的持仓」录入交易。</p>
      )}
      {board.isSuccess && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {board.data.rows.map((c) => (
            <BoardCard key={c.code} card={c} onOpen={(x) => nav(`/stock/${x}`)} onRemove={(x) => remove.mutate(x)} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/pages/Board.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/Board.tsx web/src/pages/Board.test.tsx
git commit -m "feat(web): 看板首页 Board(大盘条+加自选+卡片列表)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 导航重构（看板首页 + 量化降级）+ 路由 + 构建冒烟

**Files:**
- Modify: `web/src/App.tsx`, `web/src/App.test.tsx`, `web/src/components/Nav.tsx`, `README.md`

**Interfaces:**
- Produces：
  - 路由：`/` = `Board`（新首页）；`/macro` = 现有 `Cockpit`（宏观驾驶舱）；其余不变（`/stock/:code`、`/assist/*`、`/quant/*`）
  - Nav：主入口 **看板 `/`** · **我的持仓 `/assist/holdings`**；一个 **高级** 分组（`<details>`）含：驾驶舱 `/macro`、选票 `/assist/picks`、复盘 `/assist/review`、量化回测 `/quant/backtest`、因子 `/quant/factors`

- [ ] **Step 1: 改测试**

覆盖 `web/src/App.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("./charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("./hooks/queries", () => ({
  useBoard: () => ({ isSuccess: false }), useWatchlist: () => ({ isSuccess: false }),
  useAddWatch: () => ({ mutate: vi.fn() }), useRemoveWatch: () => ({ mutate: vi.fn() }),
  useSentiment: () => ({ isSuccess: false }),
}));
import App from "./App";

describe("App nav", () => {
  it("shows 看板 as primary and 高级 group with 量化回测", () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: "看板" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "我的持仓" })).toBeInTheDocument();
    expect(screen.getByText("高级")).toBeInTheDocument();       // 分组标题
    expect(screen.getByRole("link", { name: "量化回测" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "驾驶舱" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/App.test.tsx`
Expected: FAIL

- [ ] **Step 3: 改 Nav + App**

`web/src/components/Nav.tsx`：
```tsx
import { Link } from "react-router-dom";

const PRIMARY: [string, string][] = [["/", "看板"], ["/assist/holdings", "我的持仓"]];
const ADVANCED: [string, string][] = [
  ["/macro", "驾驶舱"], ["/assist/picks", "选票"], ["/assist/review", "复盘"],
  ["/quant/backtest", "量化回测"], ["/quant/factors", "因子"],
];

export default function Nav() {
  return (
    <nav className="flex items-center gap-4 border-b border-slate-700 bg-slate-800 px-4 py-2 text-sm">
      {PRIMARY.map(([to, label]) => (
        <Link key={to} to={to} className="text-sky-400 hover:underline">{label}</Link>
      ))}
      <details className="relative">
        <summary className="cursor-pointer list-none text-slate-400">高级 ▾</summary>
        <div className="absolute z-10 mt-1 flex flex-col gap-1 rounded border border-slate-700 bg-slate-900 p-2">
          {ADVANCED.map(([to, label]) => (
            <Link key={to} to={to} className="whitespace-nowrap text-sky-400 hover:underline">{label}</Link>
          ))}
        </div>
      </details>
    </nav>
  );
}
```

`web/src/App.tsx`：把 `Cockpit` 路由从 `/` 改到 `/macro`，`/` 指向 `Board`：
```tsx
import { Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Board from "./pages/Board";
import Cockpit from "./pages/Cockpit";
import StockDetail from "./pages/StockDetail";
import AssistPicks from "./pages/AssistPicks";
import AssistHoldings from "./pages/AssistHoldings";
import AssistReview from "./pages/AssistReview";
import QuantBacktest from "./pages/QuantBacktest";
import QuantFactors from "./pages/QuantFactors";

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<Board />} />
        <Route path="/macro" element={<Cockpit />} />
        <Route path="/stock/:code" element={<StockDetail />} />
        <Route path="/assist/picks" element={<AssistPicks />} />
        <Route path="/assist/holdings" element={<AssistHoldings />} />
        <Route path="/assist/review" element={<AssistReview />} />
        <Route path="/quant/backtest" element={<QuantBacktest />} />
        <Route path="/quant/factors" element={<QuantFactors />} />
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
Expected: 全部 Vitest 通过；`tsc -b` 无错；`vite build` 产出 dist/。

- [ ] **Step 6: 端到端冒烟**

```bash
cd /Volumes/demon/code/ml/study/stock
nohup python3 -m server > data_store/api.log 2>&1 &
sleep 6
curl -s -X POST http://127.0.0.1:8000/api/watchlist -H "Content-Type: application/json" -d '{"code":"600519"}' >/dev/null
echo -n "board: "; curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/api/board
cd web && nohup npm run dev > dev.log 2>&1 &
sleep 6
curl -s -o /dev/null -w "前端 HTTP %{http_code}\n" http://localhost:5173/
pkill -f vite; pkill -f "python3 -m server"
```
Expected: board 200；前端 200。

- [ ] **Step 7: README 追加 + 提交**

`README.md` 末尾追加：
```markdown
v3 首页：我的看板（自选∪持仓卡片：信号/迷你走势/买点止损/提醒 + 加自选）；驾驶舱/选票/复盘/量化收进导航「高级」。
```

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/App.tsx web/src/App.test.tsx web/src/components/Nav.tsx README.md
git commit -m "feat(web): 看板设为首页 + 导航降级量化(高级分组)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 v3 第 2 节前端）：
- 看板首页(大盘条+加自选+卡片:现价涨跌/迷你走势/信号/买点止损/提醒) → Task 3/4。✅
- 加自选(输入→POST→刷新) → Task 2 mutation + Task 4 表单。✅
- 卡片点进个股详情(/stock/:code) → Task 4 onOpen。✅
- 盘中轮询 → Task 2 useBoard `refetchInterval: live`。✅
- 导航降级(量化/驾驶舱/复盘收进"高级"，看板做首页) → Task 5。✅
- 深色沿用 v2.1 原子。✅

**占位符扫描**：无 TBD/TODO；每步含完整代码。✅

**类型一致性**：`BoardCard/BoardResp/WatchlistResp` 在 types/client/hooks/组件/页面一致；hooks 名(useBoard/useWatchlist/useAddWatch/useRemoveWatch)页面与测试一致；`buildSparklineOption` 与卡片一致；Nav/App 路由(/=Board,/macro=Cockpit)与测试一致。✅

**范围**：单一可测前端子系统(Vitest 全绿+build+冒烟)，消费 v3A 端点。✅

**已知取舍**：
- 大盘脸色条用 sentiment 简版(温度+涨跌家数)，不放整块宏观(宏观在 /macro)。
- board 后端已优化到 3只 ~4.8s(物化评分)；自选很多时仍会累积，后续可批量/缓存(YAGNI)。
- news 不在卡片(设计延后)。
- 现有 Cockpit.test 仍测 `/macro` 渲染(Cockpit 组件未改，仅路由迁移)，无需改动其测试。
