"""Simple, auditable backtest implementation for uploaded XSP/SPX price data."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    short_delta: float = 0.13
    width: float = 5.0
    dte: int = 35
    credit_ratio: float = 0.20
    profit_target: float = 0.50
    stop_multiple: float = 2.0
    exit_dte: int = 14
    contracts: int = 1
    multiplier: int = 100


def normalize_price_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize a CSV with Date and Close columns; reject ambiguous inputs."""
    if frame is None or frame.empty:
        raise ValueError("No price data was supplied.")
    cols = {str(c).strip().lower(): c for c in frame.columns}
    date_col = next((cols[c] for c in ("date", "datetime", "timestamp") if c in cols), None)
    close_col = next((cols[c] for c in ("close", "adj close", "price") if c in cols), None)
    if date_col is None or close_col is None:
        raise ValueError("CSV must contain a Date/Datetime column and a Close/Price column.")
    out = frame[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna().sort_values("date").drop_duplicates("date")
    if len(out) < 60:
        raise ValueError("At least 60 valid observations are required for the 200-day trend filter proxy.")
    return out.reset_index(drop=True)


def run_backtest(frame: pd.DataFrame, config: BacktestConfig) -> tuple[pd.DataFrame, dict]:
    data = normalize_price_data(frame).copy()
    data["sma200"] = data["close"].rolling(200, min_periods=20).mean()
    data["ema20"] = data["close"].ewm(span=20, adjust=False).mean()
    data["ema50"] = data["close"].ewm(span=50, adjust=False).mean()
    data["eligible"] = (data["close"] > data["sma200"]) & (data["ema20"] > data["ema50"])
    data["ret"] = data["close"].pct_change().fillna(0.0)
    data["trade_pnl"] = 0.0
    data["trade_id"] = np.nan
    data["exit_reason"] = ""
    trade_rows = []
    trade_id = 0
    i = 0
    while i < len(data) - config.dte:
        if not bool(data.loc[i, "eligible"]):
            i += 1
            continue
        entry = float(data.loc[i, "close"])
        # Deterministic proxy for strike and premium when historical option chains are not uploaded.
        short_strike = entry * (1.0 - config.short_delta)
        credit = config.width * config.credit_ratio
        max_profit = credit * config.multiplier * config.contracts
        max_loss = (config.width - credit) * config.multiplier * config.contracts
        exit_idx, reason, pnl = min(i + config.dte, len(data) - 1), "Expiry", max_profit
        for j in range(i + 1, min(i + config.dte, len(data) - 1) + 1):
            move = float(data.loc[j, "close"] / entry - 1.0)
            # Conservative mark proxy: losses accelerate as spot approaches the short strike.
            intrinsic = max(short_strike - float(data.loc[j, "close"]), 0.0)
            mark_pnl = max_profit - min(max_loss, intrinsic * config.multiplier * config.contracts)
            dte_remaining = config.dte - (j - i)
            if mark_pnl >= max_profit * config.profit_target:
                exit_idx, reason, pnl = j, "Profit target", mark_pnl
                break
            if mark_pnl <= -max_profit * config.stop_multiple:
                exit_idx, reason, pnl = j, "Stop loss", mark_pnl
                break
            if dte_remaining <= config.exit_dte:
                exit_idx, reason, pnl = j, "14 DTE time stop", mark_pnl
                break
        trade_id += 1
        data.loc[i:exit_idx, "trade_id"] = trade_id
        data.loc[exit_idx, "trade_pnl"] = pnl
        data.loc[exit_idx, "exit_reason"] = reason
        trade_rows.append({"Trade": trade_id, "Entry": data.loc[i, "date"], "Exit": data.loc[exit_idx, "date"], "P&L": pnl, "Reason": reason, "Return on max risk": pnl / max_loss if max_loss else 0.0})
        i = max(exit_idx + 1, i + 1)
    trades = pd.DataFrame(trade_rows)
    data["equity"] = data["trade_pnl"].cumsum()
    data["peak"] = data["equity"].cummax()
    data["drawdown"] = data["equity"] - data["peak"]
    if trades.empty:
        metrics = {"trades": 0, "win_rate": 0.0, "profit_factor": 0.0, "expected_value": 0.0, "sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0, "max_drawdown_duration": 0}
    else:
        wins = trades.loc[trades["P&L"] > 0, "P&L"]
        losses = trades.loc[trades["P&L"] <= 0, "P&L"]
        daily = data["equity"].diff().fillna(0.0)
        downside = daily[daily < 0]
        metrics = {
            "trades": int(len(trades)),
            "win_rate": float((trades["P&L"] > 0).mean()),
            "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() else float("inf"),
            "expected_value": float(trades["P&L"].mean()),
            "sharpe": float(daily.mean() / daily.std() * np.sqrt(252)) if daily.std() else 0.0,
            "sortino": float(daily.mean() / downside.std() * np.sqrt(252)) if downside.std() else 0.0,
            "max_drawdown": float(data["drawdown"].min()),
            "max_drawdown_duration": int(_max_drawdown_duration(data["drawdown"]))
        }
    return data, {"metrics": metrics, "trades": trades}


def _max_drawdown_duration(drawdown: pd.Series) -> int:
    best = current = 0
    for value in drawdown:
        current = current + 1 if value < 0 else 0
        best = max(best, current)
    return best
