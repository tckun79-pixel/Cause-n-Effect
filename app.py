"""Bull Put Spread Lab — interactive XSP/SPX research dashboard."""
from __future__ import annotations

import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import BacktestConfig, run_backtest
from pricing import BullPutSpread, scenario_table
from strategy import MarketContext, TradeParameters, entry_filter, exit_signal

st.set_page_config(page_title="Bull Put Spread Lab", page_icon="📉", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#07111f; color:#e8eef7; }
[data-testid="stSidebar"] { background:#0b1728; border-right:1px solid #20324a; }
.block-container { max-width: 1500px; padding-top: 1.4rem; }
.hero { background:linear-gradient(135deg,#102542,#0b1525); border:1px solid #294462; border-radius:18px; padding:24px 28px; margin-bottom:20px; }
.hero h1 { margin:0; color:#f2f7ff; font-size:2.35rem; letter-spacing:-.04em; }
.hero p { color:#9fb4cc; margin:.45rem 0 0; font-size:1rem; }
.metric-card { background:#0d1c31; border:1px solid #203752; border-radius:14px; padding:14px 16px; min-height:104px; }
.metric-label { color:#91a9c5; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { color:#f3f7fb; font-size:1.55rem; font-weight:700; margin-top:8px; }
.badge-good { color:#49d69a; font-weight:700; } .badge-bad { color:#ff7f8e; font-weight:700; }
section[data-testid="stSidebar"] .stMarkdown h3 { color:#d9e7f7; }
div[data-testid="stMetric"] { background:#0d1c31; border:1px solid #203752; padding:12px; border-radius:12px; }
</style>
""", unsafe_allow_html=True)


def money(value: float) -> str:
    return f"${value:,.2f}"


def chart_layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(template="plotly_dark", height=height, paper_bgcolor="#0d1c31", plot_bgcolor="#0d1c31", margin=dict(l=20, r=20, t=45, b=20), legend=dict(orientation="h"))
    fig.update_xaxes(gridcolor="#203752")
    fig.update_yaxes(gridcolor="#203752", zerolinecolor="#5b708b")
    return fig


st.markdown('<div class="hero"><h1>Bull Put Spread Lab</h1><p>European-style XSP/SPX credit spread research, payoff analysis, risk controls, and transparent backtesting.</p></div>', unsafe_allow_html=True)
st.warning("Research and education only. This dashboard does not provide investment advice or live execution. Historical results and model outputs are not guarantees of future performance.")

with st.sidebar:
    st.markdown("### Position inputs")
    product = st.selectbox("Product", ["XSP — Mini-SPX", "SPX — S&P 500"], index=0)
    default_spot = 550.0 if product.startswith("XSP") else 5500.0
    step = 5.0 if product.startswith("XSP") else 50.0
    spot = st.number_input("Spot price", min_value=1.0, value=default_spot, step=step)
    dte = st.slider("Days to expiration", 7, 60, 35)
    iv = st.slider("Implied volatility", 8.0, 50.0, 18.0) / 100.0
    strike_step = 1.0 if product.startswith("XSP") else 5.0
    short_strike = st.number_input("Short put strike", min_value=1.0, value=spot * 0.93, step=strike_step)
    width = st.select_slider("Wing width", options=[5.0, 10.0] if product.startswith("XSP") else [50.0, 100.0], value=5.0 if product.startswith("XSP") else 50.0)
    long_strike = short_strike - width
    contracts = st.number_input("Contracts", min_value=1, value=1, step=1)
    rate = st.number_input("Risk-free rate", min_value=0.0, max_value=0.15, value=0.045, step=0.0025, format="%.3f")
    st.caption(f"Long put strike is derived as {long_strike:,.2f}. Multiplier: 100.")

spread = BullPutSpread(spot, short_strike, long_strike, dte, iv, rate, 100, contracts)
short_delta = spread.short_put["delta"]
credit_ratio = spread.credit / spread.width if spread.width else 0.0

cols = st.columns(6)
for col, label, value in zip(cols, ["Net credit", "Max profit", "Max loss", "Breakeven", "POP", "Short delta"], [money(spread.credit * 100 * contracts), money(spread.max_profit), money(spread.max_loss), f"{spread.breakeven:,.2f}", f"{spread.pop:.1%}", f"{short_delta:.3f}"]):
    col.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

pricing_tab, rules_tab, stress_tab, backtest_tab = st.tabs(["Pricing & payoff", "Rules & management", "Stress matrix", "Backtesting"])

with pricing_tab:
    x = np.linspace(max(spot * 0.75, long_strike * 0.65), spot * 1.20, 250)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=spread.expiry_pnl(x), name="Expiration P&L", line=dict(color="#49d69a", width=3)))
    fig.add_trace(go.Scatter(x=x, y=spread.mark_to_market_pnl(x, dte), name="T+0 theoretical P&L", line=dict(color="#66a9ff", width=3, dash="dash")))
    fig.add_vline(x=spread.breakeven, line_dash="dot", line_color="#ffcf66", annotation_text="Breakeven")
    fig.add_hline(y=0, line_color="#5b708b")
    st.plotly_chart(chart_layout(fig), use_container_width=True)
    greeks = pd.DataFrame({"Metric": ["Value", "Delta", "Gamma", "Theta / day", "Vega / 1 vol point"], "Short put": [spread.short_put[k] for k in ["value", "delta", "gamma", "theta", "vega"]], "Long put": [spread.long_put[k] for k in ["value", "delta", "gamma", "theta", "vega"]]})
    st.subheader("Leg pricing and Greeks")
    st.dataframe(greeks.style.format({"Short put": "{:.6f}", "Long put": "{:.6f}"}), use_container_width=True, hide_index=True)
    st.caption("Black-Scholes assumptions: European exercise, continuous risk-free rate, constant volatility, no dividends, and 365-day annualization. XSP/SPX contract specifications and market data must be verified before live use.")

with rules_tab:
    st.subheader("Entry filter")
    c1, c2, c3 = st.columns(3)
    with c1:
        sma200 = st.number_input("200-day SMA", value=spot * 0.97, step=step)
        ema20 = st.number_input("20-day EMA", value=spot * 1.005, step=step)
    with c2:
        ema50 = st.number_input("50-day EMA", value=spot * 0.995, step=step)
        ivr = st.slider("30-day IV Rank / Percentile", 0, 100, 35)
    with c3:
        macro_hours = st.number_input("Hours to next FOMC/CPI (blank = unknown)", min_value=0.0, value=48.0, step=1.0)
    context = MarketContext(spot, sma200, ema20, ema50, ivr, macro_hours)
    parameters = TradeParameters(dte, short_delta, width, spread.credit)
    result = entry_filter(context, parameters)
    st.markdown(f"**Signal:** <span class={'badge-good' if result['eligible'] else 'badge-bad'}>{'ELIGIBLE' if result['eligible'] else 'BLOCKED'}</span>", unsafe_allow_html=True)
    checks = pd.DataFrame([{"Rule": k, "Status": "PASS" if v else "FAIL"} for k, v in result["checks"].items()])
    st.dataframe(checks, use_container_width=True, hide_index=True)
    st.subheader("Exit protocol")
    current_pnl = st.number_input("Current P&L per contract", value=0.0, step=10.0)
    current_delta = st.number_input("Current short-strike delta", value=abs(short_delta), min_value=0.0, max_value=1.0, step=0.01)
    exit_result = exit_signal(spread.credit * 100, current_pnl, dte, current_delta)
    st.info(f"**{exit_result['action']}** — {exit_result['reason']}")
    st.dataframe(pd.DataFrame([{"Profit target": exit_result["profit_target"], "Stop loss": exit_result["stop_loss"], "Time stop": "14 DTE", "Threat delta": ">= 0.30"}]).style.format("${:,.2f}"), use_container_width=True, hide_index=True)

with stress_tab:
    st.subheader("Underlying shock matrix")
    rows = scenario_table(spread, [0.05, 0.025, 0.0, -0.025, -0.05, -0.075, -0.10])
    stress = pd.DataFrame(rows)
    st.dataframe(stress.style.format({"Underlying": "{:,.2f}", "Expiry P&L": "${:,.2f}", "T+0 P&L": "${:,.2f}"}), use_container_width=True, hide_index=True)
    fig = go.Figure(go.Bar(x=stress["Shock"], y=stress["Expiry P&L"], marker_color=np.where(stress["Expiry P&L"] >= 0, "#49d69a", "#ff7181")))
    st.plotly_chart(chart_layout(fig, 320), use_container_width=True)
    st.markdown("**Settlement comparison.** XSP and SPX are European-style, cash-settled index options: at expiration, the economic result is a cash debit or credit rather than delivery of shares. A physically settled ETF option can create assignment and overnight share-delivery exposure; this dashboard intentionally does not model that process.")

with backtest_tab:
    st.subheader("Historical backtest")
    st.write("Upload a CSV containing at least 60 observations and columns named Date/Datetime plus Close/Price. If only underlying prices are provided, the simulator uses an explicitly labeled premium proxy; it does not claim to reconstruct historical option-chain fills.")
    uploaded = st.file_uploader("Upload historical price CSV", type=["csv"])
    if uploaded is None:
        st.info("No file uploaded. A small deterministic demo dataset is available for UI testing only.")
        dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=420, freq="B")
        close = 550 * np.exp(np.cumsum(np.full(len(dates), 0.00012)))
        demo = pd.DataFrame({"Date": dates, "Close": close})
        use_frame = demo if st.checkbox("Run deterministic demo", value=False) else None
    else:
        use_frame = pd.read_csv(io.BytesIO(uploaded.getvalue()))
    if use_frame is not None and st.button("Run backtest", type="primary"):
        try:
            config = BacktestConfig(short_delta=0.13, width=width, dte=dte, credit_ratio=max(credit_ratio, 0.15), contracts=contracts)
            history, output = run_backtest(use_frame, config)
            metrics = output["metrics"]
            m = st.columns(7)
            metric_values = [("Trades", metrics["trades"]), ("Win rate", f"{metrics['win_rate']:.1%}"), ("Profit factor", f"{metrics['profit_factor']:.2f}"), ("Expected value", money(metrics["expected_value"])), ("Sharpe", f"{metrics['sharpe']:.2f}"), ("Sortino", f"{metrics['sortino']:.2f}"), ("Max DD", money(metrics["max_drawdown"]))]
            for col, (label, value) in zip(m, metric_values): col.metric(label, value)
            equity = go.Figure()
            equity.add_trace(go.Scatter(x=history["date"], y=history["equity"], name="Equity", line=dict(color="#49d69a", width=3)))
            equity.add_trace(go.Scatter(x=history["date"], y=history["drawdown"], name="Drawdown", line=dict(color="#ff7181"), yaxis="y2"))
            equity.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False), title="Equity curve and drawdown")
            st.plotly_chart(chart_layout(equity), use_container_width=True)
            st.dataframe(output["trades"], use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Backtest could not run: {exc}")

st.divider()
st.caption("Implementation note: this is a research dashboard. For production deployment, connect a licensed historical option-chain source, model bid/ask fills, commissions, dividends, holidays, margin, volatility surfaces, and corporate/data-quality controls before relying on results.")
