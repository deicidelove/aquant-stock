"""命令行入口：数据更新 / 查看 / 出图。

用法：
    python -m aquant.cli basic                     # 更新股票列表
    python -m aquant.cli daily 600519 000001       # 拉/增量更新若干股票日线
    python -m aquant.cli daily 600519 --start 20200101
    python -m aquant.cli flow                       # 个股资金流当日快照
    python -m aquant.cli sectors                    # 行业板块当日快照
    python -m aquant.cli summary                    # 本地仓库概览
    python -m aquant.cli kline 600519 --last 250    # 导出K线图
"""
from __future__ import annotations

import argparse

from .data import ingest, store


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="aquant", description="A股量化投研系统 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("basic", help="更新股票列表")

    p_daily = sub.add_parser("daily", help="拉取/增量更新日线")
    p_daily.add_argument("codes", nargs="+", help="6位股票代码")
    p_daily.add_argument("--start", default=None, help="起始日 YYYYMMDD（不增量时全量）")
    p_daily.add_argument("--full", action="store_true", help="全量重拉（忽略增量断点）")

    p_all = sub.add_parser("update-all", help="全市场增量入库（全A日线，可续跑）")
    p_all.add_argument("--start", default=None, help="首次入库历史起点 YYYYMMDD")
    p_all.add_argument("--throttle", type=float, default=0.15, help="每只间隔秒")
    p_all.add_argument("--include-bj", action="store_true", help="包含北交所")

    p_rd = sub.add_parser("run-daily", help="每日例程：更新+选股+出决策报告")
    p_rd.add_argument("--no-update", action="store_true", help="跳过数据更新，只重算决策")
    p_rd.add_argument("--top", type=int, default=30)
    p_rd.add_argument("--signal", default="ma_cross")
    p_rd.add_argument("--drop", nargs="*", default=None, choices=["科创", "创业", "北交"],
                      help="剔除板块（缩小股票域并提速）")

    p_rq = sub.add_parser("run-quarterly", help="季度换仓：出等权持仓组合")
    p_rq.add_argument("--top", type=int, default=50)

    sub.add_parser("backfill", help="把落后的股票补到全库最新交易日（不空扫）")

    p_seed = sub.add_parser("paper-seed", help="模拟盘：从过去某日按策略回放建仓到今天")
    p_seed.add_argument("--start", default="20250101", help="建仓起始日 YYYYMMDD")
    p_seed.add_argument("--top", type=int, default=50)
    p_seed.add_argument("--capital", type=float, default=1_000_000)
    sub.add_parser("paper-status", help="模拟盘：净值/绩效/持仓盈亏")
    p_reb = sub.add_parser("paper-rebalance", help="模拟盘：按当前 IC 策略调仓（实盘前向）")
    p_reb.add_argument("--top", type=int, default=50)

    p_tb = sub.add_parser("track-backfill", help="推荐台账：历史回放冷启动（周频）")
    p_tb.add_argument("--start", default="20240101", help="回放起始日 YYYYMMDD")
    p_tb.add_argument("--every", type=int, default=5, help="快照步长（交易日数）")
    p_tb.add_argument("--top", type=int, default=30)
    sub.add_parser("track-eval", help="推荐台账：出 live 记分卡（前向收益/超额/Rank-IC）")

    sub.add_parser("flow", help="个股资金流当日快照")
    sub.add_parser("sectors", help="行业板块当日快照")
    sub.add_parser("summary", help="本地仓库概览")
    sub.add_parser("market", help="大盘复盘（进攻/均衡/防守）+ 板块主线/轮动")

    p_k = sub.add_parser("kline", help="导出K线图")
    p_k.add_argument("code")
    p_k.add_argument("--last", type=int, default=250)

    p_rep = sub.add_parser("report", help="个股研投报告（一页式关键信息）")
    p_rep.add_argument("code")
    p_rep.add_argument("--save", default=None)

    p_brief = sub.add_parser("brief", help="荐股研报快览（候选池多维决策速览表）")
    p_brief.add_argument("--top", type=int, default=12)

    p_pick = sub.add_parser("pick", help="每日选股决策（选股+择时+关键价位）")
    p_pick.add_argument("--top", type=int, default=3,
                        help="每日建仓名单数量；默认综合分 Top3")
    p_pick.add_argument("--signal", default="ma_cross",
                        choices=["ma_cross", "breakout", "macd", "trend_filter"])
    p_pick.add_argument("--uptrend", action="store_true",
                        help="叠加上涨过滤(价>MA60)；默认关闭，与季度低波/反转策略一致")
    p_pick.add_argument("--drop", nargs="*", default=None, choices=["科创", "创业", "北交"],
                        help="剔除板块（缩小股票域并提速）")
    p_pick.add_argument("--save", default=None, help="另存 Markdown 到指定路径")

    args = ap.parse_args(argv)

    if args.cmd == "basic":
        print(f"stock_basic 写入 {ingest.ingest_basic()} 行")
    elif args.cmd == "daily":
        r = ingest.ingest_daily_many(args.codes, start=args.start,
                                     incremental=not args.full)
        print(r.to_string(index=False))
    elif args.cmd == "update-all":
        from .data import bulk
        bulk.update_all(start=args.start, throttle=args.throttle,
                        skip_bj=not args.include_bj)
    elif args.cmd == "run-daily":
        from . import pipeline
        print(pipeline.run_daily(update=not args.no_update, top=args.top, signal=args.signal,
                                 drop_boards=set(args.drop) if args.drop else None))
    elif args.cmd == "run-quarterly":
        from . import pipeline
        print(pipeline.run_quarterly(top=args.top))
    elif args.cmd == "backfill":
        from .data import bulk
        bulk.backfill_lagging()
    elif args.cmd == "paper-seed":
        from .paper import simulate
        start = f"{args.start[:4]}-{args.start[4:6]}-{args.start[6:]}" if len(args.start) == 8 else args.start
        print(simulate.seed(start=start, top=args.top, capital=args.capital))
        print("\n绩效:", simulate.performance())
    elif args.cmd == "paper-status":
        from .paper import account, simulate
        print("绩效:", simulate.performance())
        print(f"\n现金: {account.cash():,.0f}  总资产: {account.total_value(account.nav_series()['date'].iloc[-1]):,.0f}")
        print("\n持仓盈亏 Top/Bottom:")
        attr = simulate.attribution()
        if not attr.empty:
            print(attr.head(8).to_string(index=False))
            print("...")
            print(attr.tail(5).to_string(index=False))
    elif args.cmd == "paper-rebalance":
        from .paper import account
        from . import research
        codes = research.universe()
        ranked = __import__("aquant.select.scorer", fromlist=["score_fast"]).score_fast(
            codes=codes, top=args.top)
        day = store.query("SELECT max(date) d FROM daily_bar")["d"].iloc[0]
        print(account.rebalance(day, ranked["code"].tolist(), note="live"))
    elif args.cmd == "track-backfill":
        from . import track
        start = f"{args.start[:4]}-{args.start[4:6]}-{args.start[6:]}" if len(args.start) == 8 else args.start
        print(track.reconstruct(start=start, every=args.every, top=args.top))
    elif args.cmd == "track-eval":
        from . import config, track
        md = track.scorecard()
        print(md)
        out = config.ROOT / "reports" / "track_scorecard.md"
        out.write_text(md)
        print(f"\n已保存 → {out}")
    elif args.cmd == "flow":
        print(f"fund_flow 写入 {ingest.ingest_fund_flow()} 行")
    elif args.cmd == "sectors":
        print(f"sector_daily 写入 {ingest.ingest_sectors()} 行")
    elif args.cmd == "summary":
        print(store.summary().to_string(index=False))
    elif args.cmd == "market":
        from . import market, sector
        print(market.review_markdown())
        print()
        print(sector.review_markdown())
    elif args.cmd == "kline":
        from .dashboard.kline import save_png
        print(f"已导出 → {save_png(args.code, last_n=args.last)}")
    elif args.cmd == "brief":
        from . import research
        print(research.briefing(top=args.top).to_string(index=False))
    elif args.cmd == "report":
        from . import research
        md = research.dashboard_markdown(research.decision(args.code))
        print(md)
        if args.save:
            open(args.save, "w").write(md)
            print(f"\n已保存 → {args.save}")
    elif args.cmd == "pick":
        from . import research
        picks = research.daily_picks(top=args.top, signal=args.signal,
                                     require_uptrend=args.uptrend,
                                     drop_boards=set(args.drop) if args.drop else None)
        md = research.to_markdown(picks, signal=args.signal)
        print(md)
        if args.save:
            with open(args.save, "w") as f:
                f.write(md)
            print(f"\n已保存 → {args.save}")


if __name__ == "__main__":
    main()
