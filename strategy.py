"""Rule evaluation for bull put spread entries and exits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class MarketContext:
    spot: float
    sma200: float
    ema20: float
    ema50: float
    iv_rank: float
    hours_to_fomc_or_cpi: Optional[float] = None


@dataclass(frozen=True)
class TradeParameters:
    dte: int
    short_delta: float
    width: float
    credit: float
    contracts: int = 1


def entry_filter(context: MarketContext, trade: TradeParameters) -> Dict[str, object]:
    checks = {
        "Bullish trend": context.spot > context.sma200 and context.ema20 > context.ema50,
        "IVR >= 20": context.iv_rank >= 20,
        "DTE 30-45": 30 <= trade.dte <= 45,
        "Short delta 10-16": 0.10 <= abs(trade.short_delta) <= 0.16,
        "Wing width valid": trade.width in (5, 10) or 5 <= trade.width <= 10,
        "Credit >= 15% width": trade.credit >= trade.width * 0.15,
        "Macro blackout clear": context.hours_to_fomc_or_cpi is None or context.hours_to_fomc_or_cpi > 24,
    }
    return {"checks": checks, "eligible": all(checks.values())}


def exit_signal(initial_credit: float, current_pnl_per_contract: float, dte_remaining: int, short_delta: float) -> Dict[str, object]:
    target = initial_credit * 0.50
    stop = -initial_credit * 2.0
    if current_pnl_per_contract >= target:
        action, reason = "EXIT", "50% profit target reached"
    elif current_pnl_per_contract <= stop:
        action, reason = "EXIT", "2.0x initial-credit stop reached"
    elif dte_remaining <= 14:
        action, reason = "EXIT / ROLL", "Time stop and gamma de-risking at 14 DTE"
    elif abs(short_delta) >= 0.30:
        action, reason = "ROLL / CUT", "Short-strike delta threat threshold exceeded"
    else:
        action, reason = "HOLD", "No exit threshold reached"
    return {"action": action, "reason": reason, "profit_target": target, "stop_loss": stop}
