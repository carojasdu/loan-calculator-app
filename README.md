# Mortgage / Loan Calculator

An interactive web app for exploring mortgage scenarios using French amortization (fixed monthly payment). Built with Python, Streamlit, and Plotly.

## Features

- **Two solve modes:** enter the number of months → get the monthly payment, or enter the monthly payment → get the number of months
- **Live metrics:** monthly payment, total paid, total interest, interest-only floor, danger ceiling, and net cost after rental income
- **Interactive chart:** remaining principal, cumulative interest, and cumulative principal over the full loan term — with hover tooltips and a payoff marker
- **Rental income offset:** enter monthly rental income to see the effective net cost and net interest after offsetting
- **Scenario saving:** save named scenarios for the session and reload any of them to compare alternatives

## Math

French amortization (cuota fija): the monthly payment is constant, but the split between interest and principal changes each month.

```
monthly_rate  = (1 + annual_rate_EA)^(1/12) − 1
payment       = loan × r / (1 − (1+r)^−n)        # given loan, rate, months
months        = −ln(1 − r·loan/payment) / ln(1+r)  # given loan, rate, payment
floor         = loan × r                            # payment that covers only interest
danger_ceiling = payment / r                        # loan where payment = perpetual interest
total_interest = payment × n − loan
```

Rates are entered as annual effective rates (E.A. / tasa efectiva anual), which is standard in Colombia.

## Running locally

```bash
uv sync
uv run streamlit run app.py
```

Or with pip:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```
├── app.py                    # Streamlit entry point
├── calculator/
│   ├── math_core.py          # Pure math — no UI imports
│   ├── amortization.py       # Amortization schedule (returns DataFrame)
│   └── scenarios.py          # Dataclasses + session_state helpers
├── ui/
│   ├── sidebar.py            # Sidebar inputs → InputBundle
│   ├── metrics_panel.py      # Metric cards + scenario save/load
│   └── charts.py             # Plotly figure builder
└── tests/
    ├── test_math_core.py
    └── test_amortization.py
```

## Running tests

```bash
uv run pytest tests/ -v
```
