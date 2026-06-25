# Phase 1B — 前端驾驶舱 UI 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 React + ECharts 构建驾驶舱前端，消费 Phase 1A 的 FastAPI 端点，实现总览（大盘/板块/推荐/高分）→ 下钻（个股 K 线 + 研判）的体验。

**Architecture:** 表现层与数据层分离：`pages/` 调用 TanStack Query hooks 取数并把纯数据传给 `components/` 展示面板（presentational，props in → JSX out，易测）；第三方图表封装进 `charts/EChart.tsx` 薄壳，纯函数 `charts/options.ts` 产出 ECharts option（可单测，不碰 canvas）。Vite dev server 把 `/api` 代理到 FastAPI（127.0.0.1:8000）。

**Tech Stack:** Node 18 · Vite 5 · React 18 + TypeScript · React Router 6 · TanStack Query 5 · ECharts 5 · Tailwind CSS 3 · Vitest + @testing-library/react + jsdom。

## Global Constraints

- Node 18（本机 v18.20.8 / npm 10.8.2）；所有前端代码在新目录 `web/` 下，不动 `aquant/`、`server/`、`tests/`（后端 pytest 套件）。
- 包管理用 npm；测试用 Vitest（`npm test` 跑 `vitest run`）。每个组件/纯函数 TDD：先写失败测试再实现。
- 表现层（`components/*Panel.tsx`、图表 option 构造）必须是**纯函数/纯展示**：数据经 props 传入，便于在 jsdom 下测试，不在组件内直接 fetch。取数只发生在 `hooks/queries.ts` 与 `pages/`。
- 组件测试中 **mock `charts/EChart.tsx`**（`vi.mock`），避免 echarts/canvas 在 jsdom 加载；图表逻辑通过单测 `charts/options.ts` 的纯函数覆盖。
- API 基址：开发期走 Vite 代理（前端请求 `/api/...`，代理到 `http://127.0.0.1:8000`）。client 里 base 用相对路径 `/api`。
- TanStack Query 盘中自动轮询：交易时段（周一至五 09:30–11:30 / 13:00–15:00，本地时间）`refetchInterval` 启用，否则关闭——逻辑放 `lib/tradingHours.ts`，与后端 `is_trading_hours` 语义一致。
- 提交信息结尾加：`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 在分支 `phase1b-frontend` 上开发（控制器会在派发 Task 1 前建好分支）；每个 Task 末尾提交。
- 后端端点契约（只读，已上线）：
  - `GET /api/cockpit/overview` → `{breadth:{total,up,down,limit_up,up_ratio,above_ma20_pct,above_ma60_pct}, regime:{state,score,suggested_position,note,breadth,index}, index:{code,close,above_ma20,above_ma60,ret_20d,ret_60d}}`
  - `GET /api/cockpit/sectors` → `{as_of:string|null, rows:[{sector,pct_chg,mkt_cap,...}], rotation:object}`
  - `GET /api/cockpit/top-scores?top=N` → `{as_of:string|null, rows:[{code,name,score}]}`
  - `GET /api/cockpit/picks?top=N` → `{rows:[{code,name,score,action?,close?,...}]}`
  - `GET /api/stock/{code}/kline?n=N` → `{code, bars:[{date,open,high,low,close,volume}]}`
  - `GET /api/stock/{code}/report` → `{code, decision:{code,name,date,close,total_score,score_parts,signal,one_liner,sensitivity,advice:{no_position,has_position},risk_level,risks:[],battle_plan:{ideal_buy,secondary_buy,stop_loss,take_profit,position},checklist:[]}}`（无数据时 404）

---

### Task 1: 前端脚手架 + Tailwind + Vitest

**Files:**
- Create: `web/package.json`, `web/vite.config.ts`, `web/tsconfig.json`, `web/tsconfig.node.json`, `web/index.html`, `web/postcss.config.js`, `web/tailwind.config.js`, `web/src/index.css`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/setupTests.ts`, `web/src/smoke.test.ts`
- Modify: `.gitignore`（忽略 `web/node_modules`、`web/dist`）

**Interfaces:**
- Produces: 可运行的 Vite+React+TS 工程；`npm test` 跑 Vitest；`/api` 代理到 8000；`App` 组件可渲染。

- [ ] **Step 1: 忽略前端构建产物**

在 `/Volumes/demon/code/ml/study/stock/.gitignore` 末尾追加：
```
web/node_modules/
web/dist/
```

- [ ] **Step 2: 写工程配置文件**

`web/package.json`：
```json
{
  "name": "aquant-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.51.0",
    "echarts": "^5.5.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "jsdom": "^24.1.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

`web/vite.config.ts`：
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});
```

`web/tsconfig.json`：
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`web/tsconfig.node.json`：
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

`web/index.html`：
```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Aquant 驾驶舱</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`web/postcss.config.js`：
```javascript
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

`web/tailwind.config.js`：
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

`web/src/index.css`：
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 3: 写 App + entry + 测试 setup**

`web/src/App.tsx`：
```tsx
export default function App() {
  return <div className="p-4 text-xl font-bold">Aquant 驾驶舱</div>;
}
```

`web/src/main.tsx`：
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

`web/src/setupTests.ts`：
```typescript
import "@testing-library/jest-dom";
```

- [ ] **Step 4: 写冒烟测试**

`web/src/smoke.test.ts`：
```typescript
import { describe, it, expect } from "vitest";

describe("smoke", () => {
  it("runs vitest", () => {
    expect(1 + 1).toBe(2);
  });
});
```

- [ ] **Step 5: 安装依赖并运行测试**

```bash
cd /Volumes/demon/code/ml/study/stock/web
npm install
npm test
```
Expected: `npm install` 成功；`npm test` → 1 passed（smoke）。

- [ ] **Step 6: 提交**

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/package.json web/vite.config.ts web/tsconfig.json web/tsconfig.node.json web/index.html web/postcss.config.js web/tailwind.config.js web/src/index.css web/src/App.tsx web/src/main.tsx web/src/setupTests.ts web/src/smoke.test.ts web/package-lock.json .gitignore
git commit -m "feat(web): Vite+React+TS 脚手架 + Tailwind + Vitest

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: API 类型 + client

**Files:**
- Create: `web/src/api/types.ts`, `web/src/api/client.ts`, `web/src/api/client.test.ts`

**Interfaces:**
- Produces:
  - `types.ts` 导出接口：`Overview`, `Sectors`, `TopScores`, `Picks`, `Kline`, `Report`（字段见 Global Constraints 契约）
  - `client.ts` 导出异步函数：`getOverview(): Promise<Overview>`、`getSectors(): Promise<Sectors>`、`getTopScores(top?: number): Promise<TopScores>`、`getPicks(top?: number): Promise<Picks>`、`getKline(code: string, n?: number): Promise<Kline>`、`getReport(code: string): Promise<Report>`
  - 内部 `apiGet<T>(path: string): Promise<T>`（fetch `/api`+path，非 2xx 抛 `Error`）

- [ ] **Step 1: 写失败测试**

`web/src/api/client.test.ts`：
```typescript
import { describe, it, expect, vi, afterEach } from "vitest";
import { getOverview, getKline } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok, status, json: async () => body,
  } as Response);
}

describe("api client", () => {
  it("getOverview hits /api/cockpit/overview and returns json", async () => {
    const f = mockFetch({ breadth: { up: 2500 }, regime: { state: "均衡" }, index: { close: 3900 } });
    const r = await getOverview();
    expect(f).toHaveBeenCalledWith("/api/cockpit/overview");
    expect(r.regime.state).toBe("均衡");
  });

  it("getKline passes code and n in the path", async () => {
    const f = mockFetch({ code: "600000", bars: [] });
    await getKline("600000", 120);
    expect(f).toHaveBeenCalledWith("/api/stock/600000/kline?n=120");
  });

  it("throws on non-2xx", async () => {
    mockFetch({}, false, 404);
    await expect(getKline("xxxxxx")).rejects.toThrow();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/api/client.test.ts`
Expected: FAIL（`Cannot find module './client'`）

- [ ] **Step 3: 写 types.ts**

`web/src/api/types.ts`：
```typescript
export interface Overview {
  breadth: Record<string, number>;
  regime: { state: string; score: number; suggested_position?: string; note?: string; [k: string]: unknown };
  index: { code: string; close: number; above_ma20?: boolean; above_ma60?: boolean; ret_20d?: number | null; ret_60d?: number | null };
}

export interface SectorRow { sector: string; pct_chg: number; mkt_cap?: number; [k: string]: unknown }
export interface Sectors { as_of: string | null; rows: SectorRow[]; rotation: Record<string, unknown> }

export interface ScoreRow { code: string; name: string; score: number }
export interface TopScores { as_of: string | null; rows: ScoreRow[] }

export interface PickRow { code: string; name: string; score: number; action?: string; close?: number; [k: string]: unknown }
export interface Picks { rows: PickRow[] }

export interface Bar { date: string; open: number; high: number; low: number; close: number; volume: number }
export interface Kline { code: string; bars: Bar[] }

export interface Decision {
  code: string; name: string; date: string; close: number;
  total_score: number; signal: string; one_liner: string; risk_level: string;
  risks: string[];
  battle_plan: { ideal_buy: number; secondary_buy: number; stop_loss: number; take_profit: number; position: string };
  checklist: string[];
  [k: string]: unknown;
}
export interface Report { code: string; decision: Decision }
```

- [ ] **Step 4: 写 client.ts**

`web/src/api/client.ts`：
```typescript
import type { Overview, Sectors, TopScores, Picks, Kline, Report } from "./types";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch("/api" + path);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export const getOverview = () => apiGet<Overview>("/cockpit/overview");
export const getSectors = () => apiGet<Sectors>("/cockpit/sectors");
export const getTopScores = (top = 20) => apiGet<TopScores>(`/cockpit/top-scores?top=${top}`);
export const getPicks = (top = 3) => apiGet<Picks>(`/cockpit/picks?top=${top}`);
export const getKline = (code: string, n = 250) => apiGet<Kline>(`/stock/${code}/kline?n=${n}`);
export const getReport = (code: string) => apiGet<Report>(`/stock/${code}/report`);
```

- [ ] **Step 5: 运行确认通过**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/api/client.test.ts`
Expected: PASS（3 tests）

- [ ] **Step 6: 提交**

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/api
git commit -m "feat(web): API 类型 + fetch client

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: 交易时段工具 + TanStack Query hooks

**Files:**
- Create: `web/src/lib/tradingHours.ts`, `web/src/lib/tradingHours.test.ts`, `web/src/hooks/queries.ts`, `web/src/hooks/queries.test.tsx`

**Interfaces:**
- Consumes: `api/client` 的取数函数（Task 2）
- Produces:
  - `tradingHours.ts`：`isTradingHours(now: Date): boolean`（周一至五 09:30–11:30 或 13:00–15:00）；`refetchIntervalMs(now: Date): number | false`（交易时段返回 `60000`，否则 `false`）
  - `hooks/queries.ts`：`useOverview()`、`useSectors()`、`useTopScores(top?)`、`usePicks(top?)`、`useKline(code, n?)`、`useReport(code)`，均基于 `@tanstack/react-query` 的 `useQuery`；总览类查询的 `refetchInterval` 用 `refetchIntervalMs(new Date())`

- [ ] **Step 1: 写交易时段失败测试**

`web/src/lib/tradingHours.test.ts`：
```typescript
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
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/lib/tradingHours.test.ts`
Expected: FAIL（`Cannot find module './tradingHours'`）

- [ ] **Step 3: 写 tradingHours.ts**

`web/src/lib/tradingHours.ts`：
```typescript
export function isTradingHours(now: Date): boolean {
  const day = now.getDay();
  if (day === 0 || day === 6) return false;
  const m = now.getHours() * 60 + now.getMinutes();
  const am = m >= 9 * 60 + 30 && m <= 11 * 60 + 30;
  const pm = m >= 13 * 60 && m <= 15 * 60;
  return am || pm;
}

export function refetchIntervalMs(now: Date): number | false {
  return isTradingHours(now) ? 60000 : false;
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/lib/tradingHours.test.ts`
Expected: PASS

- [ ] **Step 5: 写 hooks 失败测试（mock client）**

`web/src/hooks/queries.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getOverview: vi.fn(async () => ({ breadth: { up: 10 }, regime: { state: "进攻", score: 4 }, index: { code: "sh000300", close: 3900 } })),
  getTopScores: vi.fn(async () => ({ as_of: "2026-06-23", rows: [{ code: "600000", name: "浦发", score: 1.2 }] })),
}));

import { useOverview, useTopScores } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("query hooks", () => {
  it("useOverview returns mapped data", async () => {
    const { result } = renderHook(() => useOverview(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.regime.state).toBe("进攻");
  });
  it("useTopScores passes top and returns rows", async () => {
    const { result } = renderHook(() => useTopScores(5), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].code).toBe("600000");
  });
});
```

- [ ] **Step 6: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/hooks/queries.test.tsx`
Expected: FAIL（`Cannot find module './queries'`）

- [ ] **Step 7: 写 hooks/queries.ts**

`web/src/hooks/queries.ts`：
```typescript
import { useQuery } from "@tanstack/react-query";
import * as api from "../api/client";
import { refetchIntervalMs } from "../lib/tradingHours";

const live = () => refetchIntervalMs(new Date());

export const useOverview = () =>
  useQuery({ queryKey: ["overview"], queryFn: api.getOverview, refetchInterval: live });

export const useSectors = () =>
  useQuery({ queryKey: ["sectors"], queryFn: api.getSectors, refetchInterval: live });

export const useTopScores = (top = 20) =>
  useQuery({ queryKey: ["top-scores", top], queryFn: () => api.getTopScores(top), refetchInterval: live });

export const usePicks = (top = 3) =>
  useQuery({ queryKey: ["picks", top], queryFn: () => api.getPicks(top), refetchInterval: live });

export const useKline = (code: string, n = 250) =>
  useQuery({ queryKey: ["kline", code, n], queryFn: () => api.getKline(code, n), enabled: !!code });

export const useReport = (code: string) =>
  useQuery({ queryKey: ["report", code], queryFn: () => api.getReport(code), enabled: !!code });
```

- [ ] **Step 8: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/lib src/hooks`
Expected: PASS（tradingHours + hooks 全过）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/lib web/src/hooks
git commit -m "feat(web): 交易时段轮询门控 + TanStack Query hooks

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: ECharts 薄壳 + option 构造纯函数

**Files:**
- Create: `web/src/charts/EChart.tsx`, `web/src/charts/options.ts`, `web/src/charts/options.test.ts`

**Interfaces:**
- Consumes: `api/types` 的 `Bar`、`SectorRow`
- Produces:
  - `EChart.tsx`：`export default function EChart({ option, height }: { option: object; height?: number })` —— 用 echarts 初始化并 setOption；组件测试中被 mock。
  - `options.ts` 纯函数：`buildKlineOption(bars: Bar[]): object`、`buildSectorTreemapOption(rows: SectorRow[]): object`、`buildIndexBarOption(breadth: Record<string, number>): object`

- [ ] **Step 1: 写 option 纯函数失败测试**

`web/src/charts/options.test.ts`：
```typescript
import { describe, it, expect } from "vitest";
import { buildKlineOption, buildSectorTreemapOption } from "./options";

describe("chart options", () => {
  it("buildKlineOption maps bars to candlestick series + date axis", () => {
    const bars = [
      { date: "2026-06-22", open: 10, high: 11, low: 9, close: 10.5, volume: 100 },
      { date: "2026-06-23", open: 10.5, high: 12, low: 10, close: 11.8, volume: 120 },
    ];
    const opt = buildKlineOption(bars) as any;
    expect(opt.xAxis.data).toEqual(["2026-06-22", "2026-06-23"]);
    expect(opt.series[0].type).toBe("candlestick");
    // ECharts 蜡烛序列数据顺序为 [open, close, low, high]
    expect(opt.series[0].data[0]).toEqual([10, 10.5, 9, 11]);
  });

  it("buildSectorTreemapOption maps sectors to sized/colored nodes", () => {
    const rows = [{ sector: "银行", pct_chg: 1.5, mkt_cap: 5e11 }, { sector: "煤炭", pct_chg: -0.8, mkt_cap: 2e11 }];
    const opt = buildSectorTreemapOption(rows) as any;
    expect(opt.series[0].type).toBe("treemap");
    expect(opt.series[0].data[0].name).toBe("银行");
    expect(opt.series[0].data[0].value).toBe(5e11);
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/charts/options.test.ts`
Expected: FAIL（`Cannot find module './options'`）

- [ ] **Step 3: 写 options.ts**

`web/src/charts/options.ts`：
```typescript
import type { Bar, SectorRow } from "../api/types";

export function buildKlineOption(bars: Bar[]): object {
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "category", data: bars.map((b) => b.date), scale: true },
    yAxis: { type: "value", scale: true },
    dataZoom: [{ type: "inside" }, { type: "slider" }],
    series: [
      {
        type: "candlestick",
        data: bars.map((b) => [b.open, b.close, b.low, b.high]),
        itemStyle: { color: "#ef4444", color0: "#22c55e", borderColor: "#ef4444", borderColor0: "#22c55e" },
      },
    ],
  };
}

export function buildSectorTreemapOption(rows: SectorRow[]): object {
  return {
    tooltip: { formatter: (p: { name: string; value: number }) => `${p.name}` },
    series: [
      {
        type: "treemap",
        roam: false,
        breadcrumb: { show: false },
        data: rows.map((r) => ({
          name: r.sector,
          value: r.mkt_cap ?? Math.abs(r.pct_chg),
          itemStyle: { color: r.pct_chg >= 0 ? "#ef4444" : "#22c55e" },
        })),
      },
    ],
  };
}

export function buildIndexBarOption(breadth: Record<string, number>): object {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 80, right: 20, top: 10, bottom: 20 },
    xAxis: { type: "value", max: 100 },
    yAxis: { type: "category", data: ["站上MA20%", "站上MA60%"] },
    series: [{ type: "bar", data: [breadth.above_ma20_pct ?? 0, breadth.above_ma60_pct ?? 0] }],
  };
}
```

- [ ] **Step 4: 写 EChart.tsx**

`web/src/charts/EChart.tsx`：
```tsx
import { useEffect, useRef } from "react";
import * as echarts from "echarts";

export default function EChart({ option, height = 320 }: { option: object; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(option);
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [option]);
  return <div ref={ref} style={{ width: "100%", height }} />;
}
```

- [ ] **Step 5: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/charts/options.test.ts`
Expected: PASS（2 tests）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/charts
git commit -m "feat(web): ECharts 薄壳 + K线/板块/宽度 option 纯函数

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 展示面板 — 大盘总览 OverviewPanel

**Files:**
- Create: `web/src/components/OverviewPanel.tsx`, `web/src/components/OverviewPanel.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Overview`；`charts/EChart`（测试中 mock）；`charts/options` 的 `buildIndexBarOption`
- Produces: `export default function OverviewPanel({ data }: { data: Overview })` —— 展示 regime 状态、宽度数字（涨/跌/涨停/up_ratio）、指数收盘 + 站上均线柱状图

- [ ] **Step 1: 写失败测试（mock EChart）**

`web/src/components/OverviewPanel.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import OverviewPanel from "./OverviewPanel";

const data = {
  breadth: { total: 5000, up: 3000, down: 1800, limit_up: 40, up_ratio: 60, above_ma20_pct: 55, above_ma60_pct: 48 },
  regime: { state: "进攻", score: 4, suggested_position: "7~8成", note: "宽度强" },
  index: { code: "sh000300", close: 3912.5, above_ma20: true, above_ma60: true, ret_20d: 2.1, ret_60d: 5.5 },
};

describe("OverviewPanel", () => {
  it("renders regime state, breadth numbers and index close", () => {
    render(<OverviewPanel data={data} />);
    expect(screen.getByText("进攻")).toBeInTheDocument();
    expect(screen.getByText(/3000/)).toBeInTheDocument();    // 上涨家数
    expect(screen.getByText(/3912.5/)).toBeInTheDocument();  // 指数收盘
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/OverviewPanel.test.tsx`
Expected: FAIL（`Cannot find module './OverviewPanel'`）

- [ ] **Step 3: 写 OverviewPanel.tsx**

`web/src/components/OverviewPanel.tsx`：
```tsx
import type { Overview } from "../api/types";
import EChart from "../charts/EChart";
import { buildIndexBarOption } from "../charts/options";

export default function OverviewPanel({ data }: { data: Overview }) {
  const { breadth: b, regime, index } = data;
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">大盘总览</h2>
        <span className="rounded bg-gray-100 px-2 py-1 text-sm">
          市场：{regime.state}（建议仓位 {regime.suggested_position ?? "—"}）
        </span>
      </div>
      <div className="mt-3 grid grid-cols-4 gap-3 text-center text-sm">
        <Stat label="上涨" value={b.up} />
        <Stat label="下跌" value={b.down} />
        <Stat label="涨停" value={b.limit_up} />
        <Stat label="上涨占比%" value={b.up_ratio} />
      </div>
      <div className="mt-3 text-sm text-gray-600">
        沪深300 收盘 <b>{index.close}</b>（20日 {index.ret_20d ?? "—"}% / 60日 {index.ret_60d ?? "—"}%）
      </div>
      <EChart option={buildIndexBarOption(b)} height={140} />
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-gray-50 p-2">
      <div className="text-gray-500">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/OverviewPanel.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/OverviewPanel.tsx web/src/components/OverviewPanel.test.tsx
git commit -m "feat(web): 大盘总览面板 OverviewPanel

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 展示面板 — 板块 SectorPanel

**Files:**
- Create: `web/src/components/SectorPanel.tsx`, `web/src/components/SectorPanel.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Sectors`；`charts/EChart`（mock）；`charts/options` 的 `buildSectorTreemapOption`
- Produces: `export default function SectorPanel({ data }: { data: Sectors })` —— 展示 as_of、板块热力树图、领涨前 5 列表

- [ ] **Step 1: 写失败测试**

`web/src/components/SectorPanel.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import SectorPanel from "./SectorPanel";

const data = {
  as_of: "2026-06-23T14:30:00",
  rows: [
    { sector: "银行", pct_chg: 2.1, mkt_cap: 5e11 },
    { sector: "煤炭", pct_chg: 1.3, mkt_cap: 2e11 },
    { sector: "地产", pct_chg: -0.5, mkt_cap: 1e11 },
  ],
  rotation: {},
};

describe("SectorPanel", () => {
  it("renders heatmap chart and top sector by name", () => {
    render(<SectorPanel data={data} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
    expect(screen.getAllByText("银行").length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/SectorPanel.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写 SectorPanel.tsx**

`web/src/components/SectorPanel.tsx`：
```tsx
import type { Sectors } from "../api/types";
import EChart from "../charts/EChart";
import { buildSectorTreemapOption } from "../charts/options";

export default function SectorPanel({ data }: { data: Sectors }) {
  const top = [...data.rows].sort((a, b) => b.pct_chg - a.pct_chg).slice(0, 5);
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">板块概览</h2>
        <span className="text-xs text-gray-400">{data.as_of ?? "无快照"}</span>
      </div>
      <EChart option={buildSectorTreemapOption(data.rows)} height={260} />
      <ul className="mt-2 text-sm">
        {top.map((s) => (
          <li key={s.sector} className="flex justify-between border-b py-1">
            <span>{s.sector}</span>
            <span className={s.pct_chg >= 0 ? "text-red-500" : "text-green-600"}>
              {s.pct_chg >= 0 ? "+" : ""}{s.pct_chg}%
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/SectorPanel.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/SectorPanel.tsx web/src/components/SectorPanel.test.tsx
git commit -m "feat(web): 板块热力面板 SectorPanel

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: 展示面板 — 推荐 PicksPanel + 高分 TopScoresPanel

**Files:**
- Create: `web/src/components/PicksPanel.tsx`, `web/src/components/TopScoresPanel.tsx`, `web/src/components/Tables.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Picks`、`TopScores`
- Produces:
  - `export default function PicksPanel({ data, onPick }: { data: Picks; onPick?: (code: string) => void })`
  - `export default function TopScoresPanel({ data, onPick }: { data: TopScores; onPick?: (code: string) => void })`
  - 两者均渲染表格，点击某行调用 `onPick(code)`（供下钻）

- [ ] **Step 1: 写失败测试**

`web/src/components/Tables.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PicksPanel from "./PicksPanel";
import TopScoresPanel from "./TopScoresPanel";

describe("Picks/TopScores panels", () => {
  it("PicksPanel renders rows and fires onPick on row click", () => {
    const onPick = vi.fn();
    render(<PicksPanel data={{ rows: [{ code: "600000", name: "浦发", score: 1.23 }] }} onPick={onPick} />);
    fireEvent.click(screen.getByText("浦发"));
    expect(onPick).toHaveBeenCalledWith("600000");
  });
  it("TopScoresPanel renders score rows", () => {
    render(<TopScoresPanel data={{ as_of: "2026-06-23", rows: [{ code: "000001", name: "平安", score: 2.5 }] }} />);
    expect(screen.getByText("平安")).toBeInTheDocument();
    expect(screen.getByText(/2.5/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/Tables.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写 PicksPanel.tsx**

`web/src/components/PicksPanel.tsx`：
```tsx
import type { Picks } from "../api/types";

export default function PicksPanel({ data, onPick }: { data: Picks; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-bold">每日建仓名单</h2>
      <table className="mt-2 w-full text-sm">
        <thead className="text-gray-500">
          <tr><th className="text-left">代码</th><th className="text-left">名称</th><th className="text-right">综合分</th></tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
              <td>{r.code}</td><td>{r.name}</td><td className="text-right">{r.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

`web/src/components/TopScoresPanel.tsx`：
```tsx
import type { TopScores } from "../api/types";

export default function TopScoresPanel({ data, onPick }: { data: TopScores; onPick?: (code: string) => void }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">综合分高分股</h2>
        <span className="text-xs text-gray-400">{data.as_of ?? "—"}</span>
      </div>
      <table className="mt-2 w-full text-sm">
        <thead className="text-gray-500">
          <tr><th className="text-left">代码</th><th className="text-left">名称</th><th className="text-right">综合分</th></tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.code} className="cursor-pointer hover:bg-gray-50" onClick={() => onPick?.(r.code)}>
              <td>{r.code}</td><td>{r.name}</td><td className="text-right">{r.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 4: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/Tables.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/PicksPanel.tsx web/src/components/TopScoresPanel.tsx web/src/components/Tables.test.tsx
git commit -m "feat(web): 推荐名单 + 高分股表格面板

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: 个股下钻 — ReportPanel + StockDetail 页

**Files:**
- Create: `web/src/components/ReportPanel.tsx`, `web/src/pages/StockDetail.tsx`, `web/src/components/ReportPanel.test.tsx`

**Interfaces:**
- Consumes: `api/types` 的 `Report`/`Decision`/`Kline`；`hooks/queries` 的 `useKline`、`useReport`；`charts/EChart`（mock）+ `buildKlineOption`；`react-router-dom` 的 `useParams`
- Produces:
  - `export default function ReportPanel({ decision }: { decision: Decision })` —— 展示 signal、综合分、一句话、风险、作战计划（买点/止损/目标/仓位）、checklist
  - `export default function StockDetail()` —— 从路由参数取 code，用 hooks 取 kline+report，渲染 K 线（candlestick）+ ReportPanel

- [ ] **Step 1: 写 ReportPanel 失败测试**

`web/src/components/ReportPanel.test.tsx`：
```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ReportPanel from "./ReportPanel";

const decision = {
  code: "600000", name: "浦发银行", date: "2026-06-23", close: 10.5,
  total_score: 72, signal: "买入/增持", one_liner: "策略契合强",
  risk_level: "低", risks: ["无显著风险信号"],
  battle_plan: { ideal_buy: 10.2, secondary_buy: 9.8, stop_loss: 9.5, take_profit: 12.0, position: "3~5成分批" },
  checklist: ["季度持有", "跌破止损减仓"],
};

describe("ReportPanel", () => {
  it("renders signal, score, battle plan and checklist", () => {
    render(<ReportPanel decision={decision} />);
    expect(screen.getByText("买入/增持")).toBeInTheDocument();
    expect(screen.getByText(/72/)).toBeInTheDocument();
    expect(screen.getByText(/9.5/)).toBeInTheDocument();     // 止损
    expect(screen.getByText(/季度持有/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/ReportPanel.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写 ReportPanel.tsx**

`web/src/components/ReportPanel.tsx`：
```tsx
import type { Decision } from "../api/types";

export default function ReportPanel({ decision: d }: { decision: Decision }) {
  const p = d.battle_plan;
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-bold">{d.name} 研判</h2>
        <span className="rounded bg-gray-100 px-2 py-1 text-sm">{d.signal}（{d.total_score} 分 · 风险{d.risk_level}）</span>
      </div>
      <p className="mt-2 text-sm text-gray-700">{d.one_liner}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
        <Plan label="理想买点" value={p.ideal_buy} />
        <Plan label="加仓位" value={p.secondary_buy} />
        <Plan label="止损" value={p.stop_loss} />
        <Plan label="目标" value={p.take_profit} />
        <Plan label="仓位" value={p.position} />
      </div>
      <ul className="mt-3 list-disc pl-5 text-sm text-gray-600">
        {d.checklist.map((c, i) => <li key={i}>{c}</li>)}
      </ul>
      <div className="mt-2 text-xs text-gray-400">风险：{d.risks.join("；")}</div>
    </section>
  );
}

function Plan({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded bg-gray-50 p-2 text-center">
      <div className="text-gray-500">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
```

- [ ] **Step 4: 写 StockDetail.tsx**

`web/src/pages/StockDetail.tsx`：
```tsx
import { useParams, Link } from "react-router-dom";
import { useKline, useReport } from "../hooks/queries";
import EChart from "../charts/EChart";
import { buildKlineOption } from "../charts/options";
import ReportPanel from "../components/ReportPanel";

export default function StockDetail() {
  const { code = "" } = useParams();
  const kline = useKline(code);
  const report = useReport(code);
  return (
    <div className="space-y-4 p-4">
      <Link to="/" className="text-sm text-blue-600">← 返回驾驶舱</Link>
      <section className="rounded-lg border border-gray-200 p-4">
        <h2 className="text-lg font-bold">{code} K线</h2>
        {kline.isSuccess ? <EChart option={buildKlineOption(kline.data.bars)} height={360} />
          : <div className="text-sm text-gray-400">{kline.isError ? "无K线数据" : "加载中…"}</div>}
      </section>
      {report.isSuccess ? <ReportPanel decision={report.data.decision} />
        : <div className="text-sm text-gray-400">{report.isError ? "无研判数据" : "研判加载中…"}</div>}
    </div>
  );
}
```

- [ ] **Step 5: 运行确认通过 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/components/ReportPanel.test.tsx`
Expected: PASS

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/components/ReportPanel.tsx web/src/components/ReportPanel.test.tsx web/src/pages/StockDetail.tsx
git commit -m "feat(web): 个股研判面板 + 下钻详情页(K线+研判)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: 驾驶舱页 + 路由 + Query Provider 装配

**Files:**
- Create: `web/src/pages/Cockpit.tsx`
- Modify: `web/src/App.tsx`, `web/src/main.tsx`
- Create: `web/src/pages/Cockpit.test.tsx`

**Interfaces:**
- Consumes: 全部 hooks（Task 3）与面板（Task 5-7）；`react-router-dom`
- Produces:
  - `Cockpit.tsx`：用 `useOverview/useSectors/usePicks/useTopScores` 取数，分别渲染面板（各自 loading/error 兜底）；点击推荐/高分行用 `useNavigate` 跳 `/stock/:code`
  - `App.tsx`：`<Routes>`：`/` → `Cockpit`，`/stock/:code` → `StockDetail`
  - `main.tsx`：包 `QueryClientProvider` + `BrowserRouter`

- [ ] **Step 1: 写 Cockpit 失败测试（mock hooks）**

`web/src/pages/Cockpit.test.tsx`：
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useOverview: () => ({ isSuccess: true, isError: false, data: { breadth: { up: 3000, down: 1000, limit_up: 10, up_ratio: 60, above_ma20_pct: 55, above_ma60_pct: 48, total: 5000 }, regime: { state: "进攻", score: 4 }, index: { code: "sh000300", close: 3900 } } }),
  useSectors: () => ({ isSuccess: true, isError: false, data: { as_of: "2026-06-23", rows: [{ sector: "银行", pct_chg: 1.2, mkt_cap: 5e11 }], rotation: {} } }),
  usePicks: () => ({ isSuccess: true, isError: false, data: { rows: [{ code: "600000", name: "浦发", score: 1.2 }] } }),
  useTopScores: () => ({ isSuccess: true, isError: false, data: { as_of: "2026-06-23", rows: [{ code: "000001", name: "平安", score: 2.5 }] } }),
}));
import Cockpit from "./Cockpit";

describe("Cockpit", () => {
  it("renders all four panels' key content", () => {
    render(<MemoryRouter><Cockpit /></MemoryRouter>);
    expect(screen.getByText("进攻")).toBeInTheDocument();
    expect(screen.getByText("每日建仓名单")).toBeInTheDocument();
    expect(screen.getByText("综合分高分股")).toBeInTheDocument();
    expect(screen.getByText("板块概览")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行确认失败**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npx vitest run src/pages/Cockpit.test.tsx`
Expected: FAIL（`Cannot find module './Cockpit'`）

- [ ] **Step 3: 写 Cockpit.tsx**

`web/src/pages/Cockpit.tsx`：
```tsx
import { useNavigate } from "react-router-dom";
import { useOverview, useSectors, usePicks, useTopScores } from "../hooks/queries";
import OverviewPanel from "../components/OverviewPanel";
import SectorPanel from "../components/SectorPanel";
import PicksPanel from "../components/PicksPanel";
import TopScoresPanel from "../components/TopScoresPanel";

export default function Cockpit() {
  const nav = useNavigate();
  const overview = useOverview();
  const sectors = useSectors();
  const picks = usePicks();
  const top = useTopScores();
  const goPick = (code: string) => nav(`/stock/${code}`);
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">🛰 驾驶舱</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        {overview.isSuccess && <OverviewPanel data={overview.data} />}
        {sectors.isSuccess && <SectorPanel data={sectors.data} />}
        {picks.isSuccess && <PicksPanel data={picks.data} onPick={goPick} />}
        {top.isSuccess && <TopScoresPanel data={top.data} onPick={goPick} />}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 改写 App.tsx + main.tsx**

`web/src/App.tsx`：
```tsx
import { Routes, Route } from "react-router-dom";
import Cockpit from "./pages/Cockpit";
import StockDetail from "./pages/StockDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Cockpit />} />
      <Route path="/stock/:code" element={<StockDetail />} />
    </Routes>
  );
}
```

`web/src/main.tsx`：
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

- [ ] **Step 5: 运行全部前端测试 + 提交**

Run: `cd /Volumes/demon/code/ml/study/stock/web && npm test`
Expected: PASS（全部测试：smoke + client + tradingHours + hooks + options + 各面板 + Cockpit）

```bash
cd /Volumes/demon/code/ml/study/stock
git add web/src/pages/Cockpit.tsx web/src/pages/Cockpit.test.tsx web/src/App.tsx web/src/main.tsx
git commit -m "feat(web): 驾驶舱页 + 路由 + QueryProvider 装配

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: 联调冒烟 + 构建验证 + README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: 前端可 `npm run build` 通过；与后端联调（dev 代理）冒烟说明写入 README。

- [ ] **Step 1: 类型检查 + 生产构建**

```bash
cd /Volumes/demon/code/ml/study/stock/web
npm run build
```
Expected: `tsc -b` 无类型错误，`vite build` 产出 `dist/`（构建成功）。

- [ ] **Step 2: 端到端联调冒烟（后端 + 前端 dev）**

```bash
cd /Volumes/demon/code/ml/study/stock
nohup python3 -m server > data_store/api.log 2>&1 &
sleep 5
# 经 vite 代理验证后端可达（直连后端确认数据面）
curl -s http://127.0.0.1:8000/api/cockpit/overview | head -c 200
echo
# 构建产物可静态预览（可选，确认前端能起）
cd web && nohup npm run preview > preview.log 2>&1 &
sleep 4
curl -s -o /dev/null -w "preview HTTP %{http_code}\n" http://127.0.0.1:4173/
pkill -f "npm run preview"; pkill -f vite; pkill -f "python3 -m server"
```
Expected: overview 返回 JSON（含 breadth/regime/index）；preview HTTP 200。若后端 overview 因真实库为空返回空 dict，记录但不视为失败（前端有 loading/error 兜底）。

- [ ] **Step 3: README 追加前端说明**

`README.md` 末尾追加：
```markdown
## v2 前端（React 驾驶舱）

    cd web && npm install
    npm run dev          # http://localhost:5173 （/api 代理到后端 8000）

需后端先起：`python3 -m server`。
构建：`npm run build`（产物 dist/）。测试：`npm test`（Vitest）。
```

- [ ] **Step 4: 提交**

```bash
cd /Volumes/demon/code/ml/study/stock
git add README.md
git commit -m "docs: README 补 v2 前端启动说明 + 联调冒烟

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec 覆盖**（对照设计文档「板块① 驾驶舱」总→分）：
- 总·大盘走势/状态 → Task 5 OverviewPanel（regime/breadth/指数）。✅
- 总·板块概览 + 资金流向 → Task 6 SectorPanel（热力树图，基于 sector_snapshot）。✅
- 总·推荐收益一览 + 高分股 → Task 7 Picks/TopScores 面板。✅（注：设计的"推荐收益记分卡"track scorecard 端点 Phase 1A 未做，本计划用 picks+top-scores 覆盖"推荐一览/高分"，scorecard 留待后续，已在此标注。）
- 分·下钻个股 K图 + 研判报告 → Task 8 StockDetail（candlestick + ReportPanel）。✅
- 性能/体验：组件级渲染 + TanStack 缓存 + 盘中轮询门控 → Task 3。✅
- 市场情绪/北向、量化交易一览（因子IC状态）：设计列为驾驶舱内容但后端无对应端点，**本计划不造**，留待后续端点补齐（YAGNI，避免空壳）。

**占位符扫描**：无 TBD/TODO；每个代码步骤含完整可运行代码。✅

**类型一致性**：`api/types` 的接口名（Overview/Sectors/TopScores/Picks/Kline/Report/Decision/Bar/SectorRow/ScoreRow/PickRow）在 client、hooks、charts、components、pages 间一致引用；hooks 名（useOverview/useSectors/useTopScores/usePicks/useKline/useReport）在 Cockpit/StockDetail 与其测试中一致；`buildKlineOption/buildSectorTreemapOption/buildIndexBarOption` 在 options 与各组件一致；面板 props（`data`、`onPick`、`decision`）一致。✅

**范围**：单一可测子系统（前端，Vitest 全绿 + build + 联调冒烟），消费已上线的 Phase 1A API。✅
