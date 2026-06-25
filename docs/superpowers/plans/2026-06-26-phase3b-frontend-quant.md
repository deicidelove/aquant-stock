# Phase 3B — 量化前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增"量化"前端板块（回测页 + 因子页），消费 Phase 3A 的异步任务端点，形成"看因子IC→调权重→回测→看净值/绩效"闭环。

**Architecture:** 沿用 1B/2B：纯展示组件 + TanStack Query（提交用 mutation 拿 job_id，轮询用带 `refetchInterval` 的 query，job 完成后停轮询）+ client 扩展 + ECharts 薄壳 + 纯 option 函数。新增 `/quant/*` 路由与导航入口。

**Tech Stack:** React 18 + TS + Vite · TanStack Query 5 · ECharts 5 · Tailwind · Vitest + @testing-library/react（沿用既有配置）。

## Global Constraints

- 全部前端代码在 `web/` 下；不动后端。
- 表现组件纯（props in → JSX），数据/提交只在 `hooks/queries.ts` 与 pages；组件测试 mock `../charts/EChart` 与 `../hooks/queries`。
- 轮询：job query 的 `refetchInterval` 为函数，`status` 为 `done`/`error` 时返回 `false` 停轮询，否则 1500ms。
- ECharts option 构造为纯函数（`charts/options.ts`，不 import echarts），单测覆盖；组件测试 mock EChart。
- RTL 精确匹配冲突时把插值值额外套元素（仅加 DOM、不改数据）。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `phase3b-frontend` 上开发；每 Task 末尾提交。从 `web/` 跑 `npx vitest run` / `npm test` / `npm run build`。
- 后端契约（Phase 3A 已上线）：
  - `GET /api/quant/weights` → `{ic:{factor:number}, momentum:{factor:number}}`
  - `POST /api/quant/backtest` body `{capital,weights,top_n,rebalance_every,min_history,start?,end?}` → `{job_id}`（`weights` 为预设名 `"ic"`/`"momentum"` 或 `{factor:weight}` dict）
  - `GET /api/quant/backtest/{job_id}` → `{job_id,kind,status,result,error}`；`result={nav:[{date,equity,benchmark}],metrics:{annual_return,sharpe,max_drawdown,win_rate,...},top_n,rebalance_every}`
  - `POST /api/quant/factor-ic` body `{factors?,fwd}` → `{job_id}`
  - `GET /api/quant/factor-ic/{job_id}` → `{...,result:{rows:[{factor,ic_mean,ic_std,ir,ic_win,n}],fwd}}`

---

### Task 1: 量化 API 类型 + client

**Files:**
- Modify: `web/src/api/types.ts`, `web/src/api/client.ts`
- Test: `web/src/api/client.quant.test.ts`

**Interfaces:**
- Produces（types.ts 追加）：`QuantWeights`, `BacktestParams`, `BacktestResult`, `FactorIcResult`, `QuantJob<T>`（`{job_id,kind,status,result:T|null,error:string|null}`）
- Produces（client.ts 追加，复用既有 `apiGet`/`apiSend`）：
  - `getQuantWeights(): Promise<QuantWeights>`
  - `submitBacktest(params: BacktestParams): Promise<{job_id:string}>`
  - `getBacktestJob(id: string): Promise<QuantJob<BacktestResult>>`
  - `submitFactorIc(params: {factors?:string[]; fwd:number}): Promise<{job_id:string}>`
  - `getFactorIcJob(id: string): Promise<QuantJob<FactorIcResult>>`

- [ ] **Step 1: 写失败测试**

`web/src/api/client.quant.test.ts`：
```typescript
import { describe, it, expect, vi, afterEach } from "vitest";
import { getQuantWeights, submitBacktest, getBacktestJob } from "./client";

afterEach(() => vi.restoreAllMocks());
function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok, status, json: async () => body } as Response);
}

describe("quant client", () => {
  it("getQuantWeights GETs presets", async () => {
    const f = mockFetch({ ic: { mom_20: 1 }, momentum: { mom_20: 1 } });
    await getQuantWeights();
    expect(f).toHaveBeenCalledWith("/api/quant/weights");
  });
  it("submitBacktest POSTs params", async () => {
    const f = mockFetch({ job_id: "abc" });
    const r = await submitBacktest({ capital: 1e6, weights: "ic", top_n: 5, rebalance_every: 5, min_history: 250 });
    expect(r.job_id).toBe("abc");
    const [url, opts] = f.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/quant/backtest");
    expect(opts.method).toBe("POST");
  });
  it("getBacktestJob GETs by id", async () => {
    const f = mockFetch({ job_id: "abc", kind: "backtest", status: "done", result: { nav: [], metrics: {} }, error: null });
    await getBacktestJob("abc");
    expect(f).toHaveBeenCalledWith("/api/quant/backtest/abc");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/api/client.quant.test.ts`
Expected: FAIL（未导出）

- [ ] **Step 3: 追加 types.ts**

`web/src/api/types.ts` 末尾追加：
```typescript
export type QuantWeights = { ic: Record<string, number>; momentum: Record<string, number> };

export interface BacktestParams {
  capital: number; weights: string | Record<string, number>;
  top_n: number; rebalance_every: number; min_history: number;
  start?: string; end?: string;
}
export interface BacktestResult {
  nav: { date: string; equity: number; benchmark: number | null }[];
  metrics: Record<string, number>;
  top_n: number; rebalance_every: number;
}
export interface FactorIcRow { factor: string; ic_mean: number; ic_std: number; ir: number; ic_win: number; n: number }
export interface FactorIcResult { rows: FactorIcRow[]; fwd: number }

export interface QuantJob<T> { job_id: string; kind: string; status: string; result: T | null; error: string | null }
```

- [ ] **Step 4: 追加 client.ts**

在 import 行补充新类型，并追加：
```typescript
export const getQuantWeights = () => apiGet<QuantWeights>("/quant/weights");
export const submitBacktest = (params: BacktestParams) => apiSend<{ job_id: string }>("/quant/backtest", "POST", params);
export const getBacktestJob = (id: string) => apiGet<QuantJob<BacktestResult>>(`/quant/backtest/${id}`);
export const submitFactorIc = (params: { factors?: string[]; fwd: number }) => apiSend<{ job_id: string }>("/quant/factor-ic", "POST", params);
export const getFactorIcJob = (id: string) => apiGet<QuantJob<FactorIcResult>>(`/quant/factor-ic/${id}`);
```
（import 行追加：`QuantWeights, BacktestParams, BacktestResult, FactorIcResult, QuantJob`。）

- [ ] **Step 5: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/api/client.quant.test.ts`
Expected: PASS（3 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/api
git commit -m "feat(web): 量化 API 类型 + client

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 量化 hooks（权重 + 提交 mutation + 轮询 query）

**Files:**
- Modify: `web/src/hooks/queries.ts`
- Test: `web/src/hooks/queries.quant.test.tsx`

**Interfaces:**
- Consumes: Task 1 client
- Produces：
  - `useQuantWeights()`、`useSubmitBacktest()`（mutation）、`useBacktestJob(jobId: string | null)`（query，`enabled:!!jobId`，`refetchInterval` 在 done/error 停）、`useSubmitFactorIc()`、`useFactorIcJob(jobId)`

- [ ] **Step 1: 写失败测试**

`web/src/hooks/queries.quant.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getQuantWeights: vi.fn(async () => ({ ic: { mom_20: 1 }, momentum: { mom_20: 1 } })),
  getBacktestJob: vi.fn(async () => ({ job_id: "abc", kind: "backtest", status: "done", result: { nav: [], metrics: { sharpe: 1 }, top_n: 5, rebalance_every: 5 }, error: null })),
}));
import { useQuantWeights, useBacktestJob } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("quant hooks", () => {
  it("useQuantWeights returns presets", async () => {
    const { result } = renderHook(() => useQuantWeights(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.ic.mom_20).toBe(1);
  });
  it("useBacktestJob polls when jobId set and returns done", async () => {
    const { result } = renderHook(() => useBacktestJob("abc"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.status).toBe("done");
  });
  it("useBacktestJob disabled when jobId null", () => {
    const { result } = renderHook(() => useBacktestJob(null), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/hooks/queries.quant.test.tsx`
Expected: FAIL（未导出）

- [ ] **Step 3: 追加 hooks**

`web/src/hooks/queries.ts` 末尾追加（`useQuery`/`useMutation` 已 import）：
```typescript
import type { QuantJob } from "../api/types";

const jobPoll = (q: { state: { data?: { status?: string } } }) => {
  const s = q.state.data?.status;
  return s === "done" || s === "error" ? false : 1500;
};

export const useQuantWeights = () =>
  useQuery({ queryKey: ["quant-weights"], queryFn: api.getQuantWeights });

export const useSubmitBacktest = () =>
  useMutation({ mutationFn: api.submitBacktest });

export const useBacktestJob = (jobId: string | null) =>
  useQuery({
    queryKey: ["backtest-job", jobId],
    queryFn: () => api.getBacktestJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: jobPoll as unknown as number | false,
  });

export const useSubmitFactorIc = () =>
  useMutation({ mutationFn: api.submitFactorIc });

export const useFactorIcJob = (jobId: string | null) =>
  useQuery({
    queryKey: ["factor-ic-job", jobId],
    queryFn: () => api.getFactorIcJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: jobPoll as unknown as number | false,
  });
```
注：`refetchInterval` 接受 `(query)=>number|false` 函数；此处用 `jobPoll` 在 done/error 停轮询。类型断言规避 TanStack 泛型签名差异。

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/hooks/queries.quant.test.tsx`
Expected: PASS（3 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/hooks
git commit -m "feat(web): 量化 hooks（权重/提交/轮询）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 图表 option 纯函数（净值曲线 + 因子IC条形）

**Files:**
- Modify: `web/src/charts/options.ts`
- Test: `web/src/charts/options.quant.test.ts`

**Interfaces:**
- Consumes: `api/types` 的 `BacktestResult["nav"]`、`FactorIcRow`
- Produces：
  - `buildNavLineOption(nav: {date:string;equity:number;benchmark:number|null}[]): object`（双折线：策略 equity + 基准 benchmark；x=date）
  - `buildFactorIcBarOption(rows: {factor:string;ir:number}[]): object`（横向条形：各因子 IR，正红负绿）

- [ ] **Step 1: 写失败测试**

`web/src/charts/options.quant.test.ts`：
```typescript
import { describe, it, expect } from "vitest";
import { buildNavLineOption, buildFactorIcBarOption } from "./options";

describe("quant chart options", () => {
  it("buildNavLineOption maps two series over dates", () => {
    const nav = [
      { date: "2026-06-01", equity: 1.0, benchmark: 1.0 },
      { date: "2026-06-02", equity: 1.05, benchmark: 1.02 },
    ];
    const opt = buildNavLineOption(nav) as any;
    expect(opt.xAxis.data).toEqual(["2026-06-01", "2026-06-02"]);
    expect(opt.series).toHaveLength(2);
    expect(opt.series[0].data).toEqual([1.0, 1.05]);
    expect(opt.series[1].data).toEqual([1.0, 1.02]);
  });
  it("buildFactorIcBarOption maps factor IR bars", () => {
    const opt = buildFactorIcBarOption([{ factor: "volatility_20", ir: 0.47 }, { factor: "mom_20", ir: -0.41 }]) as any;
    expect(opt.series[0].type).toBe("bar");
    expect(opt.yAxis.data).toEqual(["volatility_20", "mom_20"]);
    expect(opt.series[0].data[0].value).toBe(0.47);
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/charts/options.quant.test.ts`
Expected: FAIL（未导出）

- [ ] **Step 3: 追加 options.ts**

`web/src/charts/options.ts` 末尾追加：
```typescript
export function buildNavLineOption(nav: { date: string; equity: number; benchmark: number | null }[]): object {
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["策略", "沪深300"], top: 0 },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: nav.map((p) => p.date) },
    yAxis: { type: "value", scale: true },
    dataZoom: [{ type: "inside" }, { type: "slider" }],
    series: [
      { name: "策略", type: "line", showSymbol: false, data: nav.map((p) => p.equity), itemStyle: { color: "#ef4444" } },
      { name: "沪深300", type: "line", showSymbol: false, data: nav.map((p) => p.benchmark), itemStyle: { color: "#9ca3af" } },
    ],
  };
}

export function buildFactorIcBarOption(rows: { factor: string; ir: number }[]): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 110, right: 20, top: 10, bottom: 30 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: rows.map((r) => r.factor) },
    series: [{
      type: "bar",
      data: rows.map((r) => ({ value: r.ir, itemStyle: { color: r.ir >= 0 ? "#ef4444" : "#22c55e" } })),
    }],
  };
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/charts/options.quant.test.ts`
Expected: PASS（2 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/charts
git commit -m "feat(web): 净值曲线 + 因子IR 条形 option 纯函数

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 回测配置表单 BacktestForm + 绩效卡 MetricsCard

**Files:**
- Create: `web/src/components/BacktestForm.tsx`, `web/src/components/MetricsCard.tsx`, `web/src/components/Backtest.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `QuantWeights`、`BacktestParams`
- Produces：
  - `BacktestForm({ presets, onSubmit }: { presets: QuantWeights; onSubmit: (p: BacktestParams) => void })` —— 预设下拉（ic/momentum，选中填充各因子权重为可编辑数字输入）+ 金额/TopN/调仓周期/最小历史输入 + 提交；提交把当前权重 map（可编辑后的）作为 `weights` dict 传出
  - `MetricsCard({ metrics }: { metrics: Record<string, number> })` —— 年化/夏普/最大回撤/胜率四数字（缺失显示 —）

- [ ] **Step 1: 写失败测试**

`web/src/components/Backtest.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import BacktestForm from "./BacktestForm";
import MetricsCard from "./MetricsCard";

const presets = { ic: { mom_20: -0.41, volatility_20: 0.47 }, momentum: { mom_20: 1.0 } };

describe("BacktestForm / MetricsCard", () => {
  it("submits weights map + params (preset populated, editable)", () => {
    const onSubmit = vi.fn();
    render(<BacktestForm presets={presets} onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("Top-N"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ top_n: 3, weights: expect.objectContaining({ mom_20: -0.41, volatility_20: 0.47 }) }),
    );
  });
  it("MetricsCard shows annual/sharpe/drawdown/winrate (rendered as %/2dp)", () => {
    render(<MetricsCard metrics={{ annual_return: 0.18, sharpe: 1.4, max_drawdown: -0.22, win_rate: 0.55 }} />);
    expect(screen.getByText("1.40")).toBeInTheDocument();      // sharpe 两位小数
    expect(screen.getByText("-22.0%")).toBeInTheDocument();    // 最大回撤百分比
    expect(screen.getByText("18.0%")).toBeInTheDocument();     // 年化百分比
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/components/Backtest.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件**

`web/src/components/BacktestForm.tsx`：
```tsx
import { useState } from "react";
import type { QuantWeights, BacktestParams } from "../api/types";

export default function BacktestForm({ presets, onSubmit }: { presets: QuantWeights; onSubmit: (p: BacktestParams) => void }) {
  const [preset, setPreset] = useState<keyof QuantWeights>("ic");
  const [weights, setWeights] = useState<Record<string, number>>({ ...presets.ic });
  const [capital, setCapital] = useState("1000000");
  const [topN, setTopN] = useState("5");
  const [rebalance, setRebalance] = useState("5");
  const [minHistory, setMinHistory] = useState("250");

  const pickPreset = (name: keyof QuantWeights) => {
    setPreset(name);
    setWeights({ ...presets[name] });
  };
  const setW = (f: string, v: string) => setWeights((w) => ({ ...w, [f]: Number(v) }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      capital: Number(capital), weights, top_n: Number(topN),
      rebalance_every: Number(rebalance), min_history: Number(minHistory),
    });
  };

  return (
    <form onSubmit={submit} className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">回测配置</h2>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <label className="flex flex-col">权重预设
          <select aria-label="权重预设" value={preset} onChange={(e) => pickPreset(e.target.value as keyof QuantWeights)} className="border p-1">
            <option value="ic">IC加权</option><option value="momentum">动量风格</option>
          </select>
        </label>
        <label className="flex flex-col">初始金额<input aria-label="初始金额" type="number" value={capital} onChange={(e) => setCapital(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">Top-N<input aria-label="Top-N" type="number" value={topN} onChange={(e) => setTopN(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">调仓周期<input aria-label="调仓周期" type="number" value={rebalance} onChange={(e) => setRebalance(e.target.value)} className="border p-1" /></label>
        <label className="flex flex-col">最小历史<input aria-label="最小历史" type="number" value={minHistory} onChange={(e) => setMinHistory(e.target.value)} className="border p-1" /></label>
      </div>
      <div className="mt-3 text-sm">
        <div className="text-gray-500">因子权重（可调）</div>
        <div className="mt-1 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {Object.keys(weights).map((f) => (
            <label key={f} className="flex items-center justify-between gap-1">
              <span className="truncate">{f}</span>
              <input aria-label={f} type="number" step="0.01" value={weights[f]} onChange={(e) => setW(f, e.target.value)} className="w-20 border p-1" />
            </label>
          ))}
        </div>
      </div>
      <button type="submit" className="mt-3 rounded bg-blue-600 px-3 py-1 text-white">运行回测</button>
    </form>
  );
}
```

`web/src/components/MetricsCard.tsx`：
```tsx
const FMT: [string, string, (v: number) => string][] = [
  ["annual_return", "年化", (v) => (v * 100).toFixed(1) + "%"],
  ["sharpe", "夏普", (v) => v.toFixed(2)],
  ["max_drawdown", "最大回撤", (v) => (v * 100).toFixed(1) + "%"],
  ["win_rate", "胜率", (v) => (v * 100).toFixed(1) + "%"],
];

export default function MetricsCard({ metrics }: { metrics: Record<string, number> }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">绩效</h2>
      <div className="mt-2 grid grid-cols-2 gap-3 text-center sm:grid-cols-4">
        {FMT.map(([k, label, fmt]) => (
          <div key={k} className="rounded bg-gray-50 p-2">
            <div className="text-gray-500 text-sm">{label}</div>
            <div className="text-base font-semibold"><span>{k in metrics ? fmt(metrics[k]) : "—"}</span></div>
          </div>
        ))}
      </div>
    </section>
  );
}
```
- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/components/Backtest.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/BacktestForm.tsx web/src/components/MetricsCard.tsx web/src/components/Backtest.test.tsx
git commit -m "feat(web): 回测配置表单 + 绩效卡组件

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 因子IC面板 FactorIcPanel

**Files:**
- Create: `web/src/components/FactorIcPanel.tsx`, `web/src/components/FactorIcPanel.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `FactorIcRow`；`charts/EChart`（mock）+ `buildFactorIcBarOption`
- Produces: `FactorIcPanel({ rows }: { rows: FactorIcRow[] })` —— IR 条形图（EChart）+ 明细表（factor/ic_mean/ir/ic_win/n）

- [ ] **Step 1: 写失败测试**

`web/src/components/FactorIcPanel.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import FactorIcPanel from "./FactorIcPanel";

describe("FactorIcPanel", () => {
  it("renders chart and factor rows", () => {
    render(<FactorIcPanel rows={[{ factor: "volatility_20", ic_mean: 0.02, ic_std: 0.1, ir: 0.47, ic_win: 0.6, n: 100 }]} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    expect(screen.getByText("volatility_20")).toBeInTheDocument();
  });
  it("shows empty hint when no rows", () => {
    render(<FactorIcPanel rows={[]} />);
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/components/FactorIcPanel.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件**

`web/src/components/FactorIcPanel.tsx`：
```tsx
import type { FactorIcRow } from "../api/types";
import EChart from "../charts/EChart";
import { buildFactorIcBarOption } from "../charts/options";

export default function FactorIcPanel({ rows }: { rows: FactorIcRow[] }) {
  if (rows.length === 0) {
    return (
      <section className="rounded-lg border border-gray-200 p-4">
        <h2 className="text-lg font-bold">因子 IC / IR</h2>
        <p className="mt-2 text-sm text-gray-400">暂无因子数据。</p>
      </section>
    );
  }
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">因子 IC / IR</h2>
      <EChart option={buildFactorIcBarOption(rows)} height={Math.max(160, rows.length * 28)} />
      <table className="mt-2 w-full text-sm">
        <thead className="text-gray-500"><tr><th className="text-left">因子</th><th className="text-right">IC均值</th><th className="text-right">IR</th><th className="text-right">IC胜率</th><th className="text-right">N</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.factor} className="border-b">
              <td>{r.factor}</td><td className="text-right">{r.ic_mean}</td><td className="text-right">{r.ir}</td><td className="text-right">{r.ic_win}</td><td className="text-right">{r.n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/components/FactorIcPanel.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/FactorIcPanel.tsx web/src/components/FactorIcPanel.test.tsx
git commit -m "feat(web): 因子 IC/IR 面板

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 回测页 QuantBacktest

**Files:**
- Create: `web/src/pages/QuantBacktest.tsx`, `web/src/pages/QuantBacktest.test.tsx`

**Interfaces:**
- Consumes: hooks `useQuantWeights/useSubmitBacktest/useBacktestJob`；组件 `BacktestForm/MetricsCard`；`charts/EChart`(mock)+`buildNavLineOption`；本地 state 存 `jobId`
- Produces: `QuantBacktest()` —— 表单提交→`useSubmitBacktest.mutate(params,{onSuccess: d=>setJobId(d.job_id)})`→`useBacktestJob(jobId)` 轮询；running 显示"回测中…"，done 渲染净值曲线 + MetricsCard

- [ ] **Step 1: 写失败测试（mock hooks，done 态）**

`web/src/pages/QuantBacktest.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useQuantWeights: () => ({ isSuccess: true, data: { ic: { mom_20: 1 }, momentum: { mom_20: 1 } } }),
  useSubmitBacktest: () => ({ mutate: vi.fn() }),
  useBacktestJob: () => ({ data: { status: "done", result: { nav: [{ date: "2026-06-01", equity: 1, benchmark: 1 }], metrics: { sharpe: 1.4 }, top_n: 5, rebalance_every: 5 } } }),
}));
import QuantBacktest from "./QuantBacktest";

describe("QuantBacktest", () => {
  it("renders form + result when job done", () => {
    render(<QuantBacktest />);
    expect(screen.getByText("回测配置")).toBeInTheDocument();
    expect(screen.getByText("绩效")).toBeInTheDocument();
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/pages/QuantBacktest.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写页面**

`web/src/pages/QuantBacktest.tsx`：
```tsx
import { useState } from "react";
import { useQuantWeights, useSubmitBacktest, useBacktestJob } from "../hooks/queries";
import BacktestForm from "../components/BacktestForm";
import MetricsCard from "../components/MetricsCard";
import EChart from "../charts/EChart";
import { buildNavLineOption } from "../charts/options";

export default function QuantBacktest() {
  const [jobId, setJobId] = useState<string | null>(null);
  const weights = useQuantWeights();
  const submit = useSubmitBacktest();
  const job = useBacktestJob(jobId);

  const run = (params: Parameters<typeof submit.mutate>[0]) =>
    submit.mutate(params, { onSuccess: (d: { job_id: string }) => setJobId(d.job_id) });

  const status = job.data?.status;
  const result = job.data?.result;
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">回测</h1>
      {weights.isSuccess && <BacktestForm presets={weights.data} onSubmit={run} />}
      {jobId && status !== "done" && status !== "error" && <p className="text-sm text-gray-400">回测中…</p>}
      {status === "error" && <p className="text-sm text-red-600">回测失败：{job.data?.error}</p>}
      {status === "done" && result && (
        <>
          <MetricsCard metrics={result.metrics} />
          <section className="rounded-lg border border-gray-200 p-4">
            <h2 className="text-lg font-bold">净值曲线</h2>
            <EChart option={buildNavLineOption(result.nav)} height={360} />
          </section>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/pages/QuantBacktest.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/QuantBacktest.tsx web/src/pages/QuantBacktest.test.tsx
git commit -m "feat(web): 回测页 QuantBacktest（提交+轮询+净值+绩效）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: 因子页 QuantFactors

**Files:**
- Create: `web/src/pages/QuantFactors.tsx`, `web/src/pages/QuantFactors.test.tsx`

**Interfaces:**
- Consumes: hooks `useSubmitFactorIc/useFactorIcJob`；组件 `FactorIcPanel`；本地 state 存 jobId
- Produces: `QuantFactors()` —— "跑因子IC"按钮→submit→轮询→done 渲染 `FactorIcPanel`

- [ ] **Step 1: 写失败测试**

`web/src/pages/QuantFactors.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useSubmitFactorIc: () => ({ mutate: vi.fn() }),
  useFactorIcJob: () => ({ data: { status: "done", result: { rows: [{ factor: "volatility_20", ic_mean: 0.02, ic_std: 0.1, ir: 0.47, ic_win: 0.6, n: 100 }], fwd: 5 } } }),
}));
import QuantFactors from "./QuantFactors";

describe("QuantFactors", () => {
  it("renders run button and factor panel when done", () => {
    render(<QuantFactors />);
    expect(screen.getByRole("button", { name: /跑因子/ })).toBeInTheDocument();
    expect(screen.getByText("volatility_20")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/pages/QuantFactors.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写页面**

`web/src/pages/QuantFactors.tsx`：
```tsx
import { useState } from "react";
import { useSubmitFactorIc, useFactorIcJob } from "../hooks/queries";
import FactorIcPanel from "../components/FactorIcPanel";

export default function QuantFactors() {
  const [jobId, setJobId] = useState<string | null>(null);
  const submit = useSubmitFactorIc();
  const job = useFactorIcJob(jobId);
  const run = () => submit.mutate({ fwd: 5 }, { onSuccess: (d: { job_id: string }) => setJobId(d.job_id) });

  const status = job.data?.status;
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">因子</h1>
      <button onClick={run} className="rounded bg-blue-600 px-3 py-1 text-white">跑因子IC</button>
      {jobId && status !== "done" && status !== "error" && <p className="text-sm text-gray-400">计算中…</p>}
      {status === "error" && <p className="text-sm text-red-600">失败：{job.data?.error}</p>}
      {status === "done" && job.data?.result && <FactorIcPanel rows={job.data.result.rows} />}
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd web && npx vitest run src/pages/QuantFactors.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/QuantFactors.tsx web/src/pages/QuantFactors.test.tsx
git commit -m "feat(web): 因子页 QuantFactors（提交+轮询+IC排名）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: 导航量化入口 + 路由 + 构建

**Files:**
- Modify: `web/src/components/Nav.tsx`, `web/src/App.tsx`, `web/src/App.test.tsx`, `README.md`

**Interfaces:**
- Produces: Nav 增"量化回测"`/quant/backtest`、"因子"`/quant/factors` 链接；App 增两条路由

- [ ] **Step 1: 改测试断言（App 增量化链接）**

`web/src/App.test.tsx` 在现有断言后追加：
```tsx
    expect(screen.getByRole("link", { name: "量化回测" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "因子" })).toBeInTheDocument();
```

- [ ] **Step 2: 运行确认失败**

Run: `cd web && npx vitest run src/App.test.tsx`
Expected: FAIL（无量化链接）

- [ ] **Step 3: 改 Nav + App**

`web/src/components/Nav.tsx` 的 `LINKS` 追加两项：
```tsx
  ["/quant/backtest", "量化回测"], ["/quant/factors", "因子"],
```

`web/src/App.tsx`：import 两个页面并加路由：
```tsx
import QuantBacktest from "./pages/QuantBacktest";
import QuantFactors from "./pages/QuantFactors";
```
在 `<Routes>` 内追加：
```tsx
        <Route path="/quant/backtest" element={<QuantBacktest />} />
        <Route path="/quant/factors" element={<QuantFactors />} />
```

- [ ] **Step 4: 运行确认通过**

Run: `cd web && npx vitest run src/App.test.tsx`
Expected: PASS

- [ ] **Step 5: 全套测试 + 构建**

Run: `cd web && npm test && npm run build`
Expected: 全部 Vitest 用例通过；`tsc -b` 无错误，`vite build` 产出 dist/。

- [ ] **Step 6: README 追加量化说明 + 提交**

`README.md` 末尾追加：
```markdown
量化板块：量化回测 `/quant/backtest`（配置→异步回测→净值+绩效）· 因子 `/quant/factors`（因子 IC/IR 排名）。
```

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/Nav.tsx web/src/App.tsx web/src/App.test.tsx README.md
git commit -m "feat(web): 导航量化入口 + 量化路由装配

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照 Phase 3 设计第 2 节前端）：
- 回测页（配置表单：金额/权重预设+可调因子权重/TopN/调仓/最小历史 → 提交 → 轮询 → 净值曲线 vs 沪深300 + 绩效卡）→ Task 4/6 + Task 3(nav option)。✅
- 因子页（提交 IC 任务 → 轮询 → IR 排名条形+表）→ Task 5/7 + Task 3(ic option)。✅
- 轮询 done/error 停 → Task 2 `jobPoll`。✅
- 导航入口 → Task 8。✅
- "点因子回填到回测权重"的跨页联动：**本期不做**（两页独立；用户看因子页 IC 后手动在回测表单调权重）。已在此标注为简化。

**占位符扫描**：无 TBD/TODO；每步含完整代码。MetricsCard 测试断言已对齐渲染值（`18.0%`/`1.40`/`-22.0%`）。✅

**类型一致性**：`QuantWeights/BacktestParams/BacktestResult/FactorIcRow/FactorIcResult/QuantJob` 在 types/client/hooks/组件/页面一致；hooks 名（useQuantWeights/useSubmitBacktest/useBacktestJob/useSubmitFactorIc/useFactorIcJob）页面与测试一致；`buildNavLineOption/buildFactorIcBarOption` 在 options 与组件/页面一致。✅

**范围**：单一可测前端子系统（Vitest 全绿 + build），消费已上线 Phase 3A API。✅
```
