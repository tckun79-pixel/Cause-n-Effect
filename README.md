# Bull Put Spread Lab

A Streamlit research dashboard for European-style, cash-settled XSP/SPX bull put spreads. It includes a vectorized Black-Scholes pricing view, expiration and T+0 payoff curves, entry filters, exit rules, shock scenarios, and a transparent CSV-driven backtest.

## Run locally

```bash
cd Cause-n-Effect
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. The app is intentionally self-contained and does not require API keys for the pricing and demonstration workflows.

## Backtest CSV format

Upload a CSV with at least 60 valid observations and a date column named `Date`, `Datetime`, or `Timestamp`, plus a price column named `Close`, `Adj Close`, or `Price`. The backtest uses the underlying price series to apply the trend filter. If historical option chains are not supplied, the app uses a clearly labeled premium proxy rather than pretending to reconstruct historical option fills.

## Model assumptions and limitations

The pricing engine assumes European exercise, continuous risk-free rate, constant volatility, no dividends, and a 365-day year. POP is a lognormal terminal-probability approximation. The stress matrix compares expiry and T+0 theoretical P&L under underlying shocks. The backtest is a research scaffold: production use requires licensed historical option chains, actual bid/ask fills, commissions, slippage, margin, dividends, exchange calendars, volatility surfaces, corporate-action handling, and point-in-time macro event data.

The software does not connect to a broker and does not place trades. Validate contract specifications, settlement mechanics, and risk controls with authoritative exchange and broker documentation before any live use.
