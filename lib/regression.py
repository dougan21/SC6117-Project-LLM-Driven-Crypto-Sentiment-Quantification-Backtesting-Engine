# 8. 回测结果的统计指标计算


def _estimate_bars_per_year(index: pd.DatetimeIndex) -> float:
    """Estimate how many bars per year based on the index frequency."""
    if len(index) < 2:
        return 252.0  # 随便给个默认值


    total_days = (index[-1] - index[0]).total_seconds() / (3600 * 24)
    if total_days <= 0:
        return 252.0


    bars_per_day = len(index) / total_days
    return bars_per_day * 252.0



def compute_backtest_stats(
    equity_curve: pd.Series,
    trades: list[TradeRecord],
) -> BacktestStats:
    """Compute basic performance statistics from equity curve and trades."""
    equity_curve = equity_curve.sort_index()
    returns = equity_curve.pct_change().dropna()


    if len(equity_curve) == 0:
        return BacktestStats(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            num_trades=0,
        )


    total_return = float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0)


    bars_per_year = _estimate_bars_per_year(equity_curve.index)


    avg_ret = returns.mean()
    vol = returns.std()


    if vol > 0:
        sharpe = float((avg_ret * bars_per_year**0.5) / vol)
    else:
        sharpe = 0.0


    # 年化收益（简单版本）：(1 + 日均收益)^(bars_per_year) - 1
    annualized_return = float((1.0 + avg_ret) ** bars_per_year - 1.0)
    volatility = float(vol * (bars_per_year**0.5))


    # 最大回撤
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    max_drawdown = float(drawdown.min())


    # 胜率和交易次数
    num_trades = len(trades)
    if num_trades > 0:
        wins = [1 for tr in trades if tr.pnl > 0]
        win_rate = float(len(wins) / num_trades)
    else:
        win_rate = 0.0


    return BacktestStats(
        total_return=total_return,
        annualized_return=annualized_return,
        volatility=volatility,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        num_trades=num_trades,
    )