"""
Main panel: metric cards and scenario save/load panel.
No math, no Plotly figures — only st.* calls.
"""

import streamlit as st

from calculator.scenarios import (
    ComputedResults,
    InputBundle,
    delete_scenario,
    save_scenario,
)


def _fmt(value: float) -> str:
    """Format a COP monetary value for display (e.g. $2,345,678)."""
    return f"${value:,.0f}"


def render_metrics(results: ComputedResults, inputs: InputBundle) -> None:
    """Render two rows of metric cards from pre-computed results."""

    has_rental = inputs.monthly_rental > 0

    # ── Row 1 ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Monthly Payment",
            _fmt(results.payment),
            help="Fixed monthly payment (cuota fija).",
        )
    with c2:
        st.metric(
            "Total Paid",
            _fmt(results.total_paid),
            help="Total amount paid to the bank over the full term (principal + interest).",
        )
    with c3:
        st.metric(
            "Total Interest",
            _fmt(results.total_interest),
            help="Total interest paid — the cost of the loan.",
        )
    with c4:
        st.metric(
            "Loan Term",
            f"{results.n_months} mo ({results.n_months / 12:.1f} yr)",
            help="Number of monthly payments.",
        )

    # ── Row 2 ─────────────────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.metric(
            "Min. Payment (floor)",
            _fmt(results.floor_payment),
            help="The minimum payment that covers only interest. "
                 "Any payment at or below this means the balance never decreases.",
        )
    with c6:
        st.metric(
            "Danger Ceiling",
            _fmt(results.danger_ceil),
            help="The loan amount at which your monthly payment only covers perpetual interest. "
                 "If your loan exceeds this, the payment is insufficient.",
        )
    with c7:
        if has_rental:
            st.metric(
                "Net Cost (after rental)",
                _fmt(results.net_total_cost),
                delta=_fmt(results.net_total_cost - results.total_paid),
                delta_color="normal",
                help="Total paid minus total rental income received over the loan term.",
            )
        else:
            st.metric(
                "Net Cost",
                _fmt(results.total_paid),
                help="Add a monthly rental income to see the net cost after rental offset.",
            )
    with c8:
        if has_rental:
            st.metric(
                "Net Interest (after rental)",
                _fmt(results.net_interest),
                delta=_fmt(results.net_interest - results.total_interest),
                delta_color="normal",
                help="Total interest minus total rental income. "
                     "Negative means rental more than covers the interest cost.",
            )
        else:
            st.metric(
                "Loan Amount",
                _fmt(results.loan),
                help="Principal borrowed (apartment price minus down payment).",
            )

    # ── Warnings ──────────────────────────────────────────────────────────────
    pct_of_floor = results.payment / results.floor_payment if results.floor_payment > 0 else 999
    if pct_of_floor < 1.05:
        st.warning(
            f"⚠️ Your payment ({_fmt(results.payment)}) is only "
            f"{(pct_of_floor - 1) * 100:.1f}% above the interest-only floor "
            f"({_fmt(results.floor_payment)}). Very little principal is being paid each month.",
            icon="⚠️",
        )

    if results.loan > results.danger_ceil * 0.95:
        st.error(
            f"🚨 The loan amount ({_fmt(results.loan)}) is close to or exceeds the danger "
            f"ceiling ({_fmt(results.danger_ceil)}) for this payment. "
            "The loan may never be fully repaid at this payment level.",
        )


def render_scenario_panel(inputs: InputBundle, results: ComputedResults) -> None:
    """Expander for saving the current scenario. Scenario list lives in the sidebar."""
    with st.expander("💾 Save This Scenario", expanded=False):
        col_name, col_btn = st.columns([3, 1])
        with col_name:
            name = st.text_input(
                "Scenario name",
                value=f"{inputs.annual_rate_ea * 100:.1f}% / {results.n_months}mo",
                label_visibility="collapsed",
                placeholder="e.g. Base case",
            )
        with col_btn:
            if st.button("Save", width=True):
                save_scenario(name or "Unnamed", inputs, results)
                st.success(f'Saved: "{name}"')


def render_scenario_list_sidebar() -> None:
    """Render the saved scenarios list in the sidebar with Load / Delete buttons."""
    scenarios = st.session_state.get("scenarios", [])
    if not scenarios:
        return

    with st.sidebar:
        st.divider()
        st.subheader("Saved Scenarios")
        for scenario in list(scenarios):  # iterate a copy so deletes don't shift indices
            col_name, col_load, col_del = st.columns([4, 2, 1])
            with col_name:
                st.caption(
                    f"**{scenario.name}**  \n"
                    f"{scenario.results.n_months}mo · "
                    f"${scenario.results.payment:,.0f}/mo · "
                    f"${scenario.results.total_interest:,.0f} int."
                )
            with col_load:
                if st.button("Load", key=f"load_{scenario.id}", width=True):
                    # Set a flag; the actual state mutation happens at the top of
                    # app.py before any widget keys are bound (avoids the
                    # "cannot modify after instantiation" error).
                    st.session_state["_pending_load_id"] = scenario.id
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"del_{scenario.id}", width=True):
                    delete_scenario(scenario.id)
                    st.rerun()
