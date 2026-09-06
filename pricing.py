"""Pricing and payoff calculations for European-style XSP/SPX bull put spreads."""
from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt
from typing import Dict

import numpy as np


def _norm_cdf(x: np.ndarray | float) -> np.ndarray | float:
    arr = np.asarray(x, dtype=float)
    out = 0.5 * (1.0 + np.vectorize(erf)(arr / sqrt(2.0)))
    return float(out) if np.ndim(x) == 0 else out


def _norm_pdf(x: np.ndarray | float) -> np.ndarray | float:
    arr = np.asarray(x, dtype=float)
    out = np.exp(-0.5 * arr * arr) / sqrt(2.0 * pi)
    return float(out) if np.ndim(x) == 0 else out


def _safe_time(days: float) -> float:
    return max(float(days), 1e-6) / 365.0


def european_put_greeks(spot: float, strike: float, dte: float, iv: float, rate: float = 0.045) -> Dict[str, float]:
    """Return Black-Scholes European put value, delta, gamma, theta and vega."""
    spot, strike, iv = max(float(spot), 1e-8), max(float(strike), 1e-8), max(float(iv), 1e-8)
    t = _safe_time(dte)
    sigma_t = iv * sqrt(t)
    d1 = (log(spot / strike) + (rate + 0.5 * iv * iv) * t) / sigma_t
    d2 = d1 - sigma_t
    disc = exp(-rate * t)
    value = strike * disc * _norm_cdf(-d2) - spot * _norm_cdf(-d1)
    delta = _norm_cdf(d1) - 1.0
    gamma = _norm_pdf(d1) / (spot * sigma_t)
    theta = -(spot * _norm_pdf(d1) * iv / (2.0 * sqrt(t))) + rate * strike * disc * _norm_cdf(-d2)
    vega = spot * _norm_pdf(d1) * sqrt(t) / 100.0
    return {"value": float(value), "delta": float(delta), "gamma": float(gamma), "theta": float(theta / 365.0), "vega": float(vega)}


@dataclass(frozen=True)
class BullPutSpread:
    spot: float
    short_strike: float
    long_strike: float
    dte: float
    iv: float
    rate: float = 0.045
    multiplier: int = 100
    contracts: int = 1

    @property
    def width(self) -> float:
        return max(self.short_strike - self.long_strike, 0.0)

    @property
    def short_put(self) -> Dict[str, float]:
        return european_put_greeks(self.spot, self.short_strike, self.dte, self.iv, self.rate)

    @property
    def long_put(self) -> Dict[str, float]:
        return european_put_greeks(self.spot, self.long_strike, self.dte, self.iv, self.rate)

    @property
    def credit(self) -> float:
        return max(self.short_put["value"] - self.long_put["value"], 0.0)

    @property
    def max_profit(self) -> float:
        return self.credit * self.multiplier * self.contracts

    @property
    def max_loss(self) -> float:
        return max(self.width - self.credit, 0.0) * self.multiplier * self.contracts

    @property
    def breakeven(self) -> float:
        return self.short_strike - self.credit

    @property
    def pop(self) -> float:
        # Approximation under the lognormal terminal distribution: expiry spot > breakeven.
        sigma_t = max(self.iv, 1e-8) * sqrt(_safe_time(self.dte))
        d2 = (log(self.spot / self.breakeven) + (self.rate - 0.5 * self.iv * self.iv) * _safe_time(self.dte)) / sigma_t
        return float(_norm_cdf(d2))

    def expiry_pnl(self, underlying: np.ndarray) -> np.ndarray:
        intrinsic_short = np.maximum(self.short_strike - underlying, 0.0)
        intrinsic_long = np.maximum(self.long_strike - underlying, 0.0)
        return (self.credit - intrinsic_short + intrinsic_long) * self.multiplier * self.contracts

    def mark_to_market_pnl(self, underlying: np.ndarray, dte_remaining: float) -> np.ndarray:
        short_values = np.array([european_put_greeks(s, self.short_strike, dte_remaining, self.iv, self.rate)["value"] for s in underlying])
        long_values = np.array([european_put_greeks(s, self.long_strike, dte_remaining, self.iv, self.rate)["value"] for s in underlying])
        current_value = short_values - long_values
        return (self.credit - current_value) * self.multiplier * self.contracts


def scenario_table(spread: BullPutSpread, shocks: list[float]) -> list[dict]:
    rows = []
    for shock in shocks:
        stressed_spot = spread.spot * (1.0 + shock)
        expiry = float(spread.expiry_pnl(np.array([stressed_spot]))[0])
        t0 = float(spread.mark_to_market_pnl(np.array([stressed_spot]), spread.dte)[0])
        rows.append({"Shock": f"{shock:+.1%}", "Underlying": stressed_spot, "Expiry P&L": expiry, "T+0 P&L": t0, "Cash-settled risk": "Cash debit only"})
    return rows
