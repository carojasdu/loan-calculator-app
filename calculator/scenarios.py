"""
Dataclasses representing the app's core data contracts,
plus session_state initialization and scenario CRUD helpers.
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st


@dataclass
class InputBundle:
    apartment_price: float
    down_payment_abs: float
    annual_rate_ea: float       # decimal, e.g. 0.127
    solve_mode: str             # "payment" | "months"
    known_payment: Optional[float]
    known_months: Optional[int]
    monthly_rental: float


@dataclass
class ComputedResults:
    loan: float
    monthly_rate: float
    payment: float
    n_months: int
    total_paid: float
    total_interest: float
    floor_payment: float        # min payment (interest-only)
    danger_ceil: float          # loan amount where payment = perpetual interest
    net_total_cost: float       # total_paid minus rental income
    net_interest: float         # total_interest minus rental income


@dataclass
class Scenario:
    name: str
    inputs: InputBundle
    results: ComputedResults
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


# ── Session state keys ────────────────────────────────────────────────────────

_DEFAULTS: dict = {
    "input_apartment_price": 300_000_000.0,
    "input_down_payment_abs": 110_000_000.0,
    "input_down_payment_pct": round(110 / 300 * 100, 2),
    "input_annual_rate_ea": 12.7,       # stored as percent (e.g. 12.7), converted on use
    "input_solve_mode": "months",
    "input_known_payment": 2_500_000.0,
    "input_known_months": 180,
    "input_monthly_rental": 0.0,
    "scenarios": [],
}


def init_session_state() -> None:
    """Initialize all session_state keys with defaults if not already set.

    Call once at the top of app.py. Safe to call multiple times (idempotent).
    """
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ── Scenario CRUD ─────────────────────────────────────────────────────────────

def save_scenario(name: str, inputs: InputBundle, results: ComputedResults) -> None:
    """Append a new scenario to the session's saved list."""
    st.session_state["scenarios"].append(Scenario(name=name, inputs=inputs, results=results))


def delete_scenario(scenario_id: str) -> None:
    """Remove scenario by id."""
    st.session_state["scenarios"] = [
        s for s in st.session_state["scenarios"] if s.id != scenario_id
    ]


def load_scenario_into_state(scenario_id: str) -> None:
    """Write a saved scenario's inputs back into session_state widget keys.

    After calling this, trigger st.rerun() so the sidebar re-renders with
    the loaded values.
    """
    scenario = next(
        (s for s in st.session_state["scenarios"] if s.id == scenario_id), None
    )
    if scenario is None:
        return

    b = scenario.inputs
    st.session_state["input_apartment_price"] = b.apartment_price
    st.session_state["input_down_payment_abs"] = b.down_payment_abs
    st.session_state["input_down_payment_pct"] = (
        round(b.down_payment_abs / b.apartment_price * 100, 2)
        if b.apartment_price > 0
        else 0.0
    )
    st.session_state["input_annual_rate_ea"] = b.annual_rate_ea * 100  # back to percent
    st.session_state["input_solve_mode"] = b.solve_mode
    st.session_state["input_known_payment"] = b.known_payment or _DEFAULTS["input_known_payment"]
    st.session_state["input_known_months"] = b.known_months or _DEFAULTS["input_known_months"]
    st.session_state["input_monthly_rental"] = b.monthly_rental
