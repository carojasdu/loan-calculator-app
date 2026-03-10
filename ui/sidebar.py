"""
Sidebar widgets. Returns a populated InputBundle.
All st.sidebar calls live here — no math, no Plotly.
"""

import streamlit as st

from calculator.scenarios import InputBundle


# ── Down payment sync callbacks ───────────────────────────────────────────────

def _sync_abs_to_pct() -> None:
    price = st.session_state.get("input_apartment_price", 0)
    abs_val = st.session_state.get("input_down_payment_abs", 0)
    if price > 0:
        new_pct = round(abs_val / price * 100, 2)
        if abs(new_pct - st.session_state.get("input_down_payment_pct", 0)) > 0.001:
            st.session_state["input_down_payment_pct"] = new_pct


def _sync_pct_to_abs() -> None:
    price = st.session_state.get("input_apartment_price", 0)
    pct = st.session_state.get("input_down_payment_pct", 0)
    new_abs = round(price * pct / 100)
    if abs(new_abs - st.session_state.get("input_down_payment_abs", 0)) > 1:
        st.session_state["input_down_payment_abs"] = float(new_abs)


def _sync_price_change() -> None:
    # When price changes, keep % fixed and update abs
    price = st.session_state.get("input_apartment_price", 0)
    pct = st.session_state.get("input_down_payment_pct", 0)
    if price > 0:
        st.session_state["input_down_payment_abs"] = float(round(price * pct / 100))


# ── Main render function ──────────────────────────────────────────────────────

def render_sidebar() -> InputBundle:
    """Render all sidebar inputs and return an InputBundle."""
    with st.sidebar:
        st.title("🏠 Loan Calculator")

        # ── Property ─────────────────────────────────────────────────────────
        st.subheader("Property")

        st.number_input(
            "Apartment price",
            min_value=1_000_000.0,
            max_value=10_000_000_000.0,
            step=1_000_000.0,
            format="%.0f",
            key="input_apartment_price",
            on_change=_sync_price_change,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Down payment (COP)",
                min_value=0.0,
                max_value=float(st.session_state.get("input_apartment_price", 10_000_000_000)),
                step=1_000_000.0,
                format="%.0f",
                key="input_down_payment_abs",
                on_change=_sync_abs_to_pct,
            )
        with col2:
            st.number_input(
                "Down payment (%)",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                format="%.1f",
                key="input_down_payment_pct",
                on_change=_sync_pct_to_abs,
            )

        loan = st.session_state["input_apartment_price"] - st.session_state["input_down_payment_abs"]
        st.caption(f"Loan amount: **{loan:,.0f}**")

        st.divider()

        # ── Interest rate ─────────────────────────────────────────────────────
        st.subheader("Interest Rate")

        st.number_input(
            "Annual rate — E.A. (%)",
            min_value=0.1,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            key="input_annual_rate_ea",
        )

        st.divider()

        # ── Solve mode ────────────────────────────────────────────────────────
        st.subheader("Solve For")

        st.radio(
            "I know the…",
            options=["months", "payment"],
            format_func=lambda x: "Number of months" if x == "months" else "Monthly payment",
            key="input_solve_mode",
            horizontal=False,
        )

        if st.session_state["input_solve_mode"] == "months":
            st.number_input(
                "Number of months",
                min_value=1,
                max_value=600,
                step=1,
                key="input_known_months",
            )
        else:
            st.number_input(
                "Monthly payment (COP)",
                min_value=1_000.0,
                max_value=1_000_000_000.0,
                step=10_000.0,
                format="%.0f",
                key="input_known_payment",
            )

        st.divider()

        # ── Optional: rental income ───────────────────────────────────────────
        st.subheader("Rental Income (optional)")

        st.number_input(
            "Monthly rental income (COP)",
            min_value=0.0,
            max_value=100_000_000.0,
            step=100_000.0,
            format="%.0f",
            key="input_monthly_rental",
            help="If you plan to rent out the property, this offsets the effective cost.",
        )

    # ── Build and return InputBundle ──────────────────────────────────────────
    return InputBundle(
        apartment_price=st.session_state["input_apartment_price"],
        down_payment_abs=st.session_state["input_down_payment_abs"],
        annual_rate_ea=st.session_state["input_annual_rate_ea"] / 100.0,  # percent → decimal
        solve_mode=st.session_state["input_solve_mode"],
        known_payment=st.session_state.get("input_known_payment"),
        known_months=st.session_state.get("input_known_months"),
        monthly_rental=st.session_state["input_monthly_rental"],
    )
