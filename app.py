"""
Loan / Mortgage Calculator — Streamlit app entry point.

Orchestrates: sidebar inputs → math → metrics → chart → scenario panel.
"""

import math

import streamlit as st

from calculator import amortization, math_core
from calculator.scenarios import (
    ComputedResults,
    init_session_state,
    load_scenario_into_state,
)
from ui import metrics_panel, sidebar
from ui.charts import build_amortization_chart

st.set_page_config(
    page_title="Loan Calculator",
    page_icon="🏠",
    layout="wide",
)

init_session_state()

# ── Apply pending scenario load BEFORE any widget is instantiated ─────────────
# The Load button only sets a flag; the actual state mutation happens here so
# that widget keys are not yet bound when we write to session_state.
if "_pending_load_id" in st.session_state:
    load_scenario_into_state(st.session_state.pop("_pending_load_id"))

# ── Sidebar: collect inputs ───────────────────────────────────────────────────
inputs = sidebar.render_sidebar()

# ── Render saved scenarios list in sidebar ────────────────────────────────────
metrics_panel.render_scenario_list_sidebar()

# ── Validate basic inputs ─────────────────────────────────────────────────────
st.title("🏠 Mortgage / Loan Calculator")

loan = inputs.apartment_price - inputs.down_payment_abs

if inputs.down_payment_abs >= inputs.apartment_price:
    st.error("Down payment must be less than the apartment price.")
    st.stop()

if loan <= 0:
    st.error("Loan amount must be positive. Adjust the down payment.")
    st.stop()

# ── Core math ─────────────────────────────────────────────────────────────────
monthly_rate = math_core.monthly_rate_from_ea(inputs.annual_rate_ea)
floor = math_core.min_payment(loan, monthly_rate)

if inputs.solve_mode == "months":
    n_months = inputs.known_months
    try:
        payment = math_core.compute_payment(loan, monthly_rate, n_months)
    except ValueError as e:
        st.error(str(e))
        st.stop()
else:  # solve_mode == "payment"
    payment = inputs.known_payment
    if payment <= floor:
        st.error(
            f"Monthly payment ({payment:,.0f}) must exceed the interest-only floor "
            f"({floor:,.0f}). Increase the payment or reduce the loan."
        )
        st.stop()
    try:
        n_months_float = math_core.compute_months(loan, monthly_rate, payment)
        n_months = math.ceil(n_months_float)
    except ValueError as e:
        st.error(str(e))
        st.stop()

total_paid = payment * n_months
total_int = math_core.total_interest(payment, n_months, loan)
d_ceil = math_core.danger_ceiling(payment, monthly_rate)
net_cost = math_core.net_cost_after_rental(total_paid, inputs.monthly_rental, n_months)
net_int = math_core.net_interest_after_rental(total_int, inputs.monthly_rental, n_months)

results = ComputedResults(
    loan=loan,
    monthly_rate=monthly_rate,
    payment=payment,
    n_months=n_months,
    total_paid=total_paid,
    total_interest=total_int,
    floor_payment=floor,
    danger_ceil=d_ceil,
    net_total_cost=net_cost,
    net_interest=net_int,
)

# ── Metrics panel ─────────────────────────────────────────────────────────────
metrics_panel.render_metrics(results, inputs)

st.divider()

# ── Amortization chart ────────────────────────────────────────────────────────
schedule = amortization.build_schedule(
    loan=loan,
    monthly_rate=monthly_rate,
    payment=payment,
    n_months=n_months,
    monthly_rental=inputs.monthly_rental,
)

fig = build_amortization_chart(
    schedule=schedule,
    show_rental_line=inputs.monthly_rental > 0,
    payoff_month=n_months,
)
st.plotly_chart(fig, width=True)

st.divider()

# ── Scenario save panel ───────────────────────────────────────────────────────
metrics_panel.render_scenario_panel(inputs, results)
